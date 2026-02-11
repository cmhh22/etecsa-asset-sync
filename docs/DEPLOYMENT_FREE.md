# Deployment en Fly.io (Free Tier Permanente)

## Opción 1: Deploy desde Navegador (MÁS FÁCIL)

### Paso 1: Crear Cuenta en Fly.io
1. Ve a https://fly.io/app/sign-up
2. Regístrate con GitHub (recomendado)
3. Verifica tu email

### Paso 2: Base de Datos MySQL Gratis con PlanetScale

**PlanetScale es gratis permanentemente** (10GB storage, 1 billón lecturas/mes):

1. Ve a https://planetscale.com
2. Regístrate con GitHub
3. Click en **"Create a new database"**
   - Name: `etecsa-ocs`
   - Region: `US East` (más cercano)
   - Plan: **Hobby** (gratis)
4. Click en **"Connect"**
5. Selecciona **"Django"** en el dropdown
6. Copia el **Database URL** (formato: `mysql://user:password@host/database`)

### Paso 3: Preparar el Proyecto

```bash
# Ya está hecho - los archivos fly.toml y Dockerfile están listos
git add fly.toml
git commit -m "config: add Fly.io deployment configuration"
git push origin main
```

### Paso 4: Deploy con Fly Launch

#### Opción A: Desde el navegador (si no puedes instalar CLI)
1. Ve a https://fly.io/apps/new
2. Selecciona "Import from GitHub"
3. Autoriza Fly.io
4. Selecciona el repo `etecsa-asset-sync`
5. Fly.io detectará automáticamente el `Dockerfile`

#### Opción B: Con Fly CLI (si ya instalaste flyctl)
```bash
cd "D:\CIBER !!!!\Estudio\CURSOS\Udemy - AI Mastery 150+ Projects, AI Algorithms, DeepSeek AI Agents 2025-3\Portafolio\Proyecto"

# Login
flyctl auth login

# Deploy (primera vez)
flyctl launch
# Responde:
# - App name: etecsa-asset-sync (o el que prefieras)
# - Region: mia (Miami)
# - Create database? NO (usaremos PlanetScale)
# - Deploy now? YES
```

### Paso 5: Configurar Secrets (Variables de Entorno)

```bash
# Con CLI
flyctl secrets set \
  SECRET_KEY="q$fim40qtq_9=8!jzssts6y%fg6p5v6xpbu35@&^2h)8a0yr+x" \
  DATABASE_URL="mysql://user:password@host/database?ssl-mode=REQUIRED" \
  DEBUG="False" \
  ALLOWED_HOSTS=".fly.dev" \
  CSRF_TRUSTED_ORIGINS="https://etecsa-asset-sync.fly.dev"

# Si no tienes CLI, desde el navegador:
# 1. Fly.io Dashboard → Tu app
# 2. Secrets tab → Add secrets
```

**Nota**: Reemplaza `DATABASE_URL` con el que copiaste de PlanetScale.

### Paso 6: Ejecutar Migraciones

```bash
# Con CLI
flyctl ssh console

# Dentro del container
cd /app
python manage.py migrate
python manage.py createsuperuser
# Username: admin
# Email: tu@email.com
# Password: (el que quieras)
python manage.py seed_demo  # Opcional: datos de prueba
exit
```

### Paso 7: Acceder a tu App

Tu app estará en: `https://etecsa-asset-sync.fly.dev`

---

## Opción 2: Alternative - Render (También Gratis)

Render tiene tier gratuito con **PostgreSQL incluido** (pero se duerme después de 15 min de inactividad).

### Paso 1: Ajustar para PostgreSQL

1. Edita `OCS/requirements.txt`:
   ```bash
   # Agregar al final:
   psycopg2-binary==2.9.9
   dj-database-url==2.2.0
   ```

2. Edita `OCS/OCS/settings.py`:
   ```python
   import dj_database_url
   
   # Reemplaza la sección DATABASES con:
   DATABASES = {
       'default': dj_database_url.config(
           default=f"{config('DB_ENGINE', 'django.db.backends.sqlite3')}://{config('DB_USER', '')}:{config('DB_PASSWORD', '')}@{config('DB_HOST', '')}:{config('DB_PORT', '')}/{config('DB_NAME', 'db.sqlite3')}",
           conn_max_age=600,
           ssl_require=True
       )
   }
   ```

### Paso 2: Deploy en Render

