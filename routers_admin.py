"""
Admin router for admin management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
import os
import uuid
import structlog

from database import get_db
from models.user import User, UserRole
from models.service import Service
from models.menu_item import MenuItem
from models.order import Order, OrderStatus
from models.team_member_plan import TeamMemberPlan
from schemas.user import UserCreate, TeamMemberCreate, AdminCreate, UserUpdate
from schemas.service import ServiceCreate, ServiceUpdate
from schemas.menu_item import MenuItemCreate, MenuItemUpdate
from schemas.team_member_plan import TeamMemberPlanCreate
from crud.user import CRUDUser
from crud.service import CRUDService
from crud.menu_item import CRUDMenuItem
from crud.order import CRUDOrder
from crud.team_member_plan import CRUDTeamMemberPlan
from core.security import verify_token, get_password_hash
from core.config import settings
from core.exceptions import AuthenticationError, NotFoundError, ValidationError

router = APIRouter()
templates = Jinja2Templates(directory="templates")
logger = structlog.get_logger(__name__)

def get_current_admin(request: Request, db: AsyncSession = Depends(get_db)):
    """Get current admin from token"""
    token = request.cookies.get("access_token")
    if not token:
        raise AuthenticationError("Not authenticated")
    
    payload = verify_token(token)
    if payload.get("role") != "admin":
        raise AuthenticationError("Access denied")
    
    user = CRUDUser.get_by_id(db, payload.get("user_id"))
    if not user or user.role != UserRole.ADMIN:
        raise AuthenticationError("Invalid admin")
    
    return user

async def save_upload_file(upload_file: UploadFile) -> str:
    """Save uploaded file and return file path"""
    # Generate unique filename
    file_ext = os.path.splitext(upload_file.filename)[1]
    filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, filename)
    
    # Save file
    with open(file_path, "wb") as buffer:
        content = await upload_file.read()
        buffer.write(content)
    
    return f"/static/uploads/{filename}"

@router.get("/dashboard", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Admin dashboard"""
    try:
        admin = await get_current_admin(request, db)
        
        # Get statistics
        order_stats = await CRUDOrder.get_order_stats(db)
        
        # Get recent orders
        orders = await CRUDOrder.get_all_orders(db, limit=10)
        
        # Get recent customers
        customers = await CRUDUser.get_customers(db, limit=10)
        
        # Get team members
        team_members = await CRUDUser.get_team_members(db)
        
        return templates.TemplateResponse("admin/dashboard.html", {
            "request": request,
            "admin": admin,
            "order_stats": order_stats,
            "orders": orders,
            "customers": customers,
            "team_members": team_members
        })
    except AuthenticationError:
        return RedirectResponse(url="/", status_code=303)

