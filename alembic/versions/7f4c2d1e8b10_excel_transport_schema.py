"""excel_transport_schema

Revision ID: 7f4c2d1e8b10
Revises: dd9b7af5d8b3
Create Date: 2026-06-02 00:00:00.000000

"""

from typing import Sequence, Union
from uuid import UUID

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '7f4c2d1e8b10'
down_revision: Union[str, None] = 'dd9b7af5d8b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _copy_lines_to_lineas(connection) -> dict[UUID, int]:
    old_lines = connection.execute(
        sa.text(
            """
            SELECT id, code, color, is_active, created_at
            FROM lines
            ORDER BY code
            """
        )
    ).mappings().all()
    mapping: dict[UUID, int] = {}
    for row in old_lines:
        new_id = connection.execute(
            sa.text(
                """
                INSERT INTO lineas (nombre_linea, color_linea, imagen_micro, is_active, fecha_creacion)
                VALUES (:nombre_linea, :color_linea, NULL, :is_active, COALESCE(:fecha_creacion, now()))
                RETURNING id_linea
                """
            ),
            {
                'nombre_linea': row['code'],
                'color_linea': row['color'],
                'is_active': row['is_active'],
                'fecha_creacion': row['created_at'],
            },
        ).scalar_one()
        mapping[row['id']] = int(new_id)
    return mapping


