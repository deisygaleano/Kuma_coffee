# Guía de despliegue en PythonAnywhere

## 1. Sube el proyecto a un repositorio remoto (GitHub)

Si aún no lo tienes en GitHub, créalo y haz push (sin subir `.env`, ya está en `.gitignore`):

```bash
git remote add origin <tu-repo>
git push -u origin main
```

## 2. Crea la cuenta y el entorno en PythonAnywhere

1. Regístrate gratis en pythonanywhere.com.
2. Abre una consola **Bash** desde el Dashboard.
3. Clona el repo:
   ```bash
   git clone https://github.com/tu-usuario/tu-repo.git kuma_coffee
   cd kuma_coffee
   ```
4. Crea el entorno virtual (usa la versión de Python 3.12/3.13 disponible):
   ```bash
   python3.12 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

## 3. Base de datos MySQL

1. Pestaña **Databases** → crea tu base de datos MySQL gratuita (te da una sola).
2. Anota el host (`tu_usuario.mysql.pythonanywhere-services.com`) y define una contraseña de MySQL.
3. **Importante**: en el plan free, PythonAnywhere exige que el nombre de la base tenga el prefijo de tu usuario, ej: `tu_usuario$kuma_coffee`.

## 4. Configura el `.env` en el servidor

Crea el archivo directamente en el servidor (nunca lo subas por git):

```bash
nano /home/tu_usuario/kuma_coffee/.env
```

Contenido:

```
DJANGO_SECRET_KEY=<genera una nueva, ver abajo>
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=tu_usuario.pythonanywhere.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://tu_usuario.pythonanywhere.com

DB_NAME=tu_usuario$kuma_coffee
DB_USER=tu_usuario
DB_PASSWORD=<tu password de MySQL>
DB_HOST=tu_usuario.mysql.pythonanywhere-services.com
DB_PORT=3306

GOOGLE_CLIENT_ID=<tu client id de Google>
GOOGLE_CLIENT_SECRET=<tu client secret de Google>
GOOGLE_REDIRECT_URI=https://tu_usuario.pythonanywhere.com/cuentas/google/callback
```

Para generar una `SECRET_KEY` nueva:

```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

## 5. Actualiza Google Cloud Console

En [console.cloud.google.com/apis/credentials](https://console.cloud.google.com/apis/credentials), agrega como **URI de redirección autorizado**:

`https://tu_usuario.pythonanywhere.com/cuentas/google/callback`

Este paso es obligatorio independientemente de si rotas o no el client secret; sin él, Google rechaza el login en producción con `redirect_uri_mismatch`.

Si el client secret quedó expuesto en el historial de git (commiteado en texto plano en algún momento), conviene rotarlo desde esta misma pantalla, sobre todo si el repositorio es o será público.

## 6. Migraciones, estáticos y superusuario

```bash
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

## 7. Configura la Web App

1. Pestaña **Web** → **Add a new web app** → elige **Manual configuration** (no "Django" preconfigurado, porque ya tenemos nuestro propio proyecto) → selecciona la misma versión de Python del venv.
2. En **Virtualenv**, indica la ruta: `/home/tu_usuario/kuma_coffee/venv`
3. En **Code** → **WSGI configuration file**, edítalo y reemplaza el contenido por algo como:

   ```python
   import os
   import sys

   path = '/home/tu_usuario/kuma_coffee'
   if path not in sys.path:
       sys.path.insert(0, path)

   os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kuma_coffee.settings')

   from django.core.wsgi import get_wsgi_application
   application = get_wsgi_application()
   ```

   (nuestro `settings.py` ya carga el `.env` automáticamente con `load_dotenv`, así que no hace falta declarar variables aquí).
4. En **Static files**, agrega dos mapeos:
   - URL `/static/` → Directory `/home/tu_usuario/kuma_coffee/staticfiles`
   - URL `/media/` → Directory `/home/tu_usuario/kuma_coffee/media`
5. Click en **Reload** (botón verde grande arriba).

## 8. Verifica el tráfico saliente para Google OAuth

El plan free restringe peticiones salientes a una whitelist. Antes de probar el login con Google:

- Ve a **Account** → **"Whitelisted sites"** y confirma si `accounts.google.com`, `oauth2.googleapis.com` y `www.googleapis.com` están permitidos.
- Si no lo están, puedes pedir que los agreguen (a veces lo permiten para dominios de Google) o considerar el plan pago "Hacker" (~$5/mes) que elimina la restricción.

## 9. Prueba

Visita `https://tu_usuario.pythonanywhere.com` y revisa:

- Que cargue el home con estilos (confirma que whitenoise/estáticos funcionan).
- Login normal y login con Google.
- Subida de imágenes de productos (confirma que `/media/` funciona).
- Panel de administración en `/admin/`.

## 10. Actualizaciones futuras

Cada vez que hagas cambios:

```bash
cd ~/kuma_coffee
git pull
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
```

Luego pestaña **Web** → **Reload**.