1. Ve a https://render.com
2. Regístrate con GitHub
3. Click **"New +"** → **"Web Service"**
4. Conecta tu repo `etecsa-asset-sync`
5. Configuración:
   - **Name**: etecsa-asset-sync
   - **Region**: Oregon (gratis)
   - **Branch**: main
   - **Build Command**: 
     ```bash
     pip install -r OCS/requirements.txt && cd OCS && python manage.py collectstatic --noinput
     ```
   - **Start Command**: 
     ```bash
     cd OCS && gunicorn OCS.wsgi:application --bind 0.0.0.0:$PORT
     ```
   - **Plan**: Free

6. Click **"Advanced"** → **"Add Environment Variable"**:
   ```
   SECRET_KEY=q$fim40qtq_9=8!jzssts6y%fg6p5v6xpbu35@&^2h)8a0yr+x
   DEBUG=False
   ALLOWED_HOSTS=.onrender.com
   CSRF_TRUSTED_ORIGINS=https://etecsa-asset-sync.onrender.com
   SECURE_SSL_REDIRECT=True
   ```

7. Click **"Create Web Service"**

8. Mientras se deploya, crea base de datos:
   - Dashboard → **"New +"** → **"PostgreSQL"**
   - Name: etecsa-db
   - Plan: Free
   - Copia el **Internal Database URL**

9. Agrega variable `DATABASE_URL` en tu web service con el URL copiado

10. Ejecutar migraciones:
    - Render Dashboard → Tu web service → **"Shell"**
    ```bash
    cd OCS
    python manage.py migrate
    python manage.py createsuperuser
    python manage.py seed_demo
    ```

**⚠️ Limitación**: Se duerme después de 15 min sin tráfico (tarda ~30 seg en despertar).

---

## Opción 3: PythonAnywhere (Más Simple, Muy Limitado)

### Free Tier Permanente:
- ✅ 512MB storage
- ✅ 1 web app
- ✅ MySQL incluido (100MB)
- ⚠️ No HTTPS en subdominios gratuitos
- ⚠️ Restricciones de outbound requests

### Deploy:
1. https://www.pythonanywhere.com → Sign up (Free)
2. Dashboard → **"Web"** → **"Add a new web app"**
3. **"Manual configuration"** → Python 3.12
4. En **"Code"** section:
   - Source code: `/home/tu_usuario/etecsa-asset-sync`
   - Working directory: `/home/tu_usuario/etecsa-asset-sync/OCS`
   - WSGI file: Click para editar, pega:
     ```python
     import sys
     import os
     
     path = '/home/tu_usuario/etecsa-asset-sync/OCS'
     if path not in sys.path:
         sys.path.append(path)
     
     os.environ['DJANGO_SETTINGS_MODULE'] = 'OCS.settings'
     
     from django.core.wsgi import get_wsgi_application
     application = get_wsgi_application()
     ```

5. Console Bash:
   ```bash
   git clone https://github.com/cmhh22/etecsa-asset-sync.git
   cd etecsa-asset-sync/OCS
   pip install -r requirements.txt --user
   python manage.py migrate
   python manage.py createsuperuser
   python manage.py collectstatic --noinput
   ```

6. Configurar MySQL:
   - Dashboard → **"Databases"** → Initialize MySQL
   - Agregar conexión en `.env`

Tu app: `http://tu_usuario.pythonanywhere.com`

---

## Recomendación Final

| Plataforma | Pros | Contras | Recomendado |
|------------|------|---------|-------------|
| **Fly.io + PlanetScale** | ✅ Siempre activo<br>✅ HTTPS<br>✅ Escalable | ⚠️ 2 servicios separados | **⭐ MEJOR** |
| **Render** | ✅ Todo incluido<br>✅ PostgreSQL gratis | ❌ Se duerme (15min) | Portfolio OK |
| **PythonAnywhere** | ✅ Muy simple | ❌ Muy limitado<br>❌ No HTTPS gratis | Solo pruebas |

---

## Troubleshooting

### Fly.io: "failed to fetch an image"
```bash
flyctl deploy --remote-only
```

### PlanetScale: SSL errors
Asegúrate de que `DATABASE_URL` tenga `?ssl-mode=REQUIRED` al final.

### Render: "Application failed to respond"
Verifica que `PORT` esté en el bind: `0.0.0.0:$PORT` (Render asigna dinámicamente).

### Build timeouts
Aumenta timeout en `fly.toml`:
```toml
[build]
  build-timeout = "20m"
```
