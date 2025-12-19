"""
Team member router for team member endpoints
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
from models.team_member_plan import TeamMemberPlan
from crud.user import CRUDUser
from crud.order import CRUDOrder
from crud.team_member_plan import CRUDTeamMemberPlan
from core.security import verify_token
from core.exceptions import AuthenticationError, NotFoundError
from core.sms import send_sms

router = APIRouter()
templates = Jinja2Templates(directory="templates")
logger = structlog.get_logger(__name__)

def get_current_team_member(request: Request, db: AsyncSession = Depends(get_db)):
    """Get current team member from token"""
    token = request.cookies.get("access_token")
    if not token:
        raise AuthenticationError("Not authenticated")
    
    payload = verify_token(token)
    if payload.get("role") != "team_member":
        raise AuthenticationError("Access denied")
    
    user = CRUDUser.get_by_id(db, payload.get("user_id"))
    if not user or user.role != UserRole.TEAM_MEMBER:
        raise AuthenticationError("Invalid team member")
    
    return user

@router.get("/dashboard", response_class=HTMLResponse)
async def team_member_dashboard(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Team member dashboard"""
    try:
        team_member = await get_current_team_member(request, db)
        
        # Get assigned orders
        orders = await CRUDOrder.get_team_member_orders(db, team_member.id)
        
        # Get unread plans
        plans = await CRUDTeamMemberPlan.get_team_member_plans(db, team_member.id)
        unread_plans = [p for p in plans if not p.is_read]
        
        # Get today's session
        from datetime import date
        sessions = await CRUDUser.get_user_sessions(db, team_member.id, start_date=date.today())
        
        return templates.TemplateResponse("team_member/dashboard.html", {
            "request": request,
            "team_member": team_member,
            "orders": orders,
            "unread_plans": unread_plans[:5],  # Show only 5 latest
            "total_plans": len(plans),
            "today_sessions": len(sessions)
        })
    except AuthenticationError:
        return RedirectResponse(url="/auth/login?role=team_member", status_code=303)

