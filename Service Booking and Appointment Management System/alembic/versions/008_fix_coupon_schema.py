from alembic import op
import sqlalchemy as sa


revision = "008_fix_coupon_schema"
down_revision = "007_add_service_id_to_availability"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    coupon_columns = [col["name"] for col in inspector.get_columns("coupons")]

    if "discount_amount" in coupon_columns:
        op.drop_column("coupons", "discount_amount")


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    coupon_columns = [col["name"] for col in inspector.get_columns("coupons")]

    if "discount_amount" not in coupon_columns:
        op.add_column("coupons", sa.Column("discount_amount", sa.Float(), nullable=True, server_default='0'))
