# Guía de demostración

Esta guía está pensada para que **cualquier persona ajena al desarrollo** de
VulnScan Platform pueda levantar el sistema completo y ejecutar una prueba
exitosa de punta a punta: desde registrar un target hasta recibir un reporte
PDF con los hallazgos, por mail. No asume conocimiento previo del proyecto —
solo Docker instalado.

> ⚠️ Todo lo que hace este sistema apunta exclusivamente al laboratorio local
> incluido en el propio `docker-compose.yml` (Juice Shop, DVWA). Ver
> [`docs/lab.md`](lab.md) para el alcance legal completo.

---

## 1. Requisitos

- [Docker](https://www.docker.com/) y Docker Compose (viene incluido con
  Docker Desktop).
- Un navegador web.
- Nada más — ninguna herramienta de seguridad, lenguaje, ni dependencia se
  instala en tu máquina; todo corre dentro de los contenedores.

## 2. Levantar la plataforma

Desde la raíz del repositorio:

```bash
cp .env.example .env
docker compose up -d
```

Esto construye y levanta los 8 servicios (base de datos, backend, scanner,
reports, n8n, frontend cuando exista, y los dos targets del laboratorio).
La primera vez puede tardar varios minutos (compila el Scanner Service, que
instala Nmap/Nikto/Nuclei/ZAP, y el Reports Service, que instala
WeasyPrint). Las siguientes veces es cuestión de segundos.

Verificá que todo esté saludable:

```bash
docker compose ps
```

Todos los servicios deberían mostrar `Up ... (healthy)`. Si alguno queda en
`Created` sin arrancar, corré `docker compose up -d` de nuevo — a veces el
primer intento no alcanza a esperar toda la cadena de dependencias.

### Si un puerto ya está en uso

Si ves un error como `port is already allocated`, algún otro proceso de tu
máquina ya está usando ese puerto (por ejemplo, otro proyecto con un
servicio en `8000` o `5678`). Solución: abrí `.env` y cambiá el puerto en
conflicto por otro libre, por ejemplo:

```bash
BACKEND_PORT=8001
N8N_PORT=5679
```

y volvé a correr `docker compose up -d`. El resto de esta guía asume los
puertos por defecto (`8000`, `5678`, etc.) — si los cambiaste, reemplazalos
en las URLs de abajo.

## 3. Importar el workflow en n8n (una sola vez)

n8n no importa workflows automáticamente al arrancar. Hacelo una vez por
cada volumen de datos nuevo (si nunca corriste `docker compose down -v`,
no hace falta repetirlo):

```bash
docker compose exec n8n n8n import:workflow --input=/workflows/vulnscan-pipeline.json
```

Después:

1. Abrí `http://localhost:5678` en el navegador.
2. Iniciá sesión con `N8N_BASIC_AUTH_USER` / `N8N_BASIC_AUTH_PASSWORD` (por
   defecto en `.env.example`: `admin` / `change_me_local_dev_only`).
3. Abrí el workflow **"VulnScan Pipeline"** en la lista.
4. Hacé click en **Publish** (arriba a la derecha). Te va a pedir un nombre
   de versión — cualquier texto sirve, por ejemplo `"demo"`.

Esto deja el workflow activo y listo para recibir ejecuciones.

## 4. Registrar un target

