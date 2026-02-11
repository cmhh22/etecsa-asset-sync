# Deploy GRATIS en PythonAnywhere (Sin Tarjeta)

PythonAnywhere es la **única opción 100% gratuita sin tarjeta de crédito** que soporta Django completamente.

## Paso 1: Crear Cuenta (5 minutos)

1. Ve a https://www.pythonanywhere.com/registration/register/beginner/
2. Completa el formulario (solo email, username, password)
3. Verifica tu email
4. Login en https://www.pythonanywhere.com

## Paso 2: Clonar el Proyecto

1. En PythonAnywhere Dashboard, ve a **"Consoles"** tab
2. Click en **"Bash"** para abrir una terminal
3. Ejecuta estos comandos:

```bash
# Clonar el repositorio
git clone https://github.com/cmhh22/etecsa-asset-sync.git

# Entrar al directorio
cd etecsa-asset-sync/OCS
```

## Paso 3: Crear Entorno Virtual

```bash
# Crear virtualenv con Python 3.12
mkvirtualenv --python=/usr/bin/python3.12 etecsa-env

# Instalar dependencias
pip install -r requirements.txt
```

## Paso 4: Configurar Base de Datos MySQL

1. En Dashboard, ve a **"Databases"** tab
2. Click en **"Initialize MySQL"**
3. Establece una contraseña (anótala)
4. Copia el **hostname** (algo como `tu_usuario.mysql.pythonanywhere-services.com`)

Vuelve a la consola Bash:

```bash
cd ~/etecsa-asset-sync/OCS

# Crear archivo .env
nano .env
```

Pega esto (reemplaza con tus valores):

```bash
SECRET_KEY=tu-secret-key-aqui-genera-uno-largo
DEBUG=False
ALLOWED_HOSTS=tu_usuario.pythonanywhere.com
DB_ENGINE=django.db.backends.mysql
DB_NAME=tu_usuario$etecsa_db
DB_USER=tu_usuario
DB_PASSWORD=tu-password-mysql
DB_HOST=tu_usuario.mysql.pythonanywhere-services.com
DB_PORT=3306
CSRF_TRUSTED_ORIGINS=http://tu_usuario.pythonanywhere.com
SECURE_SSL_REDIRECT=False
```

Guarda: `Ctrl+O`, `Enter`, `Ctrl+X`

## Paso 5: Crear Base de Datos

```bash
# En la consola Bash
mysql -u tu_usuario -h tu_usuario.mysql.pythonanywhere-services.com -p

# Cuando pida password, ingresa tu password de MySQL
# Luego ejecuta:
CREATE DATABASE tu_usuario$etecsa_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
EXIT;
```

## Paso 6: Migrar y Preparar

```bash
cd ~/etecsa-asset-sync/OCS

# Activar virtualenv (si no está activo)
workon etecsa-env

# Migrar base de datos
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser
# Username: admin
# Email: tu@email.com
# Password: admin123 (o el que prefieras)

# Seedear datos demo
python manage.py seed_demo

# Recolectar archivos estáticos
python manage.py collectstatic --noinput
```

## Paso 7: Configurar Web App

1. Dashboard → **"Web"** tab
2. Click **"Add a new web app"**
3. Selecciona **"Manual configuration"** (NO Django wizard)
4. Python version: **3.12**

### Configurar Code & Virtualenv:

En la página de configuración de Web App:

**Code section:**
- **Source code**: `/home/tu_usuario/etecsa-asset-sync/OCS`
- **Working directory**: `/home/tu_usuario/etecsa-asset-sync/OCS`

**Virtualenv section:**
- **Path**: `/home/tu_usuario/.virtualenvs/etecsa-env`

### Configurar WSGI:

1. Click en el link **"WSGI configuration file"** (algo como `/var/www/tu_usuario_pythonanywhere_com_wsgi.py`)
2. **Borra todo el contenido**
3. Pega esto:

