from alembic import op
import sqlalchemy as sa

revision = '004_make_phone_not_nullable'
down_revision = '003_add_user_address'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column('users', 'phone', nullable=False)


def downgrade() -> None:
    op.alter_column('users', 'phone', nullable=True)
