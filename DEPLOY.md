# Guía de despliegue en una VPS con Docker

Esta guía es genérica: aplica igual en DigitalOcean, Hetzner, Oracle Cloud,
Vultr, Linode o cualquier VPS con Ubuntu 22.04/24.04. Solo cambia cómo
contratas/creas el servidor; una vez tienes acceso por SSH, los pasos son
idénticos.

## 0. Requisitos antes de empezar

- Una VPS con Ubuntu 22.04 o 24.04, con al menos 1 vCPU / 1 GB RAM (suficiente
  para este proyecto de bajo tráfico).
- Acceso SSH a la VPS.
- Un dominio (o subdominio gratis de [DuckDNS](https://www.duckdns.org/))
  apuntando con un registro **A** a la IP pública de la VPS. Necesario para
  que Google OAuth funcione (exige HTTPS) y para que Caddy pueda emitir el
  certificado TLS automáticamente.

## 1. Instala Docker en la VPS

Conéctate por SSH y ejecuta:

```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
```

Cierra sesión y vuelve a entrar por SSH para que el cambio de grupo aplique.
Verifica:

```bash
docker --version
docker compose version
```

## 2. Abre el firewall

```bash
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

## 3. Clona el proyecto

```bash
git clone https://github.com/deisygaleano/Kuma_coffee.git kuma_coffee
cd kuma_coffee
```

## 4. Configura el `.env`

```bash
nano .env
```

Contenido (nota que `DB_HOST` debe ser `db`, el nombre del servicio de
MySQL en `docker-compose.yml`, no `localhost`):

```
DJANGO_SECRET_KEY=<genera una nueva, ver abajo>
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=tu-dominio.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://tu-dominio.com

DB_NAME=kuma_coffee
DB_USER=kuma_user
DB_PASSWORD=<una clave fuerte>
DB_HOST=db
DB_PORT=3306
DB_ROOT_PASSWORD=<otra clave fuerte, distinta>

GOOGLE_CLIENT_ID=<tu client id de Google>
GOOGLE_CLIENT_SECRET=<tu client secret de Google>
GOOGLE_REDIRECT_URI=https://tu-dominio.com/cuentas/google/callback
```

Genera una `SECRET_KEY` nueva:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(50))"
```

## 5. Configura el dominio en `Caddyfile`

Edita `Caddyfile` y reemplaza `tu-dominio.duckdns.org` por tu dominio real:

```bash
nano Caddyfile
```

```
tu-dominio.com {
    encode gzip

    handle_path /media/* {
        root * /srv/media
        file_server
    }

    reverse_proxy web:8000
}
```

Caddy obtiene y renueva el certificado TLS de Let's Encrypt automáticamente,
no requiere configuración adicional.

## 6. Actualiza Google Cloud Console

En [console.cloud.google.com/apis/credentials](https://console.cloud.google.com/apis/credentials),
agrega como **URI de redirección autorizado**:

`https://tu-dominio.com/cuentas/google/callback`

## 7. Levanta los contenedores

```bash
docker compose up -d --build
```

Esto construye la imagen de Django, levanta MySQL, corre las migraciones
automáticamente (parte del comando de arranque del servicio `web`) y expone
todo detrás de Caddy con HTTPS.

Verifica que los tres servicios estén corriendo:

```bash
docker compose ps
```

## 8. Crea el superusuario

```bash
docker compose exec web python manage.py createsuperuser
```

## 9. Prueba

Visita `https://tu-dominio.com` y revisa:

- Que cargue el home con estilos (estáticos servidos por whitenoise dentro
  del contenedor `web`).
- Login normal y login con Google.
- Subida de imágenes de productos (`/media/`, servido por Caddy desde el
  volumen compartido).
- Panel de administración en `/admin/`.

## 10. Actualizaciones futuras

Cada vez que hagas cambios:

```bash
cd ~/kuma_coffee
git pull
docker compose up -d --build
```

Las migraciones se aplican automáticamente al reiniciar el servicio `web`.

## 11. Comandos útiles

```bash
docker compose logs -f web        # logs de Django/gunicorn
docker compose logs -f caddy       # logs de Caddy (útil para problemas de TLS)
docker compose exec web python manage.py <comando>   # cualquier comando de manage.py
docker compose down                # detener todo (los datos persisten en volúmenes)
```

## 12. Despliegue automático con GitHub Actions

Cada push a `main` puede desplegarse solo, sin entrar por SSH manualmente.
El workflow está en `.github/workflows/deploy.yml` y usa el script
`scripts/deploy.sh`, que además:

- Hace un backup (`mysqldump`) de la base de datos **antes** de reconstruir
  los contenedores, guardado en `~/kuma_coffee_backups/` en el servidor
  (conserva los últimos 2).
- Nunca usa `docker compose down -v` ni borra volúmenes: los datos de MySQL
  y las imágenes de productos viven en volúmenes con nombre
  (`mysql_data`, `media_data`) que persisten entre despliegues.
- Verifica, tras el `docker compose up -d --build`, que los contenedores
  `web` y `db` sigan corriendo. Si alguno murió (por ejemplo, por una
  migración rota), el workflow falla y muestra los últimos logs, en vez de
  dejar el sitio caído en silencio.

### Configuración inicial (una sola vez)

**1. Genera un par de llaves SSH dedicado para el despliegue** (no reutilices
tu llave personal de GitHub/SSH):

```bash
ssh-keygen -t ed25519 -f ./deploy_key -N "" -C "github-actions-deploy"
```

Esto crea `deploy_key` (privada) y `deploy_key.pub` (pública) en tu carpeta
actual.

**2. Autoriza la llave pública en el servidor:**

```bash
cat deploy_key.pub | ssh root@<ip-del-servidor> "cat >> ~/.ssh/authorized_keys"
```

**3. Crea estos secrets en GitHub** (`Settings > Secrets and variables >
Actions > New repository secret`):

| Secret | Valor |
|---|---|
| `DEPLOY_HOST` | IP o dominio del servidor (ej. `167.233.158.241`) |
| `DEPLOY_USER` | `root` |
| `DEPLOY_SSH_KEY` | Contenido completo de `deploy_key` (la llave **privada**) |

**4. Borra `deploy_key` y `deploy_key.pub` de tu computador** una vez
copiada la privada al secret (ya no las necesitas localmente).

A partir de aquí, cada push a `main` dispara el despliegue automáticamente;
puedes ver el progreso y los logs en la pestaña **Actions** del repositorio.

> Probado y funcionando: despliegue automático verificado en producción el
> 2026-07-05 (llave SSH dedicada renovada).

### Restaurar un backup si algo sale mal

```bash
ssh root@<ip-del-servidor>
cd ~/kuma_coffee
ls ~/kuma_coffee_backups/                # elige el backup a restaurar
docker compose exec -T db mysql -u root -p"$(grep DB_ROOT_PASSWORD .env | cut -d= -f2)" "$(grep DB_NAME .env | cut -d= -f2)" < ~/kuma_coffee_backups/backup_XXXXXXXX_XXXXXX.sql
```
