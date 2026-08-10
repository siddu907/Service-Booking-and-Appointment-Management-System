from alembic import op
import sqlalchemy as sa


revision = '002_add_coupons'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'coupons',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('code', sa.String(), nullable=False, unique=True),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('discount_percent', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('usage_limit', sa.Integer(), nullable=True),
        sa.Column('used_count', sa.Integer(), nullable=False, server_default='0'),
    )
    op.add_column('bookings', sa.Column('original_amount', sa.Float(), nullable=False, server_default='0'))
    op.add_column('bookings', sa.Column('discount_amount', sa.Float(), nullable=False, server_default='0'))
    op.add_column('bookings', sa.Column('coupon_code', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('bookings', 'coupon_code')
    op.drop_column('bookings', 'discount_amount')
    op.drop_column('bookings', 'original_amount')
    op.drop_table('coupons')
