from alembic import op
import sqlalchemy as sa

revision = '003_add_user_address'
down_revision = '002_add_coupons'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('address', sa.String(), nullable=False, server_default=''))
    op.alter_column('users', 'address', server_default=None)
    op.create_unique_constraint('uq_users_phone', 'users', ['phone'])


def downgrade() -> None:
    op.drop_constraint('uq_users_phone', 'users', type_='unique')
    op.drop_column('users', 'address')