@router.get("/services", response_class=HTMLResponse)
async def manage_services(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Manage services"""
    try:
        admin = await get_current_admin(request, db)
        services = await CRUDService.get_all(db)
        
        return templates.TemplateResponse("admin/manage_services.html", {
            "request": request,
            "admin": admin,
            "services": services
        })
    except AuthenticationError:
        return RedirectResponse(url="/", status_code=303)

@router.post("/services/create")
async def create_service(
    request: Request,
    name: str = Form(...),
    description: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db)
):
    """Create new service"""
    try:
        admin = await get_current_admin(request, db)
        
        # Save image if provided
        image_url = None
        if image:
            image_url = await save_upload_file(image)
        
        # Create service
        service_data = ServiceCreate(name=name, description=description)
        service = await CRUDService.create(db, service_data)
        
        # Update image URL if uploaded
        if image_url:
            service.image_url = image_url
            await db.commit()
            await db.refresh(service)
        
        # HTMX response
        return HTMLResponse(f"""
            <tr id="service-{service.id}">
                <td>{service.id}</td>
                <td>
                    {f'<img src="{service.image_url}" class="service-thumb" alt="{service.name}">' if service.image_url else ''}
                    {service.name}
                </td>
                <td>{service.description or '-'}</td>
                <td>
                    <button class="btn btn-sm btn-primary" 
                            hx-get="/admin/services/{service.id}/menu"
                            hx-target="#menu-container">
                        Manage Menu
                    </button>
                    <button class="btn btn-sm btn-warning"
                            hx-get="/admin/services/{service.id}/edit"
                            hx-target="#edit-service-modal .modal-content">
                        Edit
                    </button>
                    <button class="btn btn-sm btn-danger"
                            hx-delete="/admin/services/{service.id}"
                            hx-confirm="Delete this service?">
                        Delete
                    </button>
                </td>
            </tr>
        """)
        
    except Exception as e:
        return HTMLResponse(f"""
            <div class="alert alert-danger">{str(e)}</div>
        """)

@router.get("/services/{service_id}/edit")
async def edit_service_form(
    request: Request,
    service_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get edit service form"""
    try:
        admin = await get_current_admin(request, db)
        service = await CRUDService.get_by_id(db, service_id)
        
        if not service:
            raise NotFoundError("Service")
        
        return HTMLResponse(f"""
            <div class="modal-header">
                <h5 class="modal-title">Edit Service</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <form hx-post="/admin/services/{service.id}/update"
                      hx-encoding="multipart/form-data"
                      hx-target="#service-{service.id}"
                      hx-swap="outerHTML">
                    
                    <div class="mb-3">
                        <label class="form-label">Name</label>
                        <input type="text" class="form-control" name="name" 
                               value="{service.name}" required>
                    </div>
                    
                    <div class="mb-3">
                        <label class="form-label">Description</label>
                        <textarea class="form-control" name="description" 
                                  rows="3">{service.description or ''}</textarea>
                    </div>
                    
                    <div class="mb-3">
                        <label class="form-label">Current Image</label>
                        {f'<img src="{service.image_url}" class="img-thumbnail mb-2" style="max-height: 100px;">' if service.image_url else '<p>No image</p>'}
                        <input type="file" class="form-control" name="image" accept="image/*">
                    </div>
                    
                    <div class="text-end">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="submit" class="btn btn-primary">Save Changes</button>
                    </div>
                </form>
            </div>
        """)
        
    except Exception as e:
        return HTMLResponse(f"""
            <div class="alert alert-danger">{str(e)}</div>
        """)

@router.post("/services/{service_id}/update")
async def update_service(
    request: Request,
    service_id: int,
    name: str = Form(...),
    description: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db)
):
    """Update service"""
    try:
        admin = await get_current_admin(request, db)
        
        # Save image if provided
        image_url = None
        if image:
            image_url = await save_upload_file(image)
        
        # Update service
        update_data = {"name": name, "description": description}
        if image_url:
            update_data["image_url"] = image_url
        
        service = await CRUDService.update(db, service_id, ServiceUpdate(**update_data))
        
        # HTMX response
        return HTMLResponse(f"""
            <tr id="service-{service.id}">
                <td>{service.id}</td>
                <td>
                    {f'<img src="{service.image_url}" class="service-thumb" alt="{service.name}">' if service.image_url else ''}
                    {service.name}
                </td>
                <td>{service.description or '-'}</td>
                <td>
                    <button class="btn btn-sm btn-primary" 
                            hx-get="/admin/services/{service.id}/menu"
                            hx-target="#menu-container">
                        Manage Menu
                    </button>
                    <button class="btn btn-sm btn-warning"
                            hx-get="/admin/services/{service.id}/edit"
                            hx-target="#edit-service-modal .modal-content">
                        Edit
                    </button>
                    <button class="btn btn-sm btn-danger"
                            hx-delete="/admin/services/{service.id}"
                            hx-confirm="Delete this service?">
                        Delete
                    </button>
                </td>
            </tr>
        """)
        
    except Exception as e:
        return HTMLResponse(f"""
            <div class="alert alert-danger">{str(e)}</div>
        """)

