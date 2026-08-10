from alembic import op

revision = '005_rename_service_image'
down_revision = '004_make_phone_not_nullable'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column('services', 'image_url', new_column_name='service_image')



