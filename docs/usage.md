# Manual de uso

Cómo usar VulnScan Platform día a día una vez instalado (ver el
[manual de instalación](installation.md) si todavía no lo levantaste).
Para una prueba guiada de punta a punta con `curl`, ver la
[guía de demostración](demo.md).

Todo lo que sigue asume el dashboard en `http://localhost:8080` y el
Backend en `http://localhost:8000` (los puertos por defecto — ajustar si
los cambiaste en `.env`).

## El dashboard

### Pantalla de Targets (`/targets`)

Punto de entrada. Muestra la lista de targets registrados (nombre, host,
estado activo/inactivo, fecha de creación) con un link **Ver detalle**
por fila.

Arriba, un formulario para registrar un target nuevo:

| Campo | Notas |
|---|---|
| Nombre | Debe ser único — un nombre repetido devuelve `409 Conflict`. |
| Host | Solo se aceptan los hosts del laboratorio configurados en `BACKEND_ALLOWED_LAB_HOSTS` (por defecto `juice-shop`, `dvwa`). Cualquier otro valor devuelve `422`. |
| Descripción | Opcional. |

### Detalle de target (`/targets/{id}`)

Muestra los datos del target y su **historial de scans** (fecha,
estado: `running` / `completed` / `failed`), cada uno con link al
detalle del scan.

El botón **Correr Pipeline** dispara el pipeline completo de 12 etapas
contra ese target (`POST /targets/{id}/pipeline` en el Backend, que a su
vez llama al webhook de n8n). La llamada devuelve casi inmediatamente —
el scan queda en estado `running` y el pipeline sigue corriendo en
segundo plano. **Normalmente tarda entre 5 y 8 minutos**, dominado por el
escaneo activo de ZAP — la duración exacta varía según la carga del host y
puede extenderse más allá de ese rango; no hay indicador de progreso en
vivo en esta pantalla,
hay que refrescar o volver a entrar al detalle del scan para ver el
estado actualizado.

### Detalle de scan (`/scans/{id}`)

Dos secciones:

- **Findings**: tabla de hallazgos normalizados (severidad, título,
  tipo, CVSS, CVE), con checkboxes para filtrar por severidad
  (`CRITICAL`/`HIGH`/`MEDIUM`/`LOW`/`INFO`) y columnas ordenables. Si el
  scan todavía está `running`, la tabla puede estar parcialmente
  poblada — las herramientas del pipeline corren secuencialmente e
  ingresan sus resultados a medida que terminan.
- **Reportes**: cuatro botones (**Generar PDF/HTML/MARKDOWN/JSON**) que
  llaman a `POST /scans/{id}/reports?format=...` y agregan el reporte
  recién generado a la lista de abajo, cada uno con un link de descarga
  con fecha de generación. La descarga no es un link directo — el
  dashboard hace la request autenticada y convierte la respuesta en un
  archivo descargable (necesario porque la descarga requiere el header
  `X-API-Key`; ver [`docs/security.md`](security.md)).

## Usar la API directamente

El Backend es la única superficie pública de la API — todo lo que hace
el dashboard pasa por ella. Documentación interactiva (Swagger UI) en:

```
http://localhost:8000/docs
```

Cada request (salvo `/health`) necesita el header `X-API-Key` con el
valor de `BACKEND_API_KEY` (`.env`). Ejemplo:

```bash
curl http://localhost:8000/targets \
  -H "X-API-Key: change_me_local_dev_only"
```

Referencia completa de endpoints, agrupados por módulo: ver la sección
"Endpoints" en [`backend/README.md`](../backend/README.md). Para un
recorrido paso a paso con `curl` desde registrar un target hasta bajar
un PDF, ver la [guía de demostración](demo.md).

## Formatos de reporte

Los cuatro formatos (`pdf`, `html`, `markdown`, `json`) se generan a
partir de los mismos datos (target, scan, findings) — la elección es
solo de presentación:

- **PDF**: para compartir o archivar: el formato standalone más
  portable.
- **HTML**: igual contenido que el PDF, para verlo en el navegador sin
  descargar nada.
- **Markdown**: para pegar en un issue, PR o documento versionado.
- **JSON**: para consumir los datos crudos desde otra herramienta o
  script.

El pipeline automatizado (Módulo 6, etapa 11) genera automáticamente un
PDF al finalizar y lo envía por mail (etapa 12, si está configurado — ver
[`docs/installation.md`](installation.md#6-opcional-configurar-el-envío-de-mails)).
Los otros tres formatos son bajo demanda, desde el dashboard o llamando
al endpoint directamente.

## Alcance de lo que se puede escanear

Solo los hosts del laboratorio local incluido (Juice Shop, DVWA por
defecto) — nunca sistemas de terceros. Ver
[`docs/lab.md`](lab.md) para el alcance legal completo y
[`docs/architecture.md`](architecture.md) para cómo se aplica la
whitelist a nivel de arquitectura.