def _migrate_bus_and_trip_line_ids(connection, line_mapping: dict[UUID, int]) -> None:
    buses = connection.execute(
        sa.text(
            """
            SELECT id, current_line_id
            FROM buses
            """
        )
    ).mappings().all()
    for row in buses:
        new_line_id = line_mapping.get(row['current_line_id'])
        if new_line_id is not None:
            connection.execute(
                sa.text(
                    """
                    UPDATE buses
                    SET current_line_id_new = :new_line_id
                    WHERE id = :bus_id
                    """
                ),
                {'new_line_id': new_line_id, 'bus_id': row['id']},
            )

    trips = connection.execute(
        sa.text(
            """
            SELECT id, line_id
            FROM active_trips
            """
        )
    ).mappings().all()
    for row in trips:
        new_line_id = line_mapping.get(row['line_id'])
        if new_line_id is not None:
            connection.execute(
                sa.text(
                    """
                    UPDATE active_trips
                    SET line_id_new = :new_line_id
                    WHERE id = :trip_id
                    """
                ),
                {'new_line_id': new_line_id, 'trip_id': row['id']},
            )


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS postgis')

    op.create_table(
        'lineas',
        sa.Column('id_linea', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('nombre_linea', sa.String(length=50), nullable=False),
        sa.Column('color_linea', sa.String(length=20), nullable=False),
        sa.Column('imagen_micro', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('fecha_creacion', sa.DateTime(timezone=False), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('nombre_linea', name=op.f('uq_lineas_nombre_linea')),
    )
    op.create_index(op.f('ix_lineas_nombre_linea'), 'lineas', ['nombre_linea'], unique=True)

    op.create_table(
        'puntos',
        sa.Column('id_punto', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('latitud', sa.Numeric(10, 6), nullable=False),
        sa.Column('longitud', sa.Numeric(10, 6), nullable=False),
        sa.Column('descripcion', sa.String(length=120), nullable=False),
        sa.Column('stop', sa.String(length=1), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('fecha_creacion', sa.DateTime(timezone=False), server_default=sa.text('now()'), nullable=False),
    )

    op.create_table(
        'linea_ruta',
        sa.Column('id_linea_ruta', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('id_linea', sa.Integer(), nullable=False),
        sa.Column('id_ruta', sa.Integer(), nullable=False),
        sa.Column('descripcion', sa.String(length=255), nullable=False),
        sa.Column('distancia', sa.Numeric(10, 2), nullable=True),
        sa.Column('tiempo', sa.Numeric(10, 2), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('fecha_creacion', sa.DateTime(timezone=False), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['id_linea'], ['lineas.id_linea'], name=op.f('fk_linea_ruta_id_linea_lineas')),
    )
    op.create_index(op.f('ix_linea_ruta_id_linea'), 'linea_ruta', ['id_linea'], unique=False)

    op.create_table(
        'lineas_puntos',
        sa.Column('id_linea_punto', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('id_linea_ruta', sa.Integer(), nullable=False),
        sa.Column('id_punto', sa.Integer(), nullable=False),
        sa.Column('id_punto_dest', sa.Integer(), nullable=False),
        sa.Column('orden', sa.Integer(), nullable=False),
        sa.Column('distancia', sa.Numeric(10, 2), nullable=True),
        sa.Column('tiempo', sa.Numeric(10, 2), nullable=True),
        sa.Column('fecha_creacion', sa.DateTime(timezone=False), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['id_linea_ruta'], ['linea_ruta.id_linea_ruta'], name=op.f('fk_lineas_puntos_id_linea_ruta_linea_ruta')),
        sa.ForeignKeyConstraint(['id_punto'], ['puntos.id_punto'], name=op.f('fk_lineas_puntos_id_punto_puntos')),
        sa.ForeignKeyConstraint(['id_punto_dest'], ['puntos.id_punto'], name=op.f('fk_lineas_puntos_id_punto_dest_puntos')),
        sa.UniqueConstraint('id_linea_ruta', 'orden', name='uq_lineas_puntos_linea_ruta_orden'),
    )
    op.create_index(op.f('ix_lineas_puntos_id_linea_ruta'), 'lineas_puntos', ['id_linea_ruta'], unique=False)

    op.create_table(
        'puntos_trasbordos',
        sa.Column('id_trasbordo', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('id_punto', sa.Integer(), nullable=False),
        sa.Column('id_linea_origen', sa.Integer(), nullable=False),
        sa.Column('id_linea_destino', sa.Integer(), nullable=False),
        sa.Column('penalizacion_min', sa.Integer(), nullable=False, server_default=sa.text('5')),
        sa.ForeignKeyConstraint(['id_punto'], ['puntos.id_punto'], name=op.f('fk_puntos_trasbordos_id_punto_puntos')),
        sa.ForeignKeyConstraint(['id_linea_origen'], ['lineas.id_linea'], name=op.f('fk_puntos_trasbordos_id_linea_origen_lineas')),
        sa.ForeignKeyConstraint(['id_linea_destino'], ['lineas.id_linea'], name=op.f('fk_puntos_trasbordos_id_linea_destino_lineas')),
    )
    op.create_index(op.f('ix_puntos_trasbordos_id_punto'), 'puntos_trasbordos', ['id_punto'], unique=False)
    op.create_index(op.f('ix_puntos_trasbordos_id_linea_origen'), 'puntos_trasbordos', ['id_linea_origen'], unique=False)
    op.create_index(op.f('ix_puntos_trasbordos_id_linea_destino'), 'puntos_trasbordos', ['id_linea_destino'], unique=False)

    connection = op.get_bind()
    line_mapping = _copy_lines_to_lineas(connection)

    op.add_column('buses', sa.Column('current_line_id_new', sa.Integer(), nullable=True))
    op.add_column('active_trips', sa.Column('line_id_new', sa.Integer(), nullable=True))
    op.add_column('active_trips', sa.Column('route_id_new', sa.Integer(), nullable=True))

    _migrate_bus_and_trip_line_ids(connection, line_mapping)

    op.drop_constraint('fk_buses_current_line_id_lines', 'buses', type_='foreignkey')
    op.drop_index('ix_buses_current_line_id', table_name='buses')
    op.drop_column('buses', 'current_line_id')
    op.alter_column('buses', 'current_line_id_new', new_column_name='current_line_id', nullable=False)
    op.create_index(op.f('ix_buses_current_line_id'), 'buses', ['current_line_id'], unique=False)
    op.create_foreign_key(op.f('fk_buses_current_line_id_lineas'), 'buses', 'lineas', ['current_line_id'], ['id_linea'])

    op.drop_constraint('fk_active_trips_line_id_lines', 'active_trips', type_='foreignkey')
    op.drop_constraint('fk_active_trips_route_id_routes', 'active_trips', type_='foreignkey')
    op.drop_index('ix_active_trips_line_id', table_name='active_trips')
    op.drop_column('active_trips', 'line_id')
    op.drop_column('active_trips', 'route_id')
    op.alter_column('active_trips', 'line_id_new', new_column_name='line_id', nullable=False)
    op.alter_column('active_trips', 'route_id_new', new_column_name='route_id', nullable=True)
    op.create_index(op.f('ix_active_trips_line_id'), 'active_trips', ['line_id'], unique=False)
    op.create_foreign_key(op.f('fk_active_trips_line_id_lineas'), 'active_trips', 'lineas', ['line_id'], ['id_linea'])
    op.create_foreign_key(op.f('fk_active_trips_route_id_linea_ruta'), 'active_trips', 'linea_ruta', ['route_id'], ['id_linea_ruta'])


def downgrade() -> None:
    op.drop_constraint(op.f('fk_active_trips_route_id_linea_ruta'), 'active_trips', type_='foreignkey')
    op.drop_constraint(op.f('fk_active_trips_line_id_lineas'), 'active_trips', type_='foreignkey')
    op.drop_index(op.f('ix_active_trips_line_id'), table_name='active_trips')
    op.add_column('active_trips', sa.Column('route_id_old', sa.UUID(), nullable=True))
    op.add_column('active_trips', sa.Column('line_id_old', sa.UUID(), nullable=False))
    op.drop_column('active_trips', 'route_id')
    op.drop_column('active_trips', 'line_id')
    op.alter_column('active_trips', 'line_id_old', new_column_name='line_id')
    op.alter_column('active_trips', 'route_id_old', new_column_name='route_id')
    op.create_index(op.f('ix_active_trips_line_id'), 'active_trips', ['line_id'], unique=False)
    op.create_foreign_key(op.f('fk_active_trips_line_id_lines'), 'active_trips', 'lines', ['line_id'], ['id'])
    op.create_foreign_key(op.f('fk_active_trips_route_id_routes'), 'active_trips', 'routes', ['route_id'], ['id'])

    op.drop_constraint(op.f('fk_buses_current_line_id_lineas'), 'buses', type_='foreignkey')
    op.drop_index(op.f('ix_buses_current_line_id'), table_name='buses')
    op.add_column('buses', sa.Column('current_line_id_old', sa.UUID(), nullable=False))
    op.drop_column('buses', 'current_line_id')
    op.alter_column('buses', 'current_line_id_old', new_column_name='current_line_id')
    op.create_index(op.f('ix_buses_current_line_id'), 'buses', ['current_line_id'], unique=False)
    op.create_foreign_key(op.f('fk_buses_current_line_id_lines'), 'buses', 'lines', ['current_line_id'], ['id'])

    op.drop_index(op.f('ix_puntos_trasbordos_id_linea_destino'), table_name='puntos_trasbordos')
    op.drop_index(op.f('ix_puntos_trasbordos_id_linea_origen'), table_name='puntos_trasbordos')
    op.drop_index(op.f('ix_puntos_trasbordos_id_punto'), table_name='puntos_trasbordos')
    op.drop_table('puntos_trasbordos')
    op.drop_index(op.f('ix_lineas_puntos_id_linea_ruta'), table_name='lineas_puntos')
    op.drop_table('lineas_puntos')
    op.drop_index(op.f('ix_linea_ruta_id_linea'), table_name='linea_ruta')
    op.drop_table('linea_ruta')
    op.drop_table('puntos')
    op.drop_index(op.f('ix_lineas_nombre_linea'), table_name='lineas')
    op.drop_table('lineas')
