# Manual de instalación

Cómo levantar VulnScan Platform en una máquina nueva, de cero a todos los
servicios saludables. Para correr una prueba completa de punta a punta
una vez instalado, ver la [guía de demostración](demo.md); para el uso
diario del dashboard, ver el [manual de uso](usage.md).

## Requisitos

- [Docker](https://www.docker.com/) con Docker Compose (viene incluido
  con Docker Desktop en Windows/Mac; en Linux, el plugin `docker-compose-plugin`).
- Un navegador web.
- Nada más — ninguna herramienta de seguridad, lenguaje ni dependencia
  se instala en el host; todo corre dentro de los contenedores.

## 1. Clonar el repositorio

```bash
git clone <url-del-repositorio>
cd tesis_v2
```

## 2. Configurar variables de entorno

```bash
cp .env.example .env
```

Los valores por defecto de `.env.example` funcionan tal cual para un
entorno local — no hace falta editar nada para levantar el sistema. Vale
la pena revisar dos cosas si algo no encaja en tu máquina:

- **Puertos ya ocupados**: si algún puerto por defecto (`8000`, `5678`,
  `8080`, `3000`, `3001`, `5432`, `8100`, `8200`) ya está en uso por otro
  proceso, cambiá la variable correspondiente en `.env` (por ejemplo
  `BACKEND_PORT=8001`) antes de levantar los servicios. Ver la sección
  "Si un puerto ya está en uso" de la [guía de demostración](demo.md).
- **Secretos de desarrollo**: `.env.example` trae contraseñas/keys
  placeholder (`change_me_local_dev_only`) para `POSTGRES_PASSWORD`,
  `BACKEND_API_KEY`, `INTERNAL_API_KEY`, `N8N_ENCRYPTION_KEY` y
  `N8N_BASIC_AUTH_PASSWORD`. Son suficientes para un laboratorio local;
  no reutilizar estos valores fuera de ese contexto. Ver
  [`docs/security.md`](security.md) para el modelo completo y sus
  límites.

## 3. Levantar todos los servicios

```bash
docker compose up -d
```

Esto construye y levanta los 9 servicios definidos en
`docker-compose.yml`: base de datos, migraciones, backend, scanner,
reports, n8n, frontend, y los dos targets del laboratorio (Juice Shop,
DVWA). La primera vez puede tardar varios minutos — compila el Scanner
Service (instala Nmap/Nikto/Nuclei/ZAP) y el Reports Service (instala
WeasyPrint). Las siguientes veces es cuestión de segundos, salvo que
cambiés una dependencia.

## 4. Verificar que todo esté saludable

```bash
docker compose ps
```

Todos los servicios deberían mostrar `Up ... (healthy)`. Si alguno queda
en `Created` sin arrancar, corré `docker compose up -d` de nuevo — a
veces el primer intento no alcanza a esperar toda la cadena de
dependencias entre servicios.

Chequeo rápido por servicio (asumiendo los puertos por defecto):

```bash
curl http://localhost:8000/health   # Backend
curl http://localhost:8080/health   # Frontend (nginx)
```

Scanner y Reports (Módulo 9) ya no publican su puerto al host — no son
alcanzables con `curl` desde fuera de los contenedores, solo desde
`app-network`. Ver [`docs/security.md`](security.md).

## 5. Importar y activar el workflow de n8n

n8n **no** importa workflows automáticamente al arrancar — es una
limitación estándar de n8n (no hay un mecanismo soportado de "watch this
folder"). Hacelo una vez por cada volumen de datos nuevo (si nunca
corriste `docker compose down -v`, no hace falta repetirlo):

```bash
docker compose exec n8n n8n import:workflow --input=/workflows/vulnscan-pipeline.json
```

Después:

1. Abrí `http://localhost:5678` (o el puerto que hayas configurado en
   `N8N_PORT`).
2. Iniciá sesión con `N8N_BASIC_AUTH_USER` / `N8N_BASIC_AUTH_PASSWORD`
   (por defecto en `.env.example`: `admin` / `change_me_local_dev_only`).
3. Abrí el workflow **"VulnScan Pipeline"** en la lista.
4. Hacé click en **Publish** (arriba a la derecha) — te va a pedir un
   nombre de versión, cualquier texto sirve. Esto deja el workflow
   activo y listo para recibir ejecuciones; sin este paso, el Webhook
   Trigger no responde.

## 6. (Opcional) Configurar el envío de mails

El último paso del pipeline manda el reporte por mail vía
[Ethereal Email](https://ethereal.email), un servicio SMTP de prueba que
nunca entrega a una bandeja real. Es un paso manual único por instancia
de n8n — ver "Email delivery (stage 12)" en
[`n8n/README.md`](../n8n/README.md#email-delivery-stage-12). Si se omite,
el resto del pipeline funciona igual; solo el paso de envío de mail
queda sin efecto (corre con `continueOnFail: true`, no rompe la
ejecución).

## 7. Abrir el dashboard

```
http://localhost:8080
```

Ver el [manual de uso](usage.md) para lo que se puede hacer desde ahí.

## Apagar todo

```bash
docker compose down
```

Agregá `-v` (`docker compose down -v`) si además querés borrar los datos
persistidos (base de datos, workflow importado en n8n, reportes
generados) y arrancar de cero la próxima vez — en ese caso hay que
repetir el paso 5 (importar el workflow) al volver a levantar el
sistema.

## Problemas comunes

| Síntoma | Causa / solución |
|---|---|
| `port is already allocated` al hacer `docker compose up` | Otro proceso usa ese puerto — cambialo en `.env` (ver paso 2). |
| El dashboard carga pero la lista de targets queda vacía o tira error de red | Ver la consola del navegador / pestaña Network. Si el Backend responde `401`, la imagen del Frontend puede haberse construido antes de que `BACKEND_API_KEY` tuviera el valor actual en `.env` — reconstruila con `docker compose build frontend && docker compose up -d frontend` (Vite inlinea la key en build time, no en runtime). |
| El Form Trigger de n8n muestra `404` o página no encontrada | El workflow no está **Publish**ado (ver paso 5). |
| Las URLs que genera n8n apuntan a un puerto distinto al que usás en el navegador | `docker-compose.yml` calcula `N8N_EDITOR_BASE_URL` a partir de `N8N_PORT` — si lo cambiaste en `.env` por un conflicto, reiniciá el contenedor para que tome el valor nuevo: `docker compose up -d n8n`. |
| Un volumen de una instalación previa de este proyecto causa `PermissionError` en Reports | Un volumen `reports-data` creado antes del hardening de contenedores (Módulo 9) puede tener archivos con dueño `root`. Corregilo una sola vez: `docker run --rm -v <nombre-del-volumen>:/data alpine chown -R 1000:1000 /data`. |
| `422 Unprocessable Entity` al registrar un target | El `host` no está en la whitelist — solo se aceptan los valores de `BACKEND_ALLOWED_LAB_HOSTS` en `.env` (por defecto `juice-shop`, `dvwa`). |
