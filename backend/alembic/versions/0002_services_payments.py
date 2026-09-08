from alembic import op
import sqlalchemy as sa

revision='0002_services_payments'
down_revision='0001_initial'
branch_labels=None
depends_on=None

def upgrade():
    op.create_table(
        'services',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('specialty_id', sa.Integer(), sa.ForeignKey('specialties.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('name', sa.String(160), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('price', sa.Integer(), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.UniqueConstraint('code'),
    )
    op.create_index('ix_services_specialty_id', 'services', ['specialty_id'])
    op.create_index('ix_services_code', 'services', ['code'], unique=True)
    op.add_column('appointments', sa.Column('service_id', sa.Integer(), nullable=True))
    op.create_foreign_key('appointments_service_id_fkey', 'appointments', 'services', ['service_id'], ['id'], ondelete='RESTRICT')
    op.create_index('ix_appointments_service_id', 'appointments', ['service_id'])
    op.drop_constraint('uq_doctor_slot', 'appointments', type_='unique')
    op.create_index(
        'uq_doctor_slot_active', 'appointments',
        ['doctor_id', 'appointment_date', 'start_time'], unique=True,
        postgresql_where=sa.text("status NOT IN ('CANCELLED', 'NO_SHOW')")
    )
    op.create_table(
        'payments',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('appointment_id', sa.Integer(), sa.ForeignKey('appointments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('service_id', sa.Integer(), sa.ForeignKey('services.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('method', sa.String(20), nullable=False),
        sa.Column('status', sa.String(30), nullable=False),
        sa.Column('reference', sa.String(80), nullable=False),
        sa.Column('qr_payload', sa.Text(), nullable=True),
        sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('appointment_id'),
        sa.UniqueConstraint('reference'),
    )
    op.create_index('ix_payments_appointment_id', 'payments', ['appointment_id'])
    op.create_index('ix_payments_reference', 'payments', ['reference'], unique=True)

def downgrade():
    op.drop_index('ix_payments_reference', table_name='payments')
    op.drop_index('ix_payments_appointment_id', table_name='payments')
    op.drop_table('payments')
    op.drop_index('uq_doctor_slot_active', table_name='appointments')
    op.create_unique_constraint('uq_doctor_slot', 'appointments', ['doctor_id','appointment_date','start_time'])
    op.drop_index('ix_appointments_service_id', table_name='appointments')
    op.drop_constraint('appointments_service_id_fkey', 'appointments', type_='foreignkey')
    op.drop_column('appointments', 'service_id')
    op.drop_index('ix_services_code', table_name='services')
    op.drop_index('ix_services_specialty_id', table_name='services')
    op.drop_table('services')
