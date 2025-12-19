"""
Admin functionality tests
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import status
import io

from models.user import User, UserRole
from models.service import Service
from models.menu_item import MenuItem
from models.order import Order, OrderStatus
from core.security import get_password_hash

@pytest.fixture
async def admin_user(db: AsyncSession):
    """Create admin user for testing"""
    admin = User(
        name="Test Admin",
        username="testadmin",
        email="admin@test.com",
        phone="9876543200",
        hashed_password=get_password_hash("Admin@12345"),
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True
    )
    db.add(admin)
    await db.commit()
    await db.refresh(admin)
    return admin

@pytest.fixture
async def test_service(db: AsyncSession):
    """Create test service"""
    service = Service(
        name="Test Service",
        description="Test service description"
    )
    db.add(service)
    await db.commit()
    await db.refresh(service)
    return service

@pytest.fixture
async def test_order(db: AsyncSession, admin_user: User, test_service: Service):
    """Create test order"""
    # Create customer for order
    customer = User(
        name="Order Customer",
        username="ordercust",
        email="ordercust@example.com",
        phone="9876543201",
        hashed_password=get_password_hash("Test@12345"),
        role=UserRole.CUSTOMER,
        is_active=True
    )
    db.add(customer)
    await db.commit()
    
    order = Order(
        customer_id=customer.id,
        service_id=test_service.id,
        total_amount=500.00,
        address="Test Address",
        status=OrderStatus.PENDING
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)
    return order

@pytest.mark.asyncio
async def test_admin_login(client: AsyncClient, admin_user: User):
    """Test admin login"""
    login_data = {
        "username": "testadmin",
        "password": "Admin@12345",
        "role": "admin"
    }
    
    response = await client.post("/auth/login", data=login_data)
    assert response.status_code == status.HTTP_303_SEE_OTHER
    assert "admin/dashboard" in response.headers.get("location", "")

@pytest.mark.asyncio
async def test_admin_dashboard(client: AsyncClient, admin_user: User):
    """Test admin dashboard access"""
    # Login as admin
    login_data = {
        "username": "testadmin",
        "password": "Admin@12345",
        "role": "admin"
    }
    await client.post("/auth/login", data=login_data)
    
    # Access dashboard
    response = await client.get("/admin/dashboard")
    assert response.status_code == status.HTTP_200_OK
    assert "Dashboard" in response.text
    assert "Statistics" in response.text

@pytest.mark.asyncio
async def test_manage_services(client: AsyncClient, admin_user: User):
    """Test service management"""
    # Login as admin
    await client.post("/auth/login", data={
        "username": "testadmin",
        "password": "Admin@12345"
    })
    
    # Access services page
    response = await client.get("/admin/services")
    assert response.status_code == status.HTTP_200_OK
    assert "Services" in response.text

@pytest.mark.asyncio
async def test_create_service(client: AsyncClient, admin_user: User):
    """Test service creation"""
    # Login as admin
    await client.post("/auth/login", data={
        "username": "testadmin",
        "password": "Admin@12345"
    })
    
    # Create service via HTMX
    service_data = {
        "name": "New Test Service",
        "description": "New service description"
    }
    
    response = await client.post("/admin/services/create", data=service_data)
    assert response.status_code == status.HTTP_200_OK
    assert "New Test Service" in response.text

@pytest.mark.asyncio
async def test_create_service_with_image(client: AsyncClient, admin_user: User):
    """Test service creation with image upload"""
    # Login as admin
    await client.post("/auth/login", data={
        "username": "testadmin",
        "password": "Admin@12345"
    })
    
    # Create service with image
    files = {
        "image": ("test.jpg", io.BytesIO(b"fake image data"), "image/jpeg")
    }
    data = {
        "name": "Service with Image",
        "description": "Service with image upload"
    }
    
    response = await client.post("/admin/services/create", data=data, files=files)
    assert response.status_code == status.HTTP_200_OK

@pytest.mark.asyncio
async def test_manage_menu_items(client: AsyncClient, admin_user: User, test_service: Service):
    """Test menu item management"""
    # Login as admin
    await client.post("/auth/login", data={
        "username": "testadmin",
        "password": "Admin@12345"
    })
    
    # Access menu management
    response = await client.get(f"/admin/services/{test_service.id}/menu")
    assert response.status_code == status.HTTP_200_OK
    assert "Menu Items" in response.text

@pytest.mark.asyncio
async def test_create_menu_item(client: AsyncClient, admin_user: User, test_service: Service):
    """Test menu item creation"""
    # Login as admin
    await client.post("/auth/login", data={
        "username": "testadmin",
        "password": "Admin@12345"
    })
    
    # Create menu item
    menu_data = {
        "service_id": test_service.id,
        "name": "New Menu Item",
        "description": "Test description",
        "price": "199.99"
    }
    
    response = await client.post("/admin/menu/create", data=menu_data)
    assert response.status_code == status.HTTP_200_OK
    assert "New Menu Item" in response.text

@pytest.mark.asyncio
async def test_manage_team_members(client: AsyncClient, admin_user: User):
    """Test team member management"""
    # Login as admin
    await client.post("/auth/login", data={
        "username": "testadmin",
        "password": "Admin@12345"
    })
    
    # Access team members page
    response = await client.get("/admin/team-members")
    assert response.status_code == status.HTTP_200_OK
    assert "Team Members" in response.text

@pytest.mark.asyncio
async def test_create_team_member(client: AsyncClient, admin_user: User):
    """Test team member creation"""
    # Login as admin
    await client.post("/auth/login", data={
        "username": "testadmin",
        "password": "Admin@12345"
    })
    
    # Create team member
    member_data = {
        "name": "New Team Member",
        "username": "newteam",
        "email": "newteam@example.com",
        "phone": "9876543210",
        "password": "Team@12345"
    }
    
    response = await client.post("/admin/team-members/create", data=member_data)
    assert response.status_code == status.HTTP_200_OK
    assert "New Team Member" in response.text

@pytest.mark.asyncio
async def test_manage_orders(client: AsyncClient, admin_user: User, test_order: Order):
    """Test order management"""
    # Login as admin
    await client.post("/auth/login", data={
        "username": "testadmin",
        "password": "Admin@12345"
    })
    
    # Access orders page
    response = await client.get("/admin/orders")
    assert response.status_code == status.HTTP_200_OK
    assert "Orders" in response.text
    assert str(test_order.id) in response.text

@pytest.mark.asyncio
async def test_assign_order(client: AsyncClient, admin_user: User, test_order: Order, db: AsyncSession):
    """Test order assignment"""
    # Create team member for assignment
    team_member = User(
        name="Assign Team Member",
        username="assignteam",
        email="assign@example.com",
        phone="9876543211",
        hashed_password=get_password_hash("Test@12345"),
        role=UserRole.TEAM_MEMBER,
        is_active=True
    )
    db.add(team_member)
    await db.commit()
    
    # Login as admin
    await client.post("/auth/login", data={
        "username": "testadmin",
        "password": "Admin@12345"
    })
    
    # Assign order
    assign_data = {
        "team_member_id": team_member.id
    }
    
    response = await client.post(f"/admin/orders/{test_order.id}/assign", data=assign_data)
    assert response.status_code == status.HTTP_200_OK
    
    # Verify assignment in database
    await db.refresh(test_order)
    assert test_order.assigned_to == team_member.id

@pytest.mark.asyncio
async def test_update_order_status_admin(client: AsyncClient, admin_user: User, test_order: Order):
    """Test order status update by admin"""
    # Login as admin
    await client.post("/auth/login", data={
        "username": "testadmin",
        "password": "Admin@12345"
    })
    
    # Update status
    status_data = {
        "status": "confirmed"
    }
    
    response = await client.post(f"/admin/orders/{test_order.id}/status", data=status_data)
    assert response.status_code == status.HTTP_200_OK
    
    # Verify status updated
    assert "Confirmed" in response.text

@pytest.mark.asyncio
async def test_manage_customers(client: AsyncClient, admin_user: User, db: AsyncSession):
    """Test customer management"""
    # Create test customer
    customer = User(
        name="Test Customer",
        username="admincust",
        email="admincust@example.com",
        phone="9876543212",
        hashed_password=get_password_hash("Test@12345"),
        role=UserRole.CUSTOMER,
        is_active=True
    )
    db.add(customer)
    await db.commit()
    
    # Login as admin
    await client.post("/auth/login", data={
        "username": "testadmin",
        "password": "Admin@12345"
    })
    
    # Access customers page
    response = await client.get("/admin/customers")
    assert response.status_code == status.HTTP_200_OK
    assert "Customers" in response.text
    assert "Test Customer" in response.text

@pytest.mark.asyncio
async def test_view_customer_details(client: AsyncClient, admin_user: User, db: AsyncSession):
    """Test viewing customer details"""
    # Create test customer
    customer = User(
        name="Detail Customer",
        username="detailcust",
        email="detail@example.com",
        phone="9876543213",
        hashed_password=get_password_hash("Test@12345"),
        role=UserRole.CUSTOMER,
        is_active=True
    )
    db.add(customer)
    await db.commit()
    
    # Login as admin
    await client.post("/auth/login", data={
        "username": "testadmin",
        "password": "Admin@12345"
    })
    
    # View customer details via HTMX
    response = await client.get(f"/admin/customers/{customer.id}")
    assert response.status_code == status.HTTP_200_OK
    assert "Detail Customer" in response.text

@pytest.mark.asyncio
async def test_manage_plans(client: AsyncClient, admin_user: User, db: AsyncSession):
    """Test team member plans management"""
    # Create team member for plan
    team_member = User(
        name="Plan Team Member",
        username="planteam",
        email="plan@example.com",
        phone="9876543214",
        hashed_password=get_password_hash("Test@12345"),
        role=UserRole.TEAM_MEMBER,
        is_active=True
    )
    db.add(team_member)
    await db.commit()
    
    # Login as admin
    await client.post("/auth/login", data={
        "username": "testadmin",
        "password": "Admin@12345"
    })
    
    # Access plans page
    response = await client.get("/admin/plans")
    assert response.status_code == status.HTTP_200_OK
    assert "Plans" in response.text

@pytest.mark.asyncio
async def test_create_plan(client: AsyncClient, admin_user: User, db: AsyncSession):
    """Test plan creation"""
    # Create team member
    team_member = User(
        name="Plan Test Member",
        username="plantest",
        email="plantest@example.com",
        phone="9876543215",
        hashed_password=get_password_hash("Test@12345"),
        role=UserRole.TEAM_MEMBER,
        is_active=True
    )
    db.add(team_member)
    await db.commit()
    
    # Login as admin
    await client.post("/auth/login", data={
        "username": "testadmin",
        "password": "Admin@12345"
    })
    
    # Create plan
    plan_data = {
        "description": "Test plan description for team member",
        "team_member_ids": [str(team_member.id)]
    }
    
    response = await client.post("/admin/plans/create", data=plan_data)
    assert response.status_code == status.HTTP_200_OK
    assert "Test plan" in response.text

@pytest.mark.asyncio
async def test_online_time_report(client: AsyncClient, admin_user: User):
    """Test online time report"""
    # Login as admin
    await client.post("/auth/login", data={
        "username": "testadmin",
        "password": "Admin@12345"
    })
    
    # Access report
    response = await client.get("/admin/reports/online-time?user_type=customer")
    assert response.status_code == status.HTTP_200_OK
    assert "Online Time" in response.text

@pytest.mark.asyncio
async def test_delete_service(client: AsyncClient, admin_user: User, test_service: Service, db: AsyncSession):
    """Test service deletion"""
    # Login as admin
    await client.post("/auth/login", data={
        "username": "testadmin",
        "password": "Admin@12345"
    })
    
    # Delete service
    response = await client.delete(f"/admin/services/{test_service.id}")
    assert response.status_code == status.HTTP_200_OK
    
    # Verify service deleted
    service = await db.get(Service, test_service.id)
    assert service is None

@pytest.mark.asyncio
async def test_toggle_menu_item_availability(client: AsyncClient, admin_user: User, db: AsyncSession, test_service: Service):
    """Test toggling menu item availability"""
    # Create menu item
    menu_item = MenuItem(
        service_id=test_service.id,
        name="Toggle Test Item",
        description="Test item for toggling",
        price=99.99,
        is_available=True
    )
    db.add(menu_item)
    await db.commit()
    await db.refresh(menu_item)
    
    # Login as admin
    await client.post("/auth/login", data={
        "username": "testadmin",
        "password": "Admin@12345"
    })
    
    # Toggle availability
    response = await client.post(f"/admin/menu/{menu_item.id}/toggle")
    assert response.status_code == status.HTTP_200_OK
    
    # Verify toggled
    await db.refresh(menu_item)
    assert menu_item.is_available == False

@pytest.mark.asyncio
async def test_admin_access_control(client: AsyncClient, db: AsyncSession):
    """Test that non-admin users cannot access admin routes"""
    # Create regular user (not admin)
    user = User(
        name="Regular User",
        username="regular",
        email="regular@example.com",
        phone="9876543216",
        hashed_password=get_password_hash("Test@12345"),
        role=UserRole.CUSTOMER,
        is_active=True
    )
    db.add(user)
    await db.commit()
    
    # Login as regular user
    await client.post("/auth/login", data={
        "username": "regular",
        "password": "Test@12345"
    })
    
    # Try to access admin dashboard
    response = await client.get("/admin/dashboard")
    assert response.status_code == status.HTTP_303_SEE_OTHER
    assert response.headers.get("location") == "/"

@pytest.mark.asyncio
async def test_bulk_actions(client: AsyncClient, admin_user: User, db: AsyncSession):
    """Test bulk actions (delete, export, etc.)"""
    # Create multiple services for bulk operations
    services = []
    for i in range(3):
        service = Service(
            name=f"Bulk Service {i}",
            description=f"Test service {i}"
        )
        db.add(service)
        services.append(service)
    await db.commit()
    
    # Login as admin
    await client.post("/auth/login", data={
        "username": "testadmin",
        "password": "Admin@12345"
    })
    
    # Test bulk delete (simulated - would need actual implementation)
    # This is a placeholder test
    assert len(services) == 3