@router.get("/orders", response_class=HTMLResponse)
async def team_member_orders(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """View assigned orders"""
    try:
        team_member = await get_current_team_member(request, db)
        orders = await CRUDOrder.get_team_member_orders(db, team_member.id)
        
        return templates.TemplateResponse("team_member/orders.html", {
            "request": request,
            "team_member": team_member,
            "orders": orders
        })
    except AuthenticationError:
        return RedirectResponse(url="/auth/login?role=team_member", status_code=303)

@router.get("/order/{order_id}/details")
async def order_details_for_delivery(
    request: Request,
    order_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get order details for delivery"""
    try:
        team_member = await get_current_team_member(request, db)
        order = await CRUDOrder.get_by_id(db, order_id, with_items=True)
        
        if not order or order.assigned_to != team_member.id:
            raise NotFoundError("Order")
        
        # HTMX response for modal
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
        
        # Customer info
        customer_html = f"""
        <div class="mb-3">
            <h6>Customer Information</h6>
            <p><strong>Name:</strong> {order.customer.name}</p>
            <p><strong>Phone:</strong> {order.customer.phone}</p>
            <p><strong>Address:</strong> {order.address}</p>
            {f'<p><strong>Instructions:</strong> {order.special_instructions}</p>' if order.special_instructions else ''}
        </div>
        """
        
        return HTMLResponse(f"""
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Order #{order.id} - Delivery Details</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <div class="row mb-3">
                        <div class="col-6">
                            <strong>Status:</strong>
                            <span class="badge bg-{'info' if order.status == 'pending' else 'warning' if order.status == 'preparing' else 'success' if order.status == 'out_for_delivery' else 'danger'}">
                                {order.status.replace('_', ' ').title()}
                            </span>
                        </div>
                        <div class="col-6">
                            <strong>Total:</strong> ₹{order.total_amount:.2f}
                        </div>
                    </div>
                    
                    {customer_html}
                    
                    <div class="mb-3">
                        <h6>Order Items</h6>
                        <div class="table-responsive">
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
                        </div>
                    </div>
                    
                    <div class="text-muted small">
                        Ordered: {order.created_at.strftime('%d %b %Y, %I:%M %p')}
                        {f'<br>Confirmed: {order.confirmed_at.strftime("%d %b %Y, %I:%M %p")}' if order.confirmed_at else ''}
                        {f'<br>Prepared: {order.prepared_at.strftime("%d %b %Y, %I:%M %p")}' if order.prepared_at else ''}
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                    
                    {f'<button type="button" class="btn btn-primary" hx-post="/team/order/{order.id}/generate-otp" hx-target="#otp-section">Generate OTP</button>' if order.status == OrderStatus.OUT_FOR_DELIVERY else ''}
                    
                    {f'<button type="button" class="btn btn-success" hx-post="/team/order/{order.id}/mark-delivered" hx-confirm="Mark as delivered?">Mark as Delivered</button>' if order.status == OrderStatus.OUT_FOR_DELIVERY else ''}
                </div>
            </div>
        """)
        
    except Exception as e:
        return HTMLResponse(f"""
            <div class="alert alert-danger">{str(e)}</div>
        """)

@router.post("/order/{order_id}/status")
async def update_order_status_team(
    request: Request,
    order_id: int,
    status: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    """Update order status (team member)"""
    try:
        team_member = await get_current_team_member(request, db)
        order = await CRUDOrder.get_by_id(db, order_id)
        
        if not order or order.assigned_to != team_member.id:
            raise NotFoundError("Order")
        
        # Validate status transition
        valid_transitions = {
            OrderStatus.CONFIRMED: [OrderStatus.PREPARING],
            OrderStatus.PREPARING: [OrderStatus.OUT_FOR_DELIVERY],
            OrderStatus.OUT_FOR_DELIVERY: [OrderStatus.DELIVERED]
        }
        
        current_status = order.status
        new_status = OrderStatus(status)
        
        if (current_status in valid_transitions and 
            new_status not in valid_transitions[current_status]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot change status from {current_status} to {new_status}"
            )
        
        # Update status
        order.update_status(new_status)
        await db.commit()
        
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
            {"<span class='badge bg-success ms-2'>Updated</span>" if status != current_status else ""}
        """)
        
    except Exception as e:
        return HTMLResponse(f"""
            <span class="badge bg-danger">Error</span>
            <div class="alert alert-danger mt-2">{str(e)}</div>
        """)

@router.post("/order/{order_id}/generate-otp")
async def generate_otp_for_delivery(
    request: Request,
    order_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Generate OTP for order delivery"""
    try:
        team_member = await get_current_team_member(request, db)
        
        # Generate OTP
        otp = await CRUDOrder.generate_otp_for_delivery(db, order_id)
        
        # Get order and customer
        order = await CRUDOrder.get_by_id(db, order_id, with_items=True)
        
        # Send SMS to customer
        if order and order.customer:
            message = f"Your Bite Me Buddy order #{order_id} is out for delivery. OTP: {otp}. Valid for 5 minutes."
            # await send_sms(order.customer.phone, message)  # Uncomment when Twilio is configured
        
        # HTMX response with OTP form
        return HTMLResponse(f"""
            <div id="otp-section" class="mt-3 p-3 border rounded">
                <h6>Delivery OTP Generated</h6>
                <div class="alert alert-info">
                    <strong>OTP: {otp}</strong><br>
                    Sent to customer: {order.customer.phone if order and order.customer else 'N/A'}<br>
                    Valid for 5 minutes
                </div>
                
                <form hx-post="/team/order/{order_id}/verify-otp" 
                      hx-target="#delivery-result"
                      class="mt-2">
                    <div class="mb-3">
                        <label class="form-label">Enter OTP from Customer</label>
                        <input type="text" class="form-control" name="otp" 
                               maxlength="4" pattern="\\d{{4}}" required 
                               placeholder="Enter 4-digit OTP">
                    </div>
                    <button type="submit" class="btn btn-success w-100">
                        Verify OTP & Complete Delivery
                    </button>
                </form>
                
                <div id="delivery-result"></div>
            </div>
        """)
        
    except Exception as e:
        return HTMLResponse(f"""
            <div class="alert alert-danger">{str(e)}</div>
        """)

@router.post("/order/{order_id}/verify-otp")
async def verify_otp_for_delivery(
    request: Request,
    order_id: int,
    otp: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    """Verify OTP for order delivery"""
    try:
        team_member = await get_current_team_member(request, db)
        
        # Verify OTP
        success = await CRUDOrder.verify_otp(db, order_id, otp)
        
        if success:
            # Update order status to delivered
            order = await CRUDOrder.get_by_id(db, order_id)
            order.update_status(OrderStatus.DELIVERED)
            await db.commit()
            
            return HTMLResponse(f"""
                <div class="alert alert-success">
                    <i class="fas fa-check-circle"></i>
                    <strong>Delivery Successful!</strong><br>
                    Order #{order_id} has been marked as delivered.
                </div>
                <script>
                    setTimeout(() => {{
                        location.reload();
                    }}, 2000);
                </script>
            """)
        else:
            return HTMLResponse(f"""
                <div class="alert alert-danger">
                    <i class="fas fa-times-circle"></i>
                    <strong>Invalid OTP!</strong><br>
                    Please check the OTP and try again.
                </div>
            """)
        
    except Exception as e:
        return HTMLResponse(f"""
            <div class="alert alert-danger">{str(e)}</div>
        """)

@router.post("/order/{order_id}/mark-delivered")
async def mark_order_delivered(
    request: Request,
    order_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Mark order as delivered (without OTP verification)"""
    try:
        team_member = await get_current_team_member(request, db)
        order = await CRUDOrder.get_by_id(db, order_id)
        
        if not order or order.assigned_to != team_member.id:
            raise NotFoundError("Order")
        
        # Mark as delivered
        order.update_status(OrderStatus.DELIVERED)
        await db.commit()
        
        return HTMLResponse(f"""
            <div class="alert alert-success">
                <i class="fas fa-check-circle"></i>
                Order marked as delivered!
            </div>
            <script>
                setTimeout(() => {{
                    location.reload();
                }}, 1500);
            </script>
        """)
        
    except Exception as e:
        return HTMLResponse(f"""
            <div class="alert alert-danger">{str(e)}</div>
        """)

@router.get("/plans", response_class=HTMLResponse)
async def view_plans(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """View team member plans"""
    try:
        team_member = await get_current_team_member(request, db)
        plans = await CRUDTeamMemberPlan.get_team_member_plans(db, team_member.id)
        
        return templates.TemplateResponse("team_member/plans.html", {
            "request": request,
            "team_member": team_member,
            "plans": plans
        })
    except AuthenticationError:
        return RedirectResponse(url="/auth/login?role=team_member", status_code=303)

@router.get("/plan/{plan_id}")
async def view_plan_details(
    request: Request,
    plan_id: int,
    db: AsyncSession = Depends(get_db)
):
    """View plan details"""
    try:
        team_member = await get_current_team_member(request, db)
        plan = await CRUDTeamMemberPlan.get_by_id(db, plan_id)
        
        if not plan or plan.team_member_id != team_member.id:
            raise NotFoundError("Plan")
        
        # Mark as read
        await CRUDTeamMemberPlan.mark_as_read(db, plan_id, team_member.id)
        
        # HTMX response for modal
        return HTMLResponse(f"""
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Plan from Admin</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <div class="mb-3">
                        <p><strong>From:</strong> {plan.admin.name}</p>
                        <p><strong>Date:</strong> {plan.created_at.strftime('%d %b %Y, %I:%M %p')}</p>
                    </div>
                    
                    <div class="mb-3">
                        <h6>Plan Details</h6>
                        <div class="p-3 bg-light rounded">
                            {plan.description.replace('\\n', '<br>')}
                        </div>
                    </div>
                    
                    {f'''
                    <div class="mb-3">
                        <h6>Attachment</h6>
                        <img src="{plan.image_url}" class="img-fluid rounded" alt="Plan Image">
                    </div>
                    ''' if plan.image_url else ''}
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

@router.post("/plan/{plan_id}/mark-read")
async def mark_plan_as_read(
    request: Request,
    plan_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Mark plan as read"""
    try:
        team_member = await get_current_team_member(request, db)
        plan = await CRUDTeamMemberPlan.mark_as_read(db, plan_id, team_member.id)
        
        if plan:
            return HTMLResponse(f"""
                <span class="badge bg-success">Read</span>
            """)
        else:
            return HTMLResponse(f"""
                <span class="badge bg-danger">Error</span>
            """)
        
    except Exception as e:
        return HTMLResponse(f"""
            <span class="badge bg-danger">Error</span>
        """)

@router.get("/profile", response_class=HTMLResponse)
async def team_member_profile(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Team member profile"""
    try:
        team_member = await get_current_team_member(request, db)
        
        # Get session statistics
        sessions = await CRUDUser.get_user_sessions(db, team_member.id)
        
        # Get assigned orders statistics
        orders = await CRUDOrder.get_team_member_orders(db, team_member.id)
        delivered_orders = [o for o in orders if o.status == OrderStatus.DELIVERED]
        
        # Get plans statistics
        plans = await CRUDTeamMemberPlan.get_team_member_plans(db, team_member.id)
        read_plans = [p for p in plans if p.is_read]
        
        # Calculate total online time
        total_minutes = 0
        for session in sessions:
            if session.duration_minutes:
                total_minutes += session.duration_minutes
        
        return templates.TemplateResponse("team_member/profile.html", {
            "request": request,
            "team_member": team_member,
            "sessions": len(sessions),
            "total_minutes": round(total_minutes, 2),
            "total_orders": len(orders),
            "delivered_orders": len(delivered_orders),
            "total_plans": len(plans),
            "read_plans": len(read_plans)
        })
    except AuthenticationError:
        return RedirectResponse(url="/auth/login?role=team_member", status_code=303)

@router.get("/attendance")
async def attendance_report(
    request: Request,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get attendance report"""
    try:
        team_member = await get_current_team_member(request, db)
        
        # Parse dates
        from datetime import datetime
        start = datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else None
        end = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None
        
        # Get sessions
        sessions = await CRUDUser.get_user_sessions(db, team_member.id, start, end)
        
        # Calculate statistics
        total_sessions = len(sessions)
        total_minutes = 0
        sessions_by_date = {}
        
        for session in sessions:
            date_str = session.date.strftime("%Y-%m-%d")
            if date_str not in sessions_by_date:
                sessions_by_date[date_str] = []
            sessions_by_date[date_str].append(session)
            
            if session.duration_minutes:
                total_minutes += session.duration_minutes
        
        # HTMX response
        rows_html = ""
        for date_str, date_sessions in sorted(sessions_by_date.items(), reverse=True):
            date_minutes = sum(s.duration_minutes or 0 for s in date_sessions)
            first_login = min(s.login_time for s in date_sessions).strftime("%I:%M %p")
            last_logout = max(s.logout_time for s in date_sessions if s.logout_time)
            last_logout_str = last_logout.strftime("%I:%M %p") if last_logout else "Still online"
            
            rows_html += f"""
            <tr>
                <td>{date_str}</td>
                <td>{len(date_sessions)}</td>
                <td>{first_login}</td>
                <td>{last_logout_str}</td>
                <td>{round(date_minutes, 2)} minutes</td>
                <td>{round(date_minutes / 60, 2) if date_minutes > 0 else 0} hours</td>
            </tr>
            """
        
        return HTMLResponse(f"""
            <div class="card">
                <div class="card-header">
                    <h5 class="mb-0">Attendance Report</h5>
                </div>
                <div class="card-body">
                    <div class="row mb-4">
                        <div class="col-md-3">
                            <div class="card bg-light">
                                <div class="card-body text-center">
                                    <h6 class="card-title">Total Sessions</h6>
                                    <h3>{total_sessions}</h3>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="card bg-light">
                                <div class="card-body text-center">
                                    <h6 class="card-title">Total Time</h6>
                                    <h3>{round(total_minutes / 60, 2)} hrs</h3>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="card bg-light">
                                <div class="card-body text-center">
                                    <h6 class="card-title">Average Session</h6>
                                    <h3>{round(total_minutes / total_sessions, 2) if total_sessions > 0 else 0} min</h3>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="card bg-light">
                                <div class="card-body text-center">
                                    <h6 class="card-title">Days Active</h6>
                                    <h3>{len(sessions_by_date)}</h3>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="table-responsive">
                        <table class="table table-hover">
                            <thead>
                                <tr>
                                    <th>Date</th>
                                    <th>Sessions</th>
                                    <th>First Login</th>
                                    <th>Last Logout</th>
                                    <th>Total Minutes</th>
                                    <th>Total Hours</th>
                                </tr>
                            </thead>
                            <tbody>
                                {rows_html if rows_html else '<tr><td colspan="6" class="text-center">No data found</td></tr>'}
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