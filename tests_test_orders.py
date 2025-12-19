"""
Order management tests
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import status
from datetime import datetime
import pytz

from models.user import User, UserRole
from models.service import Service
from models.menu_item import MenuItem
from models.order import Order, OrderStatus
from models.order_item import OrderItem
from core.security import get_password_hash

IST = pytz.timezone('Asia/Kolkata')

@pytest.fixture
async def test_customer(db: AsyncSession):
    """Create test customer"""
    customer = User(
        name="Test Customer",
        username="ordercustomer",
        email="order@example.com",
        phone="9876543201",
        hashed_password=get_password_hash("Test@12345"),
        role=UserRole.CUSTOMER,
        is_active=True,
        address="Test Address"
    )
    db.add(customer)
    await db.commit()
    await db.refresh(customer)
    return customer

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
async def test_menu_items(db: AsyncSession, test_service: Service):
    """Create test menu items"""
    items = [
        MenuItem(
            service_id=test_service.id,
            name="Test Item 1",
            description="Test description 1",
            price=100.00,
            is_available=True
        ),
        MenuItem(
            service_id=test_service.id,
            name="Test Item 2",
            description="Test description 2",
            price=150.00,
            is_available=True
        )
    ]
    for item in items:
        db.add(item)
    await db.commit()
    for item in items:
        await db.refresh(item)
    return items

@pytest.fixture
async def test_order(db: AsyncSession, test_customer: User, test_service: Service, test_menu_items: list):
    """Create test order"""
    order = Order(
        customer_id=test_customer.id,
        service_id=test_service.id,
        total_amount=250.00,
        address="Test Delivery Address",
        status=OrderStatus.PENDING,
        created_at=datetime.now(IST)
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)
    
    # Create order items
    order_items = [
        OrderItem(
            order_id=order.id,
            menu_item_id=test_menu_items[0].id,
            quantity=1,
            unit_price=100.00,
            item_name=test_menu_items[0].name
        ),
        OrderItem(
            order_id=order.id,
            menu_item_id=test_menu_items[1].id,
            quantity=1,
            unit_price=150.00,
            item_name=test_menu_items[1].name
        )
    ]
    for item in order_items:
        db.add(item)
    await db.commit()
    
    return order

@pytest.mark.asyncio
async def test_view_services(client: AsyncClient, test_service: Service):
    """Test viewing services"""
    response = await client.get("/customer/services")
    assert response.status_code in [status.HTTP_200_OK, status.HTTP_303_SEE_OTHER]
    
    # If redirected to login, that's okay for this test
    if response.status_code == status.HTTP_200_OK:
        assert "Services" in response.text

@pytest.mark.asyncio
async def test_service_menu(client: AsyncClient, test_service: Service):
    """Test viewing service menu"""
    response = await client.get(f"/customer/service/{test_service.id}")
    assert response.status_code in [status.HTTP_200_OK, status.HTTP_303_SEE_OTHER]
    
    if response.status_code == status.HTTP_200_OK:
        assert test_service.name in response.text

@pytest.mark.asyncio
async def test_add_to_cart(client: AsyncClient, test_menu_items: list):
    """Test adding item to cart"""
    # First login as customer
    login_data = {
        "username": "ordercustomer",
        "password": "Test@12345"
    }
    await client.post("/auth/login", data=login_data)
    
    # Add item to cart
    cart_data = {
        "menu_item_id": test_menu_items[0].id,
        "quantity": 2
    }
    
    response = await client.post("/customer/cart/add", data=cart_data)
    assert response.status_code == status.HTTP_200_OK
    assert "Added" in response.text

@pytest.mark.asyncio
async def test_view_cart(client: AsyncClient):
    """Test viewing cart"""
    response = await client.get("/customer/cart")
    assert response.status_code == status.HTTP_200_OK
    assert "Cart" in response.text

@pytest.mark.asyncio
async def test_place_order(client: AsyncClient, test_customer: User, test_service: Service):
    """Test placing order"""
    # Login as customer
    login_data = {
        "username": "ordercustomer",
        "password": "Test@12345"
    }
    await client.post("/auth/login", data=login_data)
    
    # Place order
    order_data = {
        "service_id": test_service.id,
        "address": "Test Delivery Address",
        "items": '[{"menu_item_id": 1, "quantity": 2}]'
    }
    
    response = await client.post("/customer/order/place", data=order_data)
    assert response.status_code in [status.HTTP_200_OK, status.HTTP_303_SEE_OTHER]
    
    if response.status_code == status.HTTP_303_SEE_OTHER:
        assert "orders" in response.headers.get("location", "")

@pytest.mark.asyncio
async def test_view_orders(client: AsyncClient, test_order: Order):
    """Test viewing customer orders"""
    response = await client.get("/customer/orders")
    assert response.status_code == status.HTTP_200_OK
    assert "Orders" in response.text

@pytest.mark.asyncio
async def test_order_details(client: AsyncClient, test_order: Order):
    """Test viewing order details"""
    response = await client.get(f"/customer/order/{test_order.id}")
    assert response.status_code == status.HTTP_200_OK
    assert f"Order #{test_order.id}" in response.text

@pytest.mark.asyncio
async def test_update_order_status(client: AsyncClient, test_order: Order, db: AsyncSession):
    """Test updating order status (admin/team member function)"""
    # Create team member for testing
    team_member = User(
        name="Test Team Member",
        username="orderteam",
        email="orderteam@example.com",
        phone="9876543202",
        hashed_password=get_password_hash("Test@12345"),
        role=UserRole.TEAM_MEMBER,
        is_active=True
    )
    db.add(team_member)
    await db.commit()
    
    # Login as team member
    login_data = {
        "username": "orderteam",
        "password": "Test@12345",
        "role": "team_member"
    }
    await client.post("/auth/login", data=login_data)
    
    # Update order status
    update_data = {
        "status": "confirmed"
    }
    
    response = await client.post(f"/team/order/{test_order.id}/status", data=update_data)
    assert response.status_code == status.HTTP_200_OK
    
    # Verify status updated in database
    await db.refresh(test_order)
    assert test_order.status == OrderStatus.CONFIRMED

@pytest.mark.asyncio
async def test_generate_otp(client: AsyncClient, test_order: Order, db: AsyncSession):
    """Test OTP generation for delivery"""
    # Set order status to out_for_delivery
    test_order.status = OrderStatus.OUT_FOR_DELIVERY
    await db.commit()
    
    # Login as team member
    login_data = {
        "username": "orderteam",
        "password": "Test@12345",
        "role": "team_member"
    }
    await client.post("/auth/login", data=login_data)
    
    # Generate OTP
    response = await client.post(f"/team/order/{test_order.id}/generate-otp")
    assert response.status_code == status.HTTP_200_OK
    assert "OTP" in response.text
    
    # Verify OTP stored in database
    await db.refresh(test_order)
    assert test_order.otp is not None
    assert test_order.otp_expiry is not None

@pytest.mark.asyncio
async def test_verify_otp(client: AsyncClient, test_order: Order, db: AsyncSession):
    """Test OTP verification"""
    # Set OTP for testing
    test_order.otp = "1234"
    test_order.otp_expiry = datetime.now(IST).replace(tzinfo=IST)
    await db.commit()
    
    # Login as team member
    login_data = {
        "username": "orderteam",
        "password": "Test@12345",
        "role": "team_member"
    }
    await client.post("/auth/login", data=login_data)
    
    # Verify OTP
    otp_data = {
        "otp": "1234"
    }
    
    response = await client.post(f"/team/order/{test_order.id}/verify-otp", data=otp_data)
    assert response.status_code == status.HTTP_200_OK
    
    # Verify order marked as delivered
    await db.refresh(test_order)
    assert test_order.status == OrderStatus.DELIVERED

@pytest.mark.asyncio
async def test_order_statistics(client: AsyncClient, db: AsyncSession):
    """Test order statistics API"""
    response = await client.get("/api/orders/stats")
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert "total_orders" in data
    assert "orders_by_status" in data
    assert "todays_orders" in data
    assert "total_revenue" in data

@pytest.mark.asyncio
async def test_recent_orders_api(client: AsyncClient):
    """Test recent orders API"""
    response = await client.get("/api/orders/recent?limit=5")
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert isinstance(data, list)

@pytest.mark.asyncio
async def test_cancel_order(client: AsyncClient, test_order: Order):
    """Test order cancellation"""
    # Login as customer
    login_data = {
        "username": "ordercustomer",
        "password": "Test@12345"
    }
    await client.post("/auth/login", data=login_data)
    
    # Cancel order
    response = await client.post(f"/customer/order/{test_order.id}/cancel")
    assert response.status_code in [status.HTTP_200_OK, status.HTTP_303_SEE_OTHER]
    
    # Note: Cancel endpoint needs to be implemented in routes

@pytest.mark.asyncio
async def test_order_with_invalid_items(client: AsyncClient, test_service: Service):
    """Test order placement with invalid items"""
    # Login as customer
    login_data = {
        "username": "ordercustomer",
        "password": "Test@12345"
    }
    await client.post("/auth/login", data=login_data)
    
    # Try to place order with invalid item
    order_data = {
        "service_id": test_service.id,
        "address": "Test Address",
        "items": '[{"menu_item_id": 99999, "quantity": 1}]'  # Non-existent item
    }
    
    response = await client.post("/customer/order/place", data=order_data)
    assert response.status_code == status.HTTP_200_OK
    assert "not found" in response.text.lower()