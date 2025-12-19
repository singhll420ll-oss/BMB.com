"""
Customer router for customer-specific endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
import structlog

from database import get_db
from models.user import User, UserRole
from models.order import Order, OrderStatus
from models.service import Service
from models.menu_item import MenuItem
from schemas.order import OrderCreate, OrderItemCreate
from crud.user import CRUDUser
from crud.service import CRUDService
from crud.menu_item import CRUDMenuItem
from crud.order import CRUDOrder
from core.security import verify_token
from core.exceptions import AuthenticationError, NotFoundError

router = APIRouter()
templates = Jinja2Templates(directory="templates")
logger = structlog.get_logger(__name__)

def get_current_customer(request: Request, db: AsyncSession = Depends(get_db)):
    """Get current customer from token"""
    token = request.cookies.get("access_token")
    if not token:
        raise AuthenticationError("Not authenticated")
    
    payload = verify_token(token)
    if payload.get("role") != "customer":
        raise AuthenticationError("Access denied")
    
    user = CRUDUser.get_by_id(db, payload.get("user_id"))
    if not user or user.role != UserRole.CUSTOMER:
        raise AuthenticationError("Invalid user")
    
    return user

@router.get("/dashboard", response_class=HTMLResponse)
async def customer_dashboard(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Customer dashboard"""
    try:
        customer = await get_current_customer(request, db)
        
        # Get recent orders
        orders = await CRUDOrder.get_customer_orders(db, customer.id, limit=5)
        
        return templates.TemplateResponse("customer/dashboard.html", {
            "request": request,
            "customer": customer,
            "orders": orders
        })
    except AuthenticationError:
        return RedirectResponse(url="/auth/login?role=customer", status_code=303)

@router.get("/services", response_class=HTMLResponse)
async def list_services(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """List all services"""
    try:
        customer = await get_current_customer(request, db)
        services = await CRUDService.get_all(db)
        
        return templates.TemplateResponse("customer/services.html", {
            "request": request,
            "customer": customer,
            "services": services
        })
    except AuthenticationError:
        return RedirectResponse(url="/auth/login?role=customer", status_code=303)

@router.get("/service/{service_id}", response_class=HTMLResponse)
async def service_menu(
    request: Request,
    service_id: int,
    db: AsyncSession = Depends(get_db)
):
    """View menu for a specific service"""
    try:
        customer = await get_current_customer(request, db)
        service = await CRUDService.get_by_id(db, service_id, with_menu=True)
        
        if not service:
            raise NotFoundError("Service")
        
        return templates.TemplateResponse("customer/service_menu.html", {
            "request": request,
            "customer": customer,
            "service": service,
            "menu_items": service.menu_items
        })
    except AuthenticationError:
        return RedirectResponse(url="/auth/login?role=customer", status_code=303)
    except NotFoundError as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": str(e)
        }, status_code=404)

@router.post("/cart/add")
async def add_to_cart(
    request: Request,
    menu_item_id: int = Form(...),
    quantity: int = Form(1),
    db: AsyncSession = Depends(get_db)
):
    """Add item to cart"""
    try:
        customer = await get_current_customer(request, db)
        
        # Get menu item
        menu_item = await CRUDMenuItem.get_by_id(db, menu_item_id)
        if not menu_item or not menu_item.is_available:
            raise NotFoundError("Menu item not available")
        
        # Get or create cart from session
        cart = request.session.get("cart", {})
        cart_key = str(menu_item_id)
        
        if cart_key in cart:
            cart[cart_key]["quantity"] += quantity
        else:
            cart[cart_key] = {
                "menu_item_id": menu_item_id,
                "name": menu_item.name,
                "price": menu_item.price,
                "quantity": quantity,
                "service_id": menu_item.service_id
            }
        
        request.session["cart"] = cart
        
        # HTMX response
        return HTMLResponse(f"""
            <div class="alert alert-success alert-dismissible fade show" role="alert">
                Added {menu_item.name} to cart
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
            <span class="badge bg-danger rounded-pill" id="cart-count">{len(cart)}</span>
        """)
        
    except Exception as e:
        return HTMLResponse(f"""
            <div class="alert alert-danger alert-dismissible fade show" role="alert">
                {str(e)}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        """)

