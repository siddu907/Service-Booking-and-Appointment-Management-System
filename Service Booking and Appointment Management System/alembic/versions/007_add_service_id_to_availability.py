from alembic import op
import sqlalchemy as sa


revision = "007_add_service_id_to_availability"
down_revision = "006_rename_duration"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [col["name"] for col in inspector.get_columns("availability")]
    if "service_id" not in columns:
        op.add_column("availability", sa.Column("service_id", sa.Integer(), nullable=True))
        op.create_foreign_key(None, "availability", "services", ["service_id"], ["id"])


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [col["name"] for col in inspector.get_columns("availability")]
    if "service_id" in columns:
        op.drop_constraint("availability_service_id_fkey", "availability", type_="foreignkey")
        op.drop_column("availability", "service_id")
