from alembic import op
import sqlalchemy as sa


revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('email', sa.String(), nullable=False, unique=True),
        sa.Column('full_name', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('role', sa.String(), nullable=False),
        sa.Column('phone', sa.String(), nullable=False, unique=True),
        sa.Column('address', sa.String(), nullable=False),
        sa.Column('profile_image', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')),
    )

    op.create_table(
        'services',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(), nullable=False),
        sa.Column('duration_minutes', sa.Integer(), nullable=False),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='active'),
        sa.Column('provider_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('service_image', sa.String(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')),
    )

    op.create_table(
        'availability',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('provider_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('availability_date', sa.Date(), nullable=False),
        sa.Column('start_time', sa.Time(), nullable=False),
        sa.Column('end_time', sa.Time(), nullable=False),
        sa.Column('slot_duration_minutes', sa.Integer(), nullable=False, server_default='30'),
        sa.Column('status', sa.String(), nullable=False, server_default='available'),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')),
    )

    op.create_table(
        'bookings',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('customer_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('service_id', sa.Integer(), sa.ForeignKey('services.id'), nullable=False),
        sa.Column('provider_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('appointment_date', sa.Date(), nullable=False),
        sa.Column('start_time', sa.Time(), nullable=False),
        sa.Column('end_time', sa.Time(), nullable=False),
        sa.Column('total_amount', sa.Float(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='Pending'),
        sa.Column('reminder_sent', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.UniqueConstraint('provider_id', 'appointment_date', 'start_time', 'end_time', name='uq_booking_provider_slot'),
    )
    op.create_index('ix_booking_provider_date_time', 'bookings', ['provider_id', 'appointment_date', 'start_time', 'end_time'])

    op.create_table(
        'payments',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('booking_id', sa.Integer(), sa.ForeignKey('bookings.id'), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('payment_method', sa.String(), nullable=False, server_default='Cash'),
        sa.Column('payment_date', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='Pending'),
    )

    op.create_table(
        'reviews',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('booking_id', sa.Integer(), sa.ForeignKey('bookings.id'), nullable=False),
        sa.Column('customer_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('provider_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('review', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )

    op.create_table(
        'notifications',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table('notifications')
    op.drop_table('reviews')
    op.drop_table('payments')
    op.drop_table('bookings')
    op.drop_table('availability')
    op.drop_table('services')
    op.drop_table('users')
