# Deploy backend en EC2 Ubuntu

Guia para desplegar solo `microbuses-backend` en una EC2 Ubuntu. El backend requiere PostgreSQL con PostGIS.

## 1. Paquetes base

```bash
sudo apt update
sudo apt install -y git python3.12 python3.12-venv python3-pip postgresql-client nginx
```

Si Ubuntu no trae Python 3.12 en sus repositorios, usa Python 3.11 o instala 3.12 con `deadsnakes`. El proyecto fue validado localmente con Python 3.11 y el repo declara 3.12.10 en `.python-version`.

## 2. Base de datos

Recomendado: usar RDS PostgreSQL con PostGIS para produccion. Para una prueba rapida en la misma EC2:

```bash
sudo apt install -y postgresql postgresql-contrib postgis
sudo -u postgres psql -c "CREATE USER sig_user WITH PASSWORD 'change_me';"
sudo -u postgres psql -c "CREATE DATABASE sig_microbuses OWNER sig_user;"
sudo -u postgres psql -d sig_microbuses -c "CREATE EXTENSION IF NOT EXISTS postgis;"
```

## 3. Backend

```bash
git clone <URL_DEL_REPO> microbuses-backend
cd microbuses-backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
chmod +x start.sh
nano .env
```

Completa como minimo:

```bash
DATABASE_URL=postgresql+psycopg://sig_user:change_me@localhost:5432/sig_microbuses
JWT_SECRET_KEY=<secreto_largo_aleatorio>
CORS_ALLOW_ORIGINS=https://tu-dominio.com
```

Ejecuta migraciones y seed inicial:

```bash
alembic upgrade head
python scripts/seed_admin.py
```

## 4. Correr manualmente

```bash
source .venv/bin/activate
HOST=0.0.0.0 PORT=8000 WEB_CONCURRENCY=1 ./start.sh
```

Prueba:

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/api/v1/openapi.json
```

## 5. systemd

Crear archivo:

```bash
sudo nano /etc/systemd/system/microbuses-backend.service
```

Contenido:

```ini
[Unit]
Description=SIG Microbuses Backend
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/microbuses-backend
EnvironmentFile=/home/ubuntu/microbuses-backend/.env
Environment=HOST=127.0.0.1
Environment=PORT=8000
Environment=WEB_CONCURRENCY=1
ExecStart=/home/ubuntu/microbuses-backend/start.sh
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Activar:

```bash
sudo systemctl daemon-reload
sudo systemctl enable microbuses-backend
sudo systemctl start microbuses-backend
sudo systemctl status microbuses-backend --no-pager
journalctl -u microbuses-backend -f
```

## 6. Nginx reverse proxy

Recomendado en produccion. Deja Uvicorn solo interno en `127.0.0.1:8000` y abre al publico 80/443.

```bash
sudo nano /etc/nginx/sites-available/microbuses-backend
```

```nginx
server {
    listen 80;
    server_name TU_DOMINIO_O_IP;

    client_max_body_size 20m;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/microbuses-backend /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 7. Security Group

Para Nginx:

- Entrada TCP 22 desde tu IP.
- Entrada TCP 80 desde `0.0.0.0/0`.
- Entrada TCP 443 desde `0.0.0.0/0` si usas TLS.
- No abrir 8000 al publico si Nginx esta delante.

Para prueba directa sin Nginx:

- Entrada TCP 8000 solo desde tu IP.

## 8. Docker Compose opcional

Si prefieres Docker:

```bash
cp .env.example .env
nano .env
docker compose up -d --build
docker compose logs -f backend
curl http://127.0.0.1:8000/health
```

## 9. Benchmark simple

Con el backend y la base ya levantados:

```bash
python scripts/benchmark_routing.py --requests 30 --concurrency 5
```

Para medir el endpoint peatonal sin DB:

```bash
python scripts/benchmark_routing.py --preset walking --requests 20 --concurrency 4
```