@router.delete("/services/{service_id}")
async def delete_service(
    request: Request,
    service_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete service"""
    try:
        admin = await get_current_admin(request, db)
        await CRUDService.delete(db, service_id)
        
        return HTMLResponse("")
        
    except Exception as e:
        return HTMLResponse(f"""
            <div class="alert alert-danger">{str(e)}</div>
        """)

@router.get("/services/{service_id}/menu")
async def service_menu_management(
    request: Request,
    service_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Manage menu for a service"""
    try:
        admin = await get_current_admin(request, db)
        service = await CRUDService.get_by_id(db, service_id)
        menu_items = await CRUDMenuItem.get_by_service(db, service_id, available_only=False)
        
        return HTMLResponse(f"""
            <div class="card">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <h5 class="mb-0">Menu Items for {service.name}</h5>
                    <button class="btn btn-primary btn-sm"
                            hx-get="/admin/menu/create?service_id={service.id}"
                            hx-target="#create-menu-modal .modal-content">
                        Add Menu Item
                    </button>
                </div>
                <div class="card-body">
                    <div class="table-responsive">
                        <table class="table table-hover">
                            <thead>
                                <tr>
                                    <th>ID</th>
                                    <th>Name</th>
                                    <th>Description</th>
                                    <th>Price</th>
                                    <th>Status</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody id="menu-items-list">
                                {"".join([f'''
                                <tr id="menu-item-{item.id}">
                                    <td>{item.id}</td>
                                    <td>
                                        {f'<img src="{item.image_url}" class="menu-thumb" alt="{item.name}">' if item.image_url else ''}
                                        {item.name}
                                    </td>
                                    <td>{item.description or '-'}</td>
                                    <td>₹{item.price:.2f}</td>
                                    <td>
                                        <span class="badge bg-{'success' if item.is_available else 'danger'}">
                                            {'Available' if item.is_available else 'Unavailable'}
                                        </span>
                                    </td>
                                    <td>
                                        <button class="btn btn-sm btn-warning"
                                                hx-get="/admin/menu/{item.id}/edit"
                                                hx-target="#edit-menu-modal .modal-content">
                                            Edit
                                        </button>
                                        <button class="btn btn-sm {'btn-success' if not item.is_available else 'btn-secondary'}"
                                                hx-post="/admin/menu/{item.id}/toggle"
                                                hx-target="#menu-item-{item.id}">
                                            {'Make Available' if not item.is_available else 'Make Unavailable'}
                                        </button>
                                        <button class="btn btn-sm btn-danger"
                                                hx-delete="/admin/menu/{item.id}"
                                                hx-confirm="Delete this menu item?">
                                            Delete
                                        </button>
                                    </td>
                                </tr>
                                ''' for item in menu_items])}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        """)
        
    except Exception as e:
        return HTMLResponse(f"""
            <div class="alert alert-danger">{str(e)}</div>
        """)

@router.get("/menu/create")
async def create_menu_item_form(
    request: Request,
    service_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get create menu item form"""
    try:
        admin = await get_current_admin(request, db)
        
        return HTMLResponse(f"""
            <div class="modal-header">
                <h5 class="modal-title">Add Menu Item</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <form hx-post="/admin/menu/create"
                      hx-encoding="multipart/form-data"
                      hx-target="#menu-items-list"
                      hx-swap="beforeend">
                    
                    <input type="hidden" name="service_id" value="{service_id}">
                    
                    <div class="mb-3">
                        <label class="form-label">Name</label>
                        <input type="text" class="form-control" name="name" required>
                    </div>
                    
                    <div class="mb-3">
                        <label class="form-label">Description</label>
                        <textarea class="form-control" name="description" rows="3"></textarea>
                    </div>
                    
                    <div class="mb-3">
                        <label class="form-label">Price (₹)</label>
                        <input type="number" class="form-control" name="price" 
                               step="0.01" min="0" required>
                    </div>
                    
                    <div class="mb-3">
                        <label class="form-label">Image</label>
                        <input type="file" class="form-control" name="image" accept="image/*">
                    </div>
                    
                    <div class="text-end">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="submit" class="btn btn-primary">Add Item</button>
                    </div>
                </form>
            </div>
        """)
        
    except Exception as e:
        return HTMLResponse(f"""
            <div class="alert alert-danger">{str(e)}</div>
        """)

@router.post("/menu/create")
async def create_menu_item(
    request: Request,
    service_id: int = Form(...),
    name: str = Form(...),
    description: Optional[str] = Form(None),
    price: float = Form(...),
    image: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db)
):
    """Create menu item"""
    try:
        admin = await get_current_admin(request, db)
        
        # Save image if provided
        image_url = None
        if image:
            image_url = await save_upload_file(image)
        
        # Create menu item
        menu_data = MenuItemCreate(
            service_id=service_id,
            name=name,
            description=description,
            price=price
        )
        
        menu_item = await CRUDMenuItem.create(db, menu_data)
        
        # Update image URL if uploaded
        if image_url:
            menu_item.image_url = image_url
            await db.commit()
            await db.refresh(menu_item)
        
        # HTMX response
        return HTMLResponse(f"""
            <tr id="menu-item-{menu_item.id}">
                <td>{menu_item.id}</td>
                <td>
                    {f'<img src="{menu_item.image_url}" class="menu-thumb" alt="{menu_item.name}">' if menu_item.image_url else ''}
                    {menu_item.name}
                </td>
                <td>{menu_item.description or '-'}</td>
                <td>₹{menu_item.price:.2f}</td>
                <td>
                    <span class="badge bg-success">Available</span>
                </td>
                <td>
                    <button class="btn btn-sm btn-warning"
                            hx-get="/admin/menu/{menu_item.id}/edit"
                            hx-target="#edit-menu-modal .modal-content">
                        Edit
                    </button>
                    <button class="btn btn-sm btn-secondary"
                            hx-post="/admin/menu/{menu_item.id}/toggle"
                            hx-target="#menu-item-{menu_item.id}">
                        Make Unavailable
                    </button>
                    <button class="btn btn-sm btn-danger"
                            hx-delete="/admin/menu/{menu_item.id}"
                            hx-confirm="Delete this menu item?">
                        Delete
                    </button>
                </td>
            </tr>
        """)
        
    except Exception as e:
        return HTMLResponse(f"""
            <div class="alert alert-danger">{str(e)}</div>
        """)

@router.get("/menu/{menu_item_id}/edit")
async def edit_menu_item_form(
    request: Request,
    menu_item_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get edit menu item form"""
    try:
        admin = await get_current_admin(request, db)
        menu_item = await CRUDMenuItem.get_by_id(db, menu_item_id)
        
        if not menu_item:
            raise NotFoundError("Menu item")
        
        return HTMLResponse(f"""
            <div class="modal-header">
                <h5 class="modal-title">Edit Menu Item</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <form hx-post="/admin/menu/{menu_item.id}/update"
                      hx-encoding="multipart/form-data"
                      hx-target="#menu-item-{menu_item.id}"
                      hx-swap="outerHTML">
                    
                    <div class="mb-3">
                        <label class="form-label">Name</label>
                        <input type="text" class="form-control" name="name" 
                               value="{menu_item.name}" required>
                    </div>
                    
                    <div class="mb-3">
                        <label class="form-label">Description</label>
                        <textarea class="form-control" name="description" 
                                  rows="3">{menu_item.description or ''}</textarea>
                    </div>
                    
                    <div class="mb-3">
                        <label class="form-label">Price (₹)</label>
                        <input type="number" class="form-control" name="price" 
                               value="{menu_item.price}" step="0.01" min="0" required>
                    </div>
                    
                    <div class="mb-3">
                        <label class="form-label">Current Image</label>
                        {f'<img src="{menu_item.image_url}" class="img-thumbnail mb-2" style="max-height: 100px;">' if menu_item.image_url else '<p>No image</p>'}
                        <input type="file" class="form-control" name="image" accept="image/*">
                    </div>
                    
                    <div class="text-end">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="submit" class="btn btn-primary">Save Changes</button>
                    </div>
                </form>
            </div>
        """)
        
    except Exception as e:
        return HTMLResponse(f"""
            <div class="alert alert-danger">{str(e)}</div>
        """)

@router.post("/menu/{menu_item_id}/update")
async def update_menu_item(
    request: Request,
    menu_item_id: int,
    name: str = Form(...),
    description: Optional[str] = Form(None),
    price: float = Form(...),
    image: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db)
):
    """Update menu item"""
    try:
        admin = await get_current_admin(request, db)
        
        # Save image if provided
        image_url = None
        if image:
            image_url = await save_upload_file(image)
        
        # Update menu item
        update_data = {"name": name, "description": description, "price": price}
        if image_url:
            update_data["image_url"] = image_url
        
        menu_item = await CRUDMenuItem.update(db, menu_item_id, MenuItemUpdate(**update_data))
        
        # HTMX response
        return HTMLResponse(f"""
            <tr id="menu-item-{menu_item.id}">
                <td>{menu_item.id}</td>
                <td>
                    {f'<img src="{menu_item.image_url}" class="menu-thumb" alt="{menu_item.name}">' if menu_item.image_url else ''}
                    {menu_item.name}
                </td>
                <td>{menu_item.description or '-'}</td>
                <td>₹{menu_item.price:.2f}</td>
                <td>
                    <span class="badge bg-{'success' if menu_item.is_available else 'danger'}">
                        {'Available' if menu_item.is_available else 'Unavailable'}
                    </span>
                </td>
                <td>
                    <button class="btn btn-sm btn-warning"
                            hx-get="/admin/menu/{menu_item.id}/edit"
                            hx-target="#edit-menu-modal .modal-content">
                        Edit
                    </button>
                    <button class="btn btn-sm {'btn-success' if not menu_item.is_available else 'btn-secondary'}"
                            hx-post="/admin/menu/{menu_item.id}/toggle"
                            hx-target="#menu-item-{menu_item.id}">
                        {'Make Available' if not menu_item.is_available else 'Make Unavailable'}
                    </button>
                    <button class="btn btn-sm btn-danger"
                            hx-delete="/admin/menu/{menu_item.id}"
                            hx-confirm="Delete this menu item?">
                        Delete
                    </button>
                </td>
            </tr>
        """)
        
    except Exception as e:
        return HTMLResponse(f"""
            <div class="alert alert-danger">{str(e)}</div>
        """)

@router.post("/menu/{menu_item_id}/toggle")
async def toggle_menu_item_availability(
    request: Request,
    menu_item_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Toggle menu item availability"""
    try:
        admin = await get_current_admin(request, db)
        menu_item = await CRUDMenuItem.toggle_availability(db, menu_item_id)
        
        # HTMX response
        return HTMLResponse(f"""
            <tr id="menu-item-{menu_item.id}">
                <td>{menu_item.id}</td>
                <td>
                    {f'<img src="{menu_item.image_url}" class="menu-thumb" alt="{menu_item.name}">' if menu_item.image_url else ''}
                    {menu_item.name}
                </td>
                <td>{menu_item.description or '-'}</td>
                <td>₹{menu_item.price:.2f}</td>
                <td>
                    <span class="badge bg-{'success' if menu_item.is_available else 'danger'}">
                        {'Available' if menu_item.is_available else 'Unavailable'}
                    </span>
                </td>
                <td>
                    <button class="btn btn-sm btn-warning"
                            hx-get="/admin/menu/{menu_item.id}/edit"
                            hx-target="#edit-menu-modal .modal-content">
                        Edit
                    </button>
                    <button class="btn btn-sm {'btn-success' if not menu_item.is_available else 'btn-secondary'}"
                            hx-post="/admin/menu/{menu_item.id}/toggle"
                            hx-target="#menu-item-{menu_item.id}">
                        {'Make Available' if not menu_item.is_available else 'Make Unavailable'}
                    </button>
                    <button class="btn btn-sm btn-danger"
                            hx-delete="/admin/menu/{menu_item.id}"
                            hx-confirm="Delete this menu item?">
                        Delete
                    </button>
                </td>
            </tr>
        """)
        
    except Exception as e:
        return HTMLResponse(f"""
            <div class="alert alert-danger">{str(e)}</div>
        """)

@router.delete("/menu/{menu_item_id}")
async def delete_menu_item(
    request: Request,
    menu_item_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete menu item"""
    try:
        admin = await get_current_admin(request, db)
        await CRUDMenuItem.delete(db, menu_item_id)
        
        return HTMLResponse("")
        
    except Exception as e:
        return HTMLResponse(f"""
            <div class="alert alert-danger">{str(e)}</div>
        """)

@router.get("/team-members", response_class=HTMLResponse)
async def manage_team_members(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Manage team members"""
    try:
        admin = await get_current_admin(request, db)
        team_members = await CRUDUser.get_team_members(db)
        
        return templates.TemplateResponse("admin/manage_team_members.html", {
            "request": request,
            "admin": admin,
            "team_members": team_members
        })
    except AuthenticationError:
        return RedirectResponse(url="/", status_code=303)

@router.post("/team-members/create")
async def create_team_member(
    request: Request,
    name: str = Form(...),
    username: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    """Create team member"""
    try:
        admin = await get_current_admin(request, db)
        
        # Create team member
        team_member_data = TeamMemberCreate(
            name=name,
            username=username,
            email=email,
            phone=phone,
            password=password
        )
        
        team_member = await CRUDUser.create(db, team_member_data)
        
        # HTMX response
        return HTMLResponse(f"""
            <tr id="team-member-{team_member.id}">
                <td>{team_member.id}</td>
                <td>{team_member.name}</td>
                <td>{team_member.username}</td>
                <td>{team_member.email}</td>
                <td>{team_member.phone}</td>
                <td>
                    <span class="badge bg-{'success' if team_member.is_active else 'danger'}">
                        {'Active' if team_member.is_active else 'Inactive'}
                    </span>
                </td>
                <td>
                    <button class="btn btn-sm btn-warning"
                            hx-get="/admin/team-members/{team_member.id}/edit"
                            hx-target="#edit-team-modal .modal-content">
                        Edit
                    </button>
                    <button class="btn btn-sm {'btn-success' if not team_member.is_active else 'btn-secondary'}"
                            hx-post="/admin/team-members/{team_member.id}/toggle"
                            hx-target="#team-member-{team_member.id}">
                        {'Activate' if not team_member.is_active else 'Deactivate'}
                    </button>
                    <button class="btn btn-sm btn-danger"
                            hx-delete="/admin/team-members/{team_member.id}"
                            hx-confirm="Delete this team member?">
                        Delete
                    </button>
                </td>
            </tr>
        """)
        
    except Exception as e:
        return HTMLResponse(f"""
            <div class="alert alert-danger">{str(e)}</div>
        """)

@router.get("/team-members/{member_id}/edit")
async def edit_team_member_form(
    request: Request,
    member_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get edit team member form"""
    try:
        admin = await get_current_admin(request, db)
        team_member = await CRUDUser.get_by_id(db, member_id)
        
        if not team_member or team_member.role != UserRole.TEAM_MEMBER:
            raise NotFoundError("Team member")
        
        return HTMLResponse(f"""
            <div class="modal-header">
                <h5 class="modal-title">Edit Team Member</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <form hx-post="/admin/team-members/{team_member.id}/update"
                      hx-target="#team-member-{team_member.id}"
                      hx-swap="outerHTML">
                    
                    <div class="mb-3">
                        <label class="form-label">Name</label>
                        <input type="text" class="form-control" name="name" 
                               value="{team_member.name}" required>
                    </div>
                    
                    <div class="mb-3">
                        <label class="form-label">Username</label>
                        <input type="text" class="form-control" name="username" 
                               value="{team_member.username}" required>
                    </div>
                    
                    <div class="mb-3">
                        <label class="form-label">Email</label>
                        <input type="email" class="form-control" name="email" 
                               value="{team_member.email}" required>
                    </div>
                    
                    <div class="mb-3">
                        <label class="form-label">Phone</label>
                        <input type="text" class="form-control" name="phone" 
                               value="{team_member.phone}" required>
                    </div>
                    
                    <div class="mb-3">
                        <label class="form-label">New Password (leave empty to keep current)</label>
                        <input type="password" class="form-control" name="password">
                    </div>
                    
                    <div class="text-end">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="submit" class="btn btn-primary">Save Changes</button>
                    </div>
                </form>
            </div>
        """)
        
    except Exception as e:
        return HTMLResponse(f"""
            <div class="alert alert-danger">{str(e)}</div>
        """)

@router.post("/team-members/{member_id}/update")
async def update_team_member(
    request: Request,
    member_id: int,
    name: str = Form(...),
    username: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    password: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """Update team member"""
    try:
        admin = await get_current_admin(request, db)
        
        update_data = {
            "name": name,
            "username": username,
            "email": email,
            "phone": phone
        }
        
        if password:
            update_data["password"] = password
        
        team_member = await CRUDUser.update(db, member_id, UserUpdate(**update_data))
        
        # HTMX response
        return HTMLResponse(f"""
            <tr id="team-member-{team_member.id}">
                <td>{team_member.id}</td>
                <td>{team_member.name}</td>
                <td>{team_member.username}</td>
                <td>{team_member.email}</td>
                <td>{team_member.phone}</td>
                <td>
                    <span class="badge bg-{'success' if team_member.is_active else 'danger'}">
                        {'Active' if team_member.is_active else 'Inactive'}
                    </span>
                </td>
                <td>
                    <button class="btn btn-sm btn-warning"
                            hx-get="/admin/team-members/{team_member.id}/edit"
                            hx-target="#edit-team-modal .modal-content">
                        Edit
                    </button>
                    <button class="btn btn-sm {'btn-success' if not team_member.is_active else 'btn-secondary'}"
                            hx-post="/admin/team-members/{team_member.id}/toggle"
                            hx-target="#team-member-{team_member.id}">
                        {'Activate' if not team_member.is_active else 'Deactivate'}
                    </button>
                    <button class="btn btn-sm btn-danger"
                            hx-delete="/admin/team-members/{team_member.id}"
                            hx-confirm="Delete this team member?">
                        Delete
                    </button>
                </td>
            </tr>
        """)
        
    except Exception as e:
        return HTMLResponse(f"""
            <div class="alert alert-danger">{str(e)}</div>
        """)

@router.post("/team-members/{member_id}/toggle")
async def toggle_team_member_status(
    request: Request,
    member_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Toggle team member active status"""
    try:
        admin = await get_current_admin(request, db)
        team_member = await CRUDUser.get_by_id(db, member_id)
        
        if not team_member:
            raise NotFoundError("Team member")
        
        team_member.is_active = not team_member.is_active
        await db.commit()
        await db.refresh(team_member)
        
        # HTMX response
        return HTMLResponse(f"""
            <tr id="team-member-{team_member.id}">
                <td>{team_member.id}</td>
                <td>{team_member.name}</td>
                <td>{team_member.username}</td>
                <td>{team_member.email}</td>
                <td>{team_member.phone}</td>
                <td>
                    <span class="badge bg-{'success' if team_member.is_active else 'danger'}">
                        {'Active' if team_member.is_active else 'Inactive'}
                    </span>
                </td>
                <td>
                    <button class="btn btn-sm btn-warning"
                            hx-get="/admin/team-members/{team_member.id}/edit"
                            hx-target="#edit-team-modal .modal-content">
                        Edit
                    </button>
                    <button class="btn btn-sm {'btn-success' if not team_member.is_active else 'btn-secondary'}"
                            hx-post="/admin/team-members/{team_member.id}/toggle"
                            hx-target="#team-member-{team_member.id}">
                        {'Activate' if not team_member.is_active else 'Deactivate'}
                    </button>
                    <button class="btn btn-sm btn-danger"
                            hx-delete="/admin/team-members/{team_member.id}"
                            hx-confirm="Delete this team member?">
                        Delete
                    </button>
                </td>
            </tr>
        """)
        
    except Exception as e:
        return HTMLResponse(f"""
            <div class="alert alert-danger">{str(e)}</div>
        """)

@router.delete("/team-members/{member_id}")
async def delete_team_member(
    request: Request,
    member_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete team member"""
    try:
        admin = await get_current_admin(request, db)
        await CRUDUser.delete(db, member_id)
        
        return HTMLResponse("")
        
    except Exception as e:
        return HTMLResponse(f"""
            <div class="alert alert-danger">{str(e)}</div>
        """)

@router.get("/orders", response_class=HTMLResponse)
async def manage_orders(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Manage orders"""
    try:
        admin = await get_current_admin(request, db)
        orders = await CRUDOrder.get_all_orders(db, limit=50)
        team_members = await CRUDUser.get_team_members(db)
        
        return templates.TemplateResponse("admin/manage_orders.html", {
            "request": request,
            "admin": admin,
            "orders": orders,
            "team_members": team_members
        })
    except AuthenticationError:
        return RedirectResponse(url="/", status_code=303)

@router.post("/orders/{order_id}/assign")
async def assign_order_to_team_member(
    request: Request,
    order_id: int,
    team_member_id: int = Form(...),
    db: AsyncSession = Depends(get_db)
):
    """Assign order to team member"""
    try:
        admin = await get_current_admin(request, db)
        order = await CRUDOrder.assign_order(db, order_id, team_member_id)
        
        # Get team member name for display
        team_member = await CRUDUser.get_by_id(db, team_member_id)
        
        # HTMX response
        return HTMLResponse(f"""
            <span class="badge bg-info">
                {team_member.name if team_member else 'Unknown'}
            </span>
        """)
        
    except Exception as e:
        return HTMLResponse(f"""
            <span class="badge bg-danger">Error</span>
            <div class="alert alert-danger mt-2">{str(e)}</div>
        """)

@router.post("/orders/{order_id}/status")
async def update_order_status(
    request: Request,
    order_id: int,
    status: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    """Update order status"""
    try:
        admin = await get_current_admin(request, db)
        
        # Validate status
        if status not in [s.value for s in OrderStatus]:
            raise ValidationError("Invalid status")
        
        order = await CRUDOrder.update(db, order_id, {"status": OrderStatus(status)})
        
        # Get status badge color
        status_colors = {
            "pending": "warning",
            "confirmed": "info",
            "preparing": "primary",
            "out_for_delivery": "success",
            "delivered": "success",
            "cancelled": "danger"
        }
        
        # HTMX response
        return HTMLResponse(f"""
            <span class="badge bg-{status_colors.get(status, 'secondary')}">
                {status.replace('_', ' ').title()}
            </span>
        """)
        
    except Exception as e:
        return HTMLResponse(f"""
            <span class="badge bg-danger">Error</span>
            <div class="alert alert-danger mt-2">{str(e)}</div>
        """)

@router.get("/customers", response_class=HTMLResponse)
async def manage_customers(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Manage customers"""
    try:
        admin = await get_current_admin(request, db)
        customers = await CRUDUser.get_customers(db)
        
        return templates.TemplateResponse("admin/manage_customers.html", {
            "request": request,
            "admin": admin,
            "customers": customers
        })
    except AuthenticationError:
        return RedirectResponse(url="/", status_code=303)

@router.get("/customers/{customer_id}")
async def customer_details(
    request: Request,
    customer_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get customer details"""
    try:
        admin = await get_current_admin(request, db)
        customer = await CRUDUser.get_by_id(db, customer_id)
        
        if not customer or customer.role != UserRole.CUSTOMER:
            raise NotFoundError("Customer")
        
        # Get customer's orders
        orders = await CRUDOrder.get_customer_orders(db, customer_id, limit=20)
        
        # Get customer's sessions
        sessions = await CRUDUser.get_user_sessions(db, customer_id)
        
        # Calculate total spent
        total_spent = sum(order.total_amount for order in orders 
                         if order.status == OrderStatus.DELIVERED)
        
        # Calculate total online time
        total_minutes = 0
        for session in sessions:
            if session.duration_minutes:
                total_minutes += session.duration_minutes
        
        return HTMLResponse(f"""
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Customer Details: {customer.name}</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <div class="row mb-4">
                        <div class="col-md-6">
                            <h6>Personal Information</h6>
                            <p><strong>Name:</strong> {customer.name}</p>
                            <p><strong>Email:</strong> {customer.email}</p>
                            <p><strong>Phone:</strong> {customer.phone}</p>
                            <p><strong>Address:</strong> {customer.address or 'Not provided'}</p>
                        </div>
                        <div class="col-md-6">
                            <h6>Account Information</h6>
                            <p><strong>Username:</strong> {customer.username}</p>
                            <p><strong>Member Since:</strong> {customer.created_at.strftime('%d %b %Y')}</p>
                            <p><strong>Status:</strong> 
                                <span class="badge bg-{'success' if customer.is_active else 'danger'}">
                                    {'Active' if customer.is_active else 'Inactive'}
                                </span>
                            </p>
                            <p><strong>Verified:</strong> 
                                {'Yes' if customer.is_verified else 'No'}
                            </p>
                        </div>
                    </div>
                    
                    <div class="row mb-4">
                        <div class="col-md-6">
                            <div class="card">
                                <div class="card-body">
                                    <h6 class="card-title">Order Statistics</h6>
                                    <p><strong>Total Orders:</strong> {len(orders)}</p>
                                    <p><strong>Total Spent:</strong> ₹{total_spent:.2f}</p>
                                    <p><strong>Successful Orders:</strong> 
                                        {len([o for o in orders if o.status == OrderStatus.DELIVERED])}
                                    </p>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="card">
                                <div class="card-body">
                                    <h6 class="card-title">Session Statistics</h6>
                                    <p><strong>Total Sessions:</strong> {len(sessions)}</p>
                                    <p><strong>Total Online Time:</strong> {round(total_minutes, 2)} minutes</p>
                                    <p><strong>Average Session:</strong> 
                                        {round(total_minutes / len(sessions), 2) if sessions else 0} minutes
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="mb-3">
                        <h6>Recent Orders</h6>
                        <div class="table-responsive">
                            <table class="table table-sm">
                                <thead>
                                    <tr>
                                        <th>Order ID</th>
                                        <th>Date</th>
                                        <th>Service</th>
                                        <th>Amount</th>
                                        <th>Status</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {"".join([f'''
                                    <tr>
                                        <td>#{order.id}</td>
                                        <td>{order.created_at.strftime('%d %b %Y')}</td>
                                        <td>{order.service.name if order.service else 'Unknown'}</td>
                                        <td>₹{order.total_amount:.2f}</td>
                                        <td>
                                            <span class="badge bg-{'info' if order.status == 'pending' else 'warning' if order.status == 'preparing' else 'success' if order.status == 'delivered' else 'danger'}">
                                                {order.status}
                                            </span>
                                        </td>
                                    </tr>
                                    ''' for order in orders[:5]])}
                                </tbody>
                            </table>
                        </div>
                    </div>
                    
                    {f'<p class="text-muted small">Showing 5 of {len(orders)} orders</p>' if len(orders) > 5 else ''}
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

@router.get("/plans", response_class=HTMLResponse)
async def manage_plans(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Manage team member plans"""
    try:
        admin = await get_current_admin(request, db)
        plans = await CRUDTeamMemberPlan.get_all_plans(db)
        team_members = await CRUDUser.get_team_members(db)
        
        return templates.TemplateResponse("admin/manage_plans.html", {
            "request": request,
            "admin": admin,
            "plans": plans,
            "team_members": team_members
        })
    except AuthenticationError:
        return RedirectResponse(url="/", status_code=303)

@router.post("/plans/create")
async def create_plan(
    request: Request,
    description: str = Form(...),
    team_member_ids: List[int] = Form(...),
    image: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db)
):
    """Create team member plan"""
    try:
        admin = await get_current_admin(request, db)
        
        # Save image if provided
        image_url = None
        if image:
            image_url = await save_upload_file(image)
        
        # Create plan
        plan_data = TeamMemberPlanCreate(
            description=description,
            team_member_ids=team_member_ids,
            image_url=image_url
        )
        
        plans = await CRUDTeamMemberPlan.create(db, plan_data, admin.id)
        
        # HTMX response for each created plan
        responses = []
        for plan in plans:
            responses.append(f"""
                <tr id="plan-{plan.id}">
                    <td>{plan.id}</td>
                    <td>{plan.admin.name}</td>
                    <td>{plan.team_member.name}</td>
                    <td>
                        {plan.description[:50]}{'...' if len(plan.description) > 50 else ''}
                    </td>
                    <td>
                        {f'<img src="{plan.image_url}" class="plan-thumb" alt="Plan Image">' if plan.image_url else 'No Image'}
                    </td>
                    <td>
                        <span class="badge bg-{'success' if plan.is_read else 'warning'}">
                            {'Read' if plan.is_read else 'Unread'}
                        </span>
                    </td>
                    <td>{plan.created_at.strftime('%d %b %Y, %I:%M %p')}</td>
                    <td>
                        <button class="btn btn-sm btn-danger"
                                hx-delete="/admin/plans/{plan.id}"
                                hx-confirm="Delete this plan?">
                            Delete
                        </button>
                    </td>
                </tr>
            """)
        
        return HTMLResponse("".join(responses))
        
    except Exception as e:
        return HTMLResponse(f"""
            <div class="alert alert-danger">{str(e)}</div>
        """)

@router.delete("/plans/{plan_id}")
async def delete_plan(
    request: Request,
    plan_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete plan"""
    try:
        admin = await get_current_admin(request, db)
        await CRUDTeamMemberPlan.delete(db, plan_id)
        
        return HTMLResponse("")
        
    except Exception as e:
        return HTMLResponse(f"""
            <div class="alert alert-danger">{str(e)}</div>
        """)

@router.get("/reports/online-time")
async def online_time_report(
    request: Request,
    user_type: str = "customer",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get online time report"""
    try:
        admin = await get_current_admin(request, db)
        
        # Parse dates
        from datetime import datetime
        start = datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else None
        end = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None
        
        # Get report
        report = await CRUDUser.get_online_time_report(db, None, start, end)
        
        # Filter by user type
        if user_type == "customer":
            report = [r for r in report if r["role"] == "customer"]
        elif user_type == "team_member":
            report = [r for r in report if r["role"] == "team_member"]
        
        # HTMX response
        rows_html = ""
        for row in report:
            rows_html += f"""
            <tr>
                <td>{row['user_id']}</td>
                <td>{row['name']}</td>
                <td>{row['username']}</td>
                <td>{row['role'].title()}</td>
                <td>{row['session_count']}</td>
                <td>{row['total_minutes']} minutes</td>
                <td>{round(row['total_minutes'] / 60, 2) if row['total_minutes'] > 0 else 0} hours</td>
            </tr>
            """
        
        return HTMLResponse(f"""
            <div class="table-responsive">
                <table class="table table-hover">
                    <thead>
                        <tr>
                            <th>User ID</th>
                            <th>Name</th>
                            <th>Username</th>
                            <th>Role</th>
                            <th>Sessions</th>
                            <th>Total Minutes</th>
                            <th>Total Hours</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows_html if rows_html else '<tr><td colspan="7" class="text-center">No data found</td></tr>'}
                    </tbody>
                </table>
            </div>
        """)
        
    except Exception as e:
        return HTMLResponse(f"""
            <div class="alert alert-danger">{str(e)}</div>
        """)