```python
import os
import sys

# Agregar el proyecto al path
path = '/home/tu_usuario/etecsa-asset-sync/OCS'
if path not in sys.path:
    sys.path.append(path)

# Configurar Django settings
os.environ['DJANGO_SETTINGS_MODULE'] = 'OCS.settings'

# Cargar variables de entorno desde .env
from pathlib import Path
from decouple import config

# Cargar la aplicación WSGI
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

4. Reemplaza `tu_usuario` con tu username real
5. **Save** (botón arriba a la derecha)

### Configurar Static Files:

En la misma página de configuración, scroll a **"Static files"**:

| URL | Directory |
|-----|-----------|
| `/static/` | `/home/tu_usuario/etecsa-asset-sync/OCS/staticfiles` |

Click **"Save"** después de cada entrada.

## Paso 8: Recargar y Probar

1. Scroll arriba en la página Web
2. Click en el botón verde **"Reload tu_usuario.pythonanywhere.com"**
3. Espera ~10 segundos
4. Click en tu URL: `http://tu_usuario.pythonanywhere.com`

**Login**: admin / admin123 (o la contraseña que pusiste)

---

## Troubleshooting

### Error "Something went wrong :("

Ve a la sección **"Log files"** en tu Web tab:
- Click en **"Error log"** para ver errores específicos

**Errores comunes:**

1. **ModuleNotFoundError**:
   - Verifica que el virtualenv esté activado: `workon etecsa-env`
   - Reinstala: `pip install -r requirements.txt`

2. **django.db.utils.OperationalError: (2002, "Can't connect to MySQL")**:
   - Verifica `.env`: `DB_HOST` debe ser `tu_usuario.mysql.pythonanywhere-services.com`
   - Verifica que creaste la base de datos

3. **CSRF verification failed**:
   - En `.env`: `CSRF_TRUSTED_ORIGINS=http://tu_usuario.pythonanywhere.com` (sin `https://`)

4. **Static files not loading**:
   - Ejecuta: `python manage.py collectstatic --noinput`
   - Verifica la configuración de "Static files" en Web tab

### Re-deployar cambios

Cada vez que actualices el código en GitHub:

```bash
# En consola Bash
cd ~/etecsa-asset-sync
git pull origin main
cd OCS
workon etecsa-env
python manage.py migrate
python manage.py collectstatic --noinput
```

Luego en Web tab: **"Reload"**

---

## Limitaciones del Tier Gratuito

| Limitación | Impacto |
|------------|---------|
| **No HTTPS** | No SSL en `tu_usuario.pythonanywhere.com` (solo HTTP) |
| **512MB storage** | Suficiente para este proyecto (~50MB usado) |
| **100MB MySQL** | OK para demo (20 assets = ~5MB) |
| **2 consoles** | Suficiente para desarrollo |
| **CPU 100s/día** | Límite diario alcanzado si hay mucho tráfico |
| **Whitelist internet** | Solo puedes acceder a sitios aprobados desde código |

Para portafolio/demo es perfecto. Para producción real necesitarías plan pagado.

---

## Actualizar proyecto después de cambios

1. Consola Bash:
   ```bash
   cd ~/etecsa-asset-sync
   git pull origin main
   cd OCS
   workon etecsa-env
   python manage.py migrate
   python manage.py collectstatic --noinput
   ```

2. Web tab → **"Reload"**

---

## Backup de la Base de Datos

```bash
# En consola Bash
mysqldump -u tu_usuario -h tu_usuario.mysql.pythonanywhere-services.com -p tu_usuario$etecsa_db > backup_$(date +%Y%m%d).sql
```

---

## Links Útiles

- **Tu app**: http://tu_usuario.pythonanywhere.com
- **Dashboard**: https://www.pythonanywhere.com/user/tu_usuario/
- **Help**: https://help.pythonanywhere.com/
- **Forums**: https://www.pythonanywhere.com/forums/

---

## Ejemplo de URL final

Si tu username es `cmhh22`:
- **App**: http://cmhh22.pythonanywhere.com
- **Login**: admin / admin123
- **Analytics**: http://cmhh22.pythonanywhere.com/analytics/