@router.get("/cart", response_class=HTMLResponse)
async def view_cart(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """View shopping cart"""
    try:
        customer = await get_current_customer(request, db)
        cart = request.session.get("cart", {})
        
        # Calculate totals
        total = 0
        cart_items = []
        
        for item_data in cart.values():
            subtotal = item_data["price"] * item_data["quantity"]
            total += subtotal
            cart_items.append({
                **item_data,
                "subtotal": subtotal
            })
        
        return templates.TemplateResponse("customer/cart.html", {
            "request": request,
            "customer": customer,
            "cart_items": cart_items,
            "total": total
        })
    except AuthenticationError:
        return RedirectResponse(url="/auth/login?role=customer", status_code=303)

@router.post("/cart/update")
async def update_cart_item(
    request: Request,
    menu_item_id: str = Form(...),
    quantity: int = Form(...)
):
    """Update cart item quantity"""
    try:
        cart = request.session.get("cart", {})
        
        if quantity <= 0:
            if menu_item_id in cart:
                del cart[menu_item_id]
        else:
            if menu_item_id in cart:
                cart[menu_item_id]["quantity"] = quantity
        
        request.session["cart"] = cart
        
        # Recalculate totals for HTMX response
        total = 0
        for item_data in cart.values():
            total += item_data["price"] * item_data["quantity"]
        
        return HTMLResponse(f"""
            <span id="cart-total">₹{total:.2f}</span>
            <span class="badge bg-danger rounded-pill ms-2" id="cart-count">{len(cart)}</span>
        """)
        
    except Exception as e:
        return HTMLResponse(f"""
            <div class="alert alert-danger">{str(e)}</div>
        """)

@router.post("/cart/remove")
async def remove_cart_item(
    request: Request,
    menu_item_id: str = Form(...)
):
    """Remove item from cart"""
    try:
        cart = request.session.get("cart", {})
        
        if menu_item_id in cart:
            item_name = cart[menu_item_id]["name"]
            del cart[menu_item_id]
            request.session["cart"] = cart
            
            # Recalculate total
            total = 0
            for item_data in cart.values():
                total += item_data["price"] * item_data["quantity"]
            
            return HTMLResponse(f"""
                <div class="alert alert-info">
                    Removed {item_name} from cart
                </div>
                <span id="cart-total">₹{total:.2f}</span>
                <span class="badge bg-danger rounded-pill ms-2" id="cart-count">{len(cart)}</span>
            """)
        
        return HTMLResponse("")
        
    except Exception as e:
        return HTMLResponse(f"""
            <div class="alert alert-danger">{str(e)}</div>
        """)

@router.post("/order/place")
async def place_order(
    request: Request,
    address: str = Form(...),
    special_instructions: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """Place order from cart"""
    try:
        customer = await get_current_customer(request, db)
        cart = request.session.get("cart", {})
        
        if not cart:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cart is empty"
            )
        
        # Group items by service
        service_items = {}
        for item_data in cart.values():
            service_id = item_data["service_id"]
            if service_id not in service_items:
                service_items[service_id] = []
            
            service_items[service_id].append(item_data)
        
        # Create orders for each service
        orders_created = []
        for service_id, items in service_items.items():
            # Create order items
            order_items = []
            for item_data in items:
                order_items.append(OrderItemCreate(
                    menu_item_id=item_data["menu_item_id"],
                    quantity=item_data["quantity"]
                ))
            
            # Create order
            order_data = OrderCreate(
                service_id=service_id,
                address=address,
                special_instructions=special_instructions,
                items=order_items
            )
            
            order = await CRUDOrder.create(db, order_data, customer.id)
            orders_created.append(order)
        
        # Clear cart
        request.session["cart"] = {}
        
        # Redirect to orders page
        return RedirectResponse(url="/customer/orders", status_code=303)
        
    except AuthenticationError:
        return RedirectResponse(url="/auth/login?role=customer", status_code=303)
    except Exception as e:
        logger.error(f"Order placement error: {str(e)}")
        return templates.TemplateResponse("customer/cart.html", {
            "request": request,
            "error": str(e)
        })

@router.get("/orders", response_class=HTMLResponse)
async def my_orders(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """View customer's orders"""
    try:
        customer = await get_current_customer(request, db)
        orders = await CRUDOrder.get_customer_orders(db, customer.id)
        
        return templates.TemplateResponse("customer/my_orders.html", {
            "request": request,
            "customer": customer,
            "orders": orders
        })
    except AuthenticationError:
        return RedirectResponse(url="/auth/login?role=customer", status_code=303)

@router.get("/order/{order_id}")
async def order_details(
    request: Request,
    order_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get order details"""
    try:
        customer = await get_current_customer(request, db)
        order = await CRUDOrder.get_by_id(db, order_id, with_items=True)
        
        if not order or order.customer_id != customer.id:
            raise NotFoundError("Order")
        
        # HTMX response for order details modal
        items_html = ""
        for item in order.order_items:
            items_html += f"""
            <tr>
                <td>{item.item_name}</td>
                <td>{item.quantity}</td>
                <td>₹{item.unit_price:.2f}</td>
                <td>₹{item.subtotal:.2f}</td>
            </tr>
            """
        
        return HTMLResponse(f"""
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Order #{order.id}</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <div class="row mb-3">
                        <div class="col-6">
                            <strong>Status:</strong>
                            <span class="badge bg-{'info' if order.status == 'pending' else 'warning' if order.status == 'preparing' else 'success' if order.status == 'delivered' else 'danger'}">
                                {order.status}
                            </span>
                        </div>
                        <div class="col-6">
                            <strong>Total:</strong> ₹{order.total_amount:.2f}
                        </div>
                    </div>
                    
                    <div class="mb-3">
                        <strong>Address:</strong>
                        <p class="mb-1">{order.address}</p>
                        {f'<p><strong>Instructions:</strong> {order.special_instructions}</p>' if order.special_instructions else ''}
                    </div>
                    
                    <table class="table table-sm">
                        <thead>
                            <tr>
                                <th>Item</th>
                                <th>Qty</th>
                                <th>Price</th>
                                <th>Subtotal</th>
                            </tr>
                        </thead>
                        <tbody>
                            {items_html}
                        </tbody>
                        <tfoot>
                            <tr>
                                <td colspan="3" class="text-end"><strong>Total:</strong></td>
                                <td><strong>₹{order.total_amount:.2f}</strong></td>
                            </tr>
                        </tfoot>
                    </table>
                    
                    <div class="text-muted small">
                        Ordered: {order.created_at.strftime('%d %b %Y, %I:%M %p')}
                        {f'<br>Delivered: {order.delivered_at.strftime("%d %b %Y, %I:%M %p")}' if order.delivered_at else ''}
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                </div>
            </div>
        """)
        
    except Exception as e:
        return HTMLResponse(f"""
            <div class="alert alert-danger">{str(e)}</div>
        """)

@router.get("/profile", response_class=HTMLResponse)
async def customer_profile(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Customer profile page"""
    try:
        customer = await get_current_customer(request, db)
        
        # Get session statistics
        sessions = await CRUDUser.get_user_sessions(db, customer.id)
        
        total_minutes = 0
        for session in sessions:
            if session.duration_minutes:
                total_minutes += session.duration_minutes
        
        return templates.TemplateResponse("customer/profile.html", {
            "request": request,
            "customer": customer,
            "sessions": len(sessions),
            "total_minutes": round(total_minutes, 2)
        })
    except AuthenticationError:
        return RedirectResponse(url="/auth/login?role=customer", status_code=303)
