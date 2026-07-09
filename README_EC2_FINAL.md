# SIG Microbuses Backend - EC2 final

## A. Tecnologia del backend

- Python 3.12
- FastAPI
- Uvicorn
- SQLAlchemy 2
- Alembic
- PostgreSQL/PostGIS externo en Neon
- NetworkX/OSMnx para routing y red peatonal
- Nginx como reverse proxy
- systemd para proceso persistente

## B. Ruta del proyecto en EC2

```bash
/home/ubuntu/microbuses-backend
```

## C. Activar venv

```bash
cd /home/ubuntu/microbuses-backend
source .venv/bin/activate
```

## D. Instalar dependencias

```bash
cd /home/ubuntu/microbuses-backend
source .venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

## E. Ruta del .env

```bash
/home/ubuntu/microbuses-backend/.env
```

Permisos esperados:

```bash
chmod 600 /home/ubuntu/microbuses-backend/.env
chown ubuntu:ubuntu /home/ubuntu/microbuses-backend/.env
```

## F. Correr manualmente

```bash
cd /home/ubuntu/microbuses-backend
source .venv/bin/activate
HOST=127.0.0.1 PORT=8000 WEB_CONCURRENCY=1 ./start.sh
```

Alternativa:

```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1
```

## G. Servicio systemd

Nombre:

```bash
microbuses-backend
```

Archivo:

```bash
/etc/systemd/system/microbuses-backend.service
```

## H. Iniciar backend

```bash
sudo systemctl start microbuses-backend
```

## I. Detener backend

```bash
sudo systemctl stop microbuses-backend
```

## J. Reiniciar backend

```bash
sudo systemctl restart microbuses-backend
```

## K. Ver logs

```bash
journalctl -u microbuses-backend -f
```

Ultimas lineas:

```bash
journalctl -u microbuses-backend -n 100 --no-pager
```

Verificar precarga del grafo peatonal:

```bash
journalctl -u microbuses-backend -n 50 --no-pager | grep "Walking graph preloaded"
```

## L. Configuracion Nginx

Archivo:

```bash
/etc/nginx/sites-available/microbuses-backend
```

Symlink activo:

```bash
/etc/nginx/sites-enabled/microbuses-backend
```

Validar y reiniciar:

```bash
sudo nginx -t
sudo systemctl restart nginx
```

## M. URL publica

```bash
http://sig.leonardoserrate.xyz
```

## N. Probar /health

Interno Uvicorn:

```bash
curl http://127.0.0.1:8000/health
```

Via Nginx local:

```bash
curl http://127.0.0.1/health
```

Publico por IP:

```bash
curl http://100.49.168.60/health
```

Publico por dominio:

```bash
curl http://sig.leonardoserrate.xyz/health
```

## O. Probar routing

Endpoint:

```bash
POST /api/v1/routing/calculate
```

Comando:

```bash
curl -X POST http://sig.leonardoserrate.xyz/api/v1/routing/calculate \
  -H "Content-Type: application/json" \
  -d '{"origin":{"lat":-17.7833,"lng":-63.1821},"destination":{"lat":-17.7900,"lng":-63.1750},"max_transfers":3,"boarding_mode":"ANYWHERE_ON_ROUTE"}'
```

Benchmark:

```bash
cd /home/ubuntu/microbuses-backend
source .venv/bin/activate
python scripts/benchmark_routing.py --requests 10 --concurrency 2 --timeout 120
python scripts/benchmark_routing.py --preset walking --requests 10 --concurrency 2 --timeout 120
```

## P. Si falla Neon

Revisar:

```bash
cd /home/ubuntu/microbuses-backend
source .venv/bin/activate
python - <<'PY'
from sqlalchemy import create_engine, text
from app.core.settings import get_settings
engine = create_engine(get_settings().database_url, pool_pre_ping=True)
with engine.connect() as conn:
    print(conn.execute(text("SELECT 1")).scalar_one())
PY
```

Confirmar en `.env`:

- `DATABASE_URL` apunta a Neon, no a localhost.
- `sslmode=require` esta presente.
- Las credenciales son las correctas.

## Q. Si falla el grafo

Revisar archivo:

```bash
ls -lh /home/ubuntu/microbuses-backend/data/walking/santa_cruz_walk.graphml
ls -lh /home/ubuntu/microbuses-backend/data/walking/santa_cruz_walk.pkl
```

Revisar variable:

```bash
cd /home/ubuntu/microbuses-backend
source .venv/bin/activate
python - <<'PY'
from pathlib import Path
from app.core.settings import get_settings
path = Path(get_settings().walking_graph_path)
print(path)
print(path.exists())
PY
```

## R. Antes de la defensa

```bash
sudo systemctl status microbuses-backend --no-pager
sudo systemctl status nginx --no-pager
curl http://sig.leonardoserrate.xyz/health
curl http://sig.leonardoserrate.xyz/api/v1/openapi.json
```

El backend precarga el grafo peatonal durante el startup. Aun asi, una llamada a routing antes de iniciar la demo ayuda a validar el flujo completo y dejar caches de consulta recientes:

```bash
curl -X POST http://sig.leonardoserrate.xyz/api/v1/routing/calculate \
  -H "Content-Type: application/json" \
  -d '{"origin":{"lat":-17.7833,"lng":-63.1821},"destination":{"lat":-17.7900,"lng":-63.1750},"max_transfers":3,"boarding_mode":"ANYWHERE_ON_ROUTE"}'
```

Notas:

- El servicio usa 1 worker para no duplicar memoria del grafo.
- El grafo peatonal se precarga al iniciar FastAPI; revisar logs con `Walking graph preloaded`.
- Uvicorn escucha solo en `127.0.0.1:8000`.
- Nginx publica el backend por puerto 80.
- La base de datos vive en Neon, no en la EC2.
- `scripts/seed_admin.py` no se ejecuto porque el `.env` subido no incluye `SUPER_ADMIN_EMAIL` ni `SUPER_ADMIN_PASSWORD`; no usar credenciales por defecto sin confirmacion.