El sistema solo puede escanear los hosts del laboratorio incluido
(`juice-shop` o `dvwa` — ver la whitelist en
[`backend/README.md`](../backend/README.md#the-lab-whitelist)). Registrá
uno:

```bash
curl -X POST http://localhost:8000/targets \
  -H "Content-Type: application/json" \
  -d '{"name": "juice-shop-demo", "host": "juice-shop", "description": "Demo target"}'
```

La respuesta trae un `id` — ese es el **target_id** que vas a usar en el
paso siguiente. Ejemplo:

```json
{"id": "9bd7313a-55b9-44c1-8649-ac875519d08b", "name": "juice-shop-demo", "host": "juice-shop", ...}
```

Si en algún momento perdés ese id, pedilo de nuevo con:

```bash
curl http://localhost:8000/targets
```

## 5. Ejecutar el pipeline

Hay dos formas de disparar el escaneo completo. Para una demo en vivo, la
opción B (sin terminal) suele ser la más práctica.

### Opción A — vía API (como lo haría el futuro frontend)

```bash
curl -X POST http://localhost:8000/targets/{target_id}/pipeline
```

(reemplazando `{target_id}` por el id del paso anterior). Devuelve
inmediatamente un `202` con el scan recién creado — el pipeline sigue
corriendo en segundo plano.

### Opción B — vía el formulario manual de n8n (sin terminal)

1. En n8n, abrí el nodo **Form Trigger** del workflow (doble click).
2. Copiá la **Production URL** que muestra arriba del nodo.
3. Pegala en una pestaña nueva del navegador. Va a aparecer un formulario
   simple pidiendo `target_id`.
4. Pegá el id del paso 4 y enviá.

Ambas opciones disparan exactamente el mismo pipeline: reconocimiento
(Nmap) → identificación de tecnologías (WhatWeb) → escaneo (Nikto, Nuclei,
ZAP) → clasificación y persistencia de hallazgos → generación de reporte
PDF → envío por mail.

### Cuánto tarda

**Entre 4 y 6 minutos.** El cuello de botella es ZAP (hace un escaneo activo
real, no una simulación). No es que se cuelgue — podés seguir el progreso
en tiempo real desde la pestaña **Executions** de n8n, viendo cada nodo
iluminarse a medida que corre.

## 6. Ver los resultados

### Los hallazgos

```bash
curl http://localhost:8000/scans/{scan_id}/findings
```

El `scan_id` te lo devuelve tanto la Opción A como el nodo "Create Scan
(Manual)" dentro de la ejecución de n8n (click en el nodo → panel de la
derecha).

### El reporte PDF

El pipeline genera automáticamente un PDF al finalizar. Para bajarlo:

```bash
# 1. Listar los reportes de ese scan
curl http://localhost:8000/scans/{scan_id}/reports

# 2. Descargar con el id que te devolvió el paso anterior
curl http://localhost:8000/reports/{report_id}/download -o reporte.pdf
```

También podés pegar esa segunda URL directo en el navegador para
descargarlo/abrirlo sin usar la terminal.

Otros formatos (`html`, `markdown`, `json`) están disponibles bajo demanda,
llamando al mismo endpoint de generación con otro `format`:

```bash
curl -X POST "http://localhost:8000/scans/{scan_id}/reports?format=html"
```

### El mail (opcional)

El último paso del pipeline manda el PDF por mail usando
[Ethereal Email](https://ethereal.email) — un servicio SMTP de prueba que
nunca entrega mails reales, solo los captura para verlos en su web. Si
todavía no configuraste esto, es un paso manual único — ver
[`n8n/README.md`](../n8n/README.md#email-delivery-stage-12).

Si ya está configurado, después de correr el pipeline entrá a
`https://ethereal.email/messages` con el usuario que generaste ahí y
deberías ver el mail con el PDF adjunto.

## 7. Apagar todo

```bash
docker compose down
```

Agregá `-v` (`docker compose down -v`) si además querés borrar los datos
persistidos (base de datos, workflow importado en n8n, reportes generados)
y arrancar de cero la próxima vez.

---

## Problemas comunes

| Síntoma | Causa / solución |
|---|---|
| `port is already allocated` al hacer `docker compose up` | Otro proceso usa ese puerto — cambialo en `.env` (ver sección 2). |
| El Form Trigger de n8n muestra `404` o página no encontrada | El workflow no está **Publish**ado (ver sección 3, paso 4). |
| Las URLs que genera n8n (Production URL del Form Trigger, etc.) apuntan a un puerto distinto al que usás en el navegador | `docker-compose.yml` calcula `N8N_EDITOR_BASE_URL` automáticamente a partir de `N8N_PORT`, así que si cambiaste `N8N_PORT` en `.env` por un conflicto, solo hace falta reiniciar el contenedor para que tome el valor nuevo: `docker compose up -d n8n`. |
| El pipeline queda "corriendo" mucho más de 6 minutos | Revisá `docker compose logs backend --tail=30` — si no aparecen nuevas líneas `POST /scans/.../tasks`, algo se frenó; revisá también `docker compose logs n8n` por errores de nodo. |
| El mail llega pero no ves el adjunto | Los adjuntos en Ethereal aparecen separados del cuerpo del mensaje (con ícono de clip), no inline en el texto — revisá la vista completa del mensaje, no solo el pie de página. |
| `422 Unprocessable Entity` al registrar un target | El `host` no está en la whitelist — solo se aceptan `juice-shop` y `dvwa` (ver `BACKEND_ALLOWED_LAB_HOSTS` en `.env`). |
| `409 Conflict` al registrar un target | Ya existe un target con ese `name` — usá uno distinto o reusá el existente (`GET /targets`). |
