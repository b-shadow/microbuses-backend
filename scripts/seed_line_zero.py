import sys
from pathlib import Path

from sqlalchemy import select

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.core.dependencies import SessionLocal
from app.modules.lines.models import Linea


def main() -> None:
    with SessionLocal() as db:
        row = db.scalar(select(Linea).where(Linea.nombre_linea == '0'))
        if row:
            row.color_linea = '#64748B'
            row.is_active = True
            db.add(row)
            db.commit()
            print('[seed_line_zero] Updated linea 0')
            return

        line = Linea(
            nombre_linea='0',
            color_linea='#64748B',
            is_active=True,
        )
        db.add(line)
        db.commit()
        print('[seed_line_zero] Created linea 0')


if __name__ == '__main__':
    main()
