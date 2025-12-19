"""Initial migration

Revision ID: 001_initial
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=100), nullable=False),
        sa.Column('phone', sa.String(length=20), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('role', sa.Enum('CUSTOMER', 'TEAM_MEMBER', 'ADMIN', name='userrole'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_verified', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_users'))
    )
    
    # Create indexes for users
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_phone'), 'users', ['phone'], unique=True)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.create_index('idx_user_role_active', 'users', ['role', 'is_active'], unique=False)
    
    # Create services table
    op.create_table('services',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('image_url', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_services')),
        sa.UniqueConstraint('name', name=op.f('uq_services_name'))
    )
    
    op.create_index(op.f('ix_services_id'), 'services', ['id'], unique=False)
    op.create_index(op.f('ix_services_name'), 'services', ['name'], unique=True)
    
    # Create menu_items table
    op.create_table('menu_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('service_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('image_url', sa.String(length=255), nullable=True),
        sa.Column('is_available', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['service_id'], ['services.id'], name=op.f('fk_menu_items_service_id_services'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_menu_items'))
    )
    
    op.create_index(op.f('ix_menu_items_id'), 'menu_items', ['id'], unique=False)
    op.create_index(op.f('ix_menu_items_name'), 'menu_items', ['name'], unique=False)
    op.create_index(op.f('ix_menu_items_service_id'), 'menu_items', ['service_id'], unique=False)
    
    # Create orders table
    op.create_table('orders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('service_id', sa.Integer(), nullable=False),
        sa.Column('assigned_to', sa.Integer(), nullable=True),
        sa.Column('total_amount', sa.Float(), nullable=False),
        sa.Column('address', sa.Text(), nullable=False),
        sa.Column('special_instructions', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('PENDING', 'CONFIRMED', 'PREPARING', 'OUT_FOR_DELIVERY', 'DELIVERED', 'CANCELLED', name='orderstatus'), nullable=False),
        sa.Column('otp', sa.String(length=4), nullable=True),
        sa.Column('otp_expiry', sa.DateTime(timezone=True), nullable=True),
        sa.Column('otp_attempts', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('confirmed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('prepared_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('out_for_delivery_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['assigned_to'], ['users.id'], name=op.f('fk_orders_assigned_to_users'), ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['customer_id'], ['users.id'], name=op.f('fk_orders_customer_id_users'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['service_id'], ['services.id'], name=op.f('fk_orders_service_id_services'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_orders'))
    )
    
    op.create_index(op.f('ix_orders_assigned_to'), 'orders', ['assigned_to'], unique=False)
    op.create_index(op.f('ix_orders_customer_id'), 'orders', ['customer_id'], unique=False)
    op.create_index(op.f('ix_orders_id'), 'orders', ['id'], unique=False)
    op.create_index(op.f('ix_orders_service_id'), 'orders', ['service_id'], unique=False)
    
    # Create order_items table
    op.create_table('order_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('menu_item_id', sa.Integer(), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('unit_price', sa.Float(), nullable=False),
        sa.Column('item_name', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['menu_item_id'], ['menu_items.id'], name=op.f('fk_order_items_menu_item_id_menu_items'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], name=op.f('fk_order_items_order_id_orders'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_order_items'))
    )
    
    op.create_index(op.f('ix_order_items_id'), 'order_items', ['id'], unique=False)
    op.create_index(op.f('ix_order_items_menu_item_id'), 'order_items', ['menu_item_id'], unique=False)
    op.create_index(op.f('ix_order_items_order_id'), 'order_items', ['order_id'], unique=False)
    
    # Create team_member_plans table
    op.create_table('team_member_plans',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('admin_id', sa.Integer(), nullable=False),
        sa.Column('team_member_id', sa.Integer(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('image_url', sa.String(length=255), nullable=True),
        sa.Column('is_read', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['admin_id'], ['users.id'], name=op.f('fk_team_member_plans_admin_id_users'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['team_member_id'], ['users.id'], name=op.f('fk_team_member_plans_team_member_id_users'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_team_member_plans'))
    )
    
    op.create_index(op.f('ix_team_member_plans_admin_id'), 'team_member_plans', ['admin_id'], unique=False)
    op.create_index(op.f('ix_team_member_plans_id'), 'team_member_plans', ['id'], unique=False)
    op.create_index(op.f('ix_team_member_plans_team_member_id'), 'team_member_plans', ['team_member_id'], unique=False)
    
    # Create user_sessions table
    op.create_table('user_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('login_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('logout_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_user_sessions_user_id_users'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_user_sessions'))
    )
    
    op.create_index(op.f('ix_user_sessions_date'), 'user_sessions', ['date'], unique=False)
    op.create_index(op.f('ix_user_sessions_id'), 'user_sessions', ['id'], unique=False)
    op.create_index(op.f('ix_user_sessions_user_id'), 'user_sessions', ['user_id'], unique=False)
    op.create_index('idx_session_date', 'user_sessions', ['date'], unique=False)
    op.create_index('idx_session_user_date', 'user_sessions', ['user_id', 'date'], unique=False)
    
    # Insert initial data
    op.execute("""
        INSERT INTO users (name, username, email, phone, hashed_password, role, is_active, is_verified, created_at, updated_at)
        VALUES (
            'Admin User',
            'admin',
            'admin@bitemebuddy.com',
            '9876543210',
            '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', -- password: 'admin123'
            'ADMIN',
            true,
            true,
            NOW(),
            NOW()
        )
    """)

def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('user_sessions')
    op.drop_table('team_member_plans')
    op.drop_table('order_items')
    op.drop_table('orders')
    op.drop_table('menu_items')
    op.drop_table('services')
    op.drop_table('users')
    
    # Drop enums
    op.execute("DROP TYPE IF EXISTS orderstatus")
    op.execute("DROP TYPE IF EXISTS userrole")
