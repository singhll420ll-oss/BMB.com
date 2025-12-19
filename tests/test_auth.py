"""
Authentication tests
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import status

from models.user import User, UserRole
from core.security import get_password_hash

@pytest.mark.asyncio
async def test_home_page(client: AsyncClient):
    """Test home page loads successfully"""
    response = await client.get("/")
    assert response.status_code == status.HTTP_200_OK
    assert "Bite Me Buddy" in response.text

@pytest.mark.asyncio
async def test_customer_registration(client: AsyncClient, db: AsyncSession):
    """Test customer registration"""
    registration_data = {
        "name": "Test Customer",
        "username": "testcustomer",
        "email": "test@example.com",
        "phone": "9876543210",
        "password": "Test@12345",
        "address": "Test Address"
    }
    
    response = await client.post("/auth/register", data=registration_data)
    assert response.status_code in [status.HTTP_200_OK, status.HTTP_303_SEE_OTHER]
    
    # Check user created in database
    user = await db.get(User, 1)
    assert user is not None
    assert user.username == "testcustomer"
    assert user.role == UserRole.CUSTOMER

@pytest.mark.asyncio
async def test_customer_login(client: AsyncClient, db: AsyncSession):
    """Test customer login"""
    # Create test user
    user = User(
        name="Test User",
        username="testuser",
        email="testuser@example.com",
        phone="9876543211",
        hashed_password=get_password_hash("Test@12345"),
        role=UserRole.CUSTOMER,
        is_active=True
    )
    db.add(user)
    await db.commit()
    
    # Test login
    login_data = {
        "username": "testuser",
        "password": "Test@12345",
        "role": "customer"
    }
    
    response = await client.post("/auth/login", data=login_data)
    assert response.status_code == status.HTTP_303_SEE_OTHER
    assert "customer/dashboard" in response.headers.get("location", "")

@pytest.mark.asyncio
async def test_team_member_login(client: AsyncClient, db: AsyncSession):
    """Test team member login"""
    # Create test team member
    team_member = User(
        name="Test Team Member",
        username="testteam",
        email="team@example.com",
        phone="9876543212",
        hashed_password=get_password_hash("Test@12345"),
        role=UserRole.TEAM_MEMBER,
        is_active=True
    )
    db.add(team_member)
    await db.commit()
    
    # Test login
    login_data = {
        "username": "testteam",
        "password": "Test@12345",
        "role": "team_member"
    }
    
    response = await client.post("/auth/login", data=login_data)
    assert response.status_code == status.HTTP_303_SEE_OTHER
    assert "team/dashboard" in response.headers.get("location", "")

@pytest.mark.asyncio
async def test_admin_login_via_secret(client: AsyncClient, db: AsyncSession):
    """Test admin login via secret clock"""
    # Create test admin
    admin = User(
        name="Test Admin",
        username="testadmin",
        email="admin@example.com",
        phone="9876543213",
        hashed_password=get_password_hash("Test@12345"),
        role=UserRole.ADMIN,
        is_active=True
    )
    db.add(admin)
    await db.commit()
    
    # Access admin login page
    response = await client.get("/auth/admin-login")
    assert response.status_code == status.HTTP_200_OK
    assert "Admin Login" in response.text

@pytest.mark.asyncio
async def test_invalid_login(client: AsyncClient, db: AsyncSession):
    """Test invalid login credentials"""
    login_data = {
        "username": "nonexistent",
        "password": "wrongpassword",
        "role": "customer"
    }
    
    response = await client.post("/auth/login", data=login_data)
    assert response.status_code == status.HTTP_200_OK
    assert "Invalid username or password" in response.text

@pytest.mark.asyncio
async def test_logout(client: AsyncClient, db: AsyncSession):
    """Test logout functionality"""
    # First login
    user = User(
        name="Test User",
        username="logouttest",
        email="logout@example.com",
        phone="9876543214",
        hashed_password=get_password_hash("Test@12345"),
        role=UserRole.CUSTOMER,
        is_active=True
    )
    db.add(user)
    await db.commit()
    
    login_data = {
        "username": "logouttest",
        "password": "Test@12345"
    }
    
    response = await client.post("/auth/login", data=login_data)
    assert response.status_code == status.HTTP_303_SEE_OTHER
    
    # Then logout
    response = await client.get("/auth/logout")
    assert response.status_code == status.HTTP_303_SEE_OTHER
    assert response.headers.get("location") == "/"

@pytest.mark.asyncio
async def test_duplicate_registration(client: AsyncClient, db: AsyncSession):
    """Test duplicate user registration"""
    # Create initial user
    user = User(
        name="Existing User",
        username="existing",
        email="existing@example.com",
        phone="9876543215",
        hashed_password=get_password_hash("Test@12345"),
        role=UserRole.CUSTOMER,
        is_active=True
    )
    db.add(user)
    await db.commit()
    
    # Try to register with same username
    registration_data = {
        "name": "New User",
        "username": "existing",  # Duplicate username
        "email": "new@example.com",
        "phone": "9876543216",
        "password": "Test@12345",
        "address": "Test Address"
    }
    
    response = await client.post("/auth/register", data=registration_data)
    assert response.status_code == status.HTTP_200_OK
    assert "already exists" in response.text

@pytest.mark.asyncio
async def test_password_validation(client: AsyncClient):
    """Test password validation during registration"""
    registration_data = {
        "name": "Test User",
        "username": "testuser2",
        "email": "test2@example.com",
        "phone": "9876543217",
        "password": "123",  # Too short
        "address": "Test Address"
    }
    
    response = await client.post("/auth/register", data=registration_data)
    assert response.status_code == status.HTTP_200_OK
    assert "Password must be at least 8 characters" in response.text

@pytest.mark.asyncio
async def test_phone_validation(client: AsyncClient):
    """Test phone number validation"""
    registration_data = {
        "name": "Test User",
        "username": "testuser3",
        "email": "test3@example.com",
        "phone": "12345",  # Invalid phone
        "password": "Test@12345",
        "address": "Test Address"
    }
    
    response = await client.post("/auth/register", data=registration_data)
    assert response.status_code == status.HTTP_200_OK
    assert "Invalid Indian mobile number" in response.text

@pytest.mark.asyncio
async def test_email_validation(client: AsyncClient):
    """Test email validation"""
    registration_data = {
        "name": "Test User",
        "username": "testuser4",
        "email": "invalid-email",  # Invalid email
        "phone": "9876543218",
        "password": "Test@12345",
        "address": "Test Address"
    }
    
    response = await client.post("/auth/register", data=registration_data)
    assert response.status_code == status.HTTP_200_OK
    assert "valid email address" in response.text
