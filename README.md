# Control de Stock y Estado de Pizzas (Festival)

MVP para operar un puesto de pizzas con escaneo rapido por QR/codigo.

## Stack
- Django + DRF
- PostgreSQL (objetivo produccion)
- Generacion de etiquetas QR en PDF (ReportLab + qrcode)

## Pantallas
- `/login`: acceso por usuario + PIN con sesion expirable
- `/branding/select`: seleccion de servicio (Festival/Burgers). Solo admin puede alternar libremente.
- `/kitchen`: escaneo en modo cocina (`PREPARACION -> LISTA`)
- `/sales`: escaneo en modo ventas (`LISTA -> VENDIDA`)
- `/dashboard`: conteos en tiempo real + facturacion vendida + ultimos eventos + deshacer admin
- `/batches`: generacion de lotes del dia y descarga de etiquetas PDF
- `/admin-ops`: menu admin protegido por PIN para `MERMA`, `CANCELADA` y deshacer

## API principal
- `POST /api/scan`
- `POST /api/batches/generate`
- `GET /api/batches/<batch_code>/labels.pdf`
- `GET /api/dashboard`
- `POST /api/admin/status`
- `POST /api/admin/undo`

## Arranque rapido
1. Crear entorno virtual e instalar dependencias:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```
2. Migrar DB:
   ```powershell
   python manage.py migrate
   ```
3. Configurar variables en `.env` (PIN, secret, DB, hosts):
   ```powershell
   Copy-Item .env.example .env
   ```
4. (Opcional) cambiar PIN admin:
   ```powershell
   $env:ADMIN_ACTIONS_PIN="4321"
   $env:ADMIN_OVERRIDE_PIN="4321"
   ```
5. Levantar servidor:
   ```powershell
   python manage.py runserver
   ```
6. Abrir:
  - http://127.0.0.1:8000/login/
  - http://127.0.0.1:8000/kitchen/
  - http://127.0.0.1:8000/sales/
  - http://127.0.0.1:8000/dashboard/
  - http://127.0.0.1:8000/batches/
  - http://127.0.0.1:8000/admin-ops/

## Docker + PostgreSQL (recomendado)
1. Copiar variables:
   ```powershell
   Copy-Item .env.example .env
   ```
2. Levantar servicios:
   ```powershell
   docker compose up --build
   ```
3. Abrir:
   - http://127.0.0.1:8000/login/

Notas:
- `entrypoint.sh` ejecuta `migrate` + `collectstatic` automaticamente al iniciar `web`.
- La DB corre en contenedor `postgres:16-alpine` y persiste en volumen `postgres_data`.
- Si quieres levantar local sin Docker usando SQLite, ajusta `.env` segun comentarios en `.env.example`.

## Usuarios iniciales (auto bootstrap)
- `cocina` (rol kitchen, branding festival) PIN `DEFAULT_FESTIVAL_KITCHEN_PIN`
- `ventas` (rol sales, branding festival) PIN `DEFAULT_FESTIVAL_SALES_PIN`
- `lotes` (rol batches, branding festival) PIN `DEFAULT_FESTIVAL_BATCHES_PIN`
- `cocinaburger` (rol kitchen, branding burgers) PIN `DEFAULT_BURGERS_KITCHEN_PIN`
- `ventasburger` (rol sales, branding burgers) PIN `DEFAULT_BURGERS_SALES_PIN`
- `lotesburger` (rol batches, branding burgers) PIN `DEFAULT_BURGERS_BATCHES_PIN`
- `admin` (rol admin) PIN `DEFAULT_ADMIN_LOGIN_PIN`

## Notas operativas
- El QR debe contener solo el ID (fuente de verdad: servidor).
- La UI funciona con scanner USB tipo keyboard wedge (Enter al final).
- Cada scan da feedback visual + sonido + vibracion.
- El endpoint de ventas permite override con PIN admin.
