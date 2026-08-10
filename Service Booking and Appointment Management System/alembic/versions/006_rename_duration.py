"""rename duration_minutes to duration (string)

Revision ID: 006_rename_duration_minutes_to_duration
Revises: 005_rename_service_image
Create Date: 2026-08-07 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = '006_rename_duration'
down_revision = '005_rename_service_image'
branch_labels = None
depends_on = None


def upgrade():
    # Add new duration column
    op.add_column('services', sa.Column('duration', sa.String(), nullable=True))

    bind = op.get_bind()
    results = bind.execute(text('SELECT id, duration_minutes FROM services'))

    from app.utils.helpers import format_minutes_to_duration

    for row in results:
        sid = row[0]
        dm = row[1]
        if dm is not None:
            dur = format_minutes_to_duration(dm)
            bind.execute(text('UPDATE services SET duration = :d WHERE id = :id'), {'d': dur, 'id': sid})

    op.alter_column('services', 'duration', nullable=False)

    with op.batch_alter_table('services') as batch_op:
        batch_op.drop_column('duration_minutes')


def downgrade():
    op.add_column('services', sa.Column('duration_minutes', sa.Integer(), nullable=True))

    bind = op.get_bind()
    results = bind.execute(text('SELECT id, duration FROM services'))

    from app.utils.helpers import parse_duration_to_minutes

    for row in results:
        sid = row[0]
        dur = row[1]
        if dur is not None:
            try:
                dm = parse_duration_to_minutes(dur)
                bind.execute(text('UPDATE services SET duration_minutes = :dm WHERE id = :id'), {'dm': dm, 'id': sid})
            except Exception:
                pass

    op.alter_column('services', 'duration_minutes', nullable=False)

    with op.batch_alter_table('services') as batch_op:
        batch_op.drop_column('duration')
