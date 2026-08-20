# Modelo de seguridad — Módulo 9

Este documento describe el modelo de autenticación elegido para VulnScan
Platform y, sobre todo, sus límites conocidos: qué protege, qué no
protege, y qué habría que cambiar si el alcance del proyecto creciera más
allá de un laboratorio local de un solo operador.

## Qué existe hoy

> **Nota sobre la auditoría externa (C-14):** el borrador de tesis que la
> auditoría revisó describía la API del Backend como "sin ningún control
> de acceso" (tabla `users` sin consumir, §11.7). Esa descripción
> corresponde a un estado del proyecto anterior al Módulo 9 — la
> autenticación por API key descrita en esta página ya existe en el
> código y está verificada funcionando (401 sin `X-API-Key`, 200 con la
> key correcta). El hallazgo C-14 está resuelto en la implementación; lo
> que falta es que el texto de la tesis lo refleje (ver
> `docs/audit-corrections/`).

Dos niveles de secreto compartido, ninguno de los dos es un sistema de
usuarios:

- **`BACKEND_API_KEY`** — protege el Backend (todo excepto `/health`).
  Lo manda el Frontend (header `X-API-Key`) y n8n al llamar al Backend.
- **`INTERNAL_API_KEY`** — protege Scanner y Reports (todo excepto
  `/health`), que además dejaron de publicar su puerto al host. Lo mandan
  n8n (al llamar a Scanner) y el Backend (al llamar a Reports), header
  `X-Internal-Token`.
- **`N8N_WEBHOOK_SECRET`** — protege el Webhook Trigger de n8n
  (`POST /webhook/vulnscan-pipeline`), la única entrada externa al
  workflow. Lo manda el Backend (header `X-Webhook-Secret`, ver
  `backend/app/services/pipeline_service.py`); el nodo `Check Webhook
  Secret`, ubicado inmediatamente después del trigger, lo compara contra
  `$env.N8N_WEBHOOK_SECRET` y responde 401 (`Respond Unauthorized`) antes
  de que se cree ningún hallazgo si no matchea, o 200 (`Respond OK`) y
  continúa el pipeline en paralelo si matchea (ver
  `n8n/workflows/vulnscan-pipeline.json`, `n8n/README.md`). Verificado en
  vivo: sin el header o con un valor incorrecto, 401; con el valor
  correcto, 200 y el pipeline corre de punta a punta con normalidad.
  Antes de esto (Recomendación #7,
  `docs/independent-evaluation-report.md`), el webhook aceptaba
  cualquier `POST` con un `scan_id`/`target_id` con forma válida sin
  ninguna verificación — el basic auth de n8n protege el editor/API,
  nunca cubrió las URLs de webhook.

Ver `backend/app/security.py`, `scanner/app/security.py` y
`reports/app/security.py` para la implementación de los dos primeros
(misma forma en los tres: `secrets.compare_digest` contra el valor
esperado, 401 si no matchea o falta el header). El tercero se valida
dentro del propio workflow de n8n, no en un Backend — ver más arriba.

## Defensa en profundidad: whitelist de hosts de laboratorio

Además de las dos API keys de arriba, hay un tercer control relevante que
no es de autenticación sino de autorización de *objetivo*: qué hosts
puede escanear la plataforma. Hasta la corrección de este hallazgo
(auditoría externa, C-13), esa whitelist solo se aplicaba en el Backend
al registrar un target (`POST /targets`) — pero el Backend no es el
componente con ruta de red hacia el laboratorio; el Scanner Service sí lo
es (`lab-network`), y no validaba nada por su cuenta. Un chequeo único en
un servicio que ni siquiera puede alcanzar el laboratorio no es defensa
en profundidad real, aunque el proyecto la describiera así.

Ahora la whitelist (`BACKEND_ALLOWED_LAB_HOSTS`/`SCANNER_ALLOWED_LAB_HOSTS`,
mismo valor en `.env`, dos puntos de código independientes) se aplica en:

1. **El Backend**, al registrar un target — administrativo, una vez.
2. **El Scanner Service**, en cada `POST /scan/{tool_name}` — operacional,
   hasta 5 veces por pipeline, y es el punto que efectivamente importa
   porque es el único con ruta de red al laboratorio.

Ver `scanner/app/config.py`/`scanner/app/routers/scans.py` para la
implementación, y `docs/lab.md`/`docs/architecture.md` para el resto del
modelo de red.

## Sesgo conocido en la escala de severidad

La escala unificada (`info`/`low`/`medium`/`high`/`critical`,
`backend/app/normalization/severity.py`) no trata a las tres herramientas
de detección de vulnerabilidades por igual, y esto no está impulsado por
el objetivo analizado sino por la política de mapeo de cada una:

- **ZAP** aporta un `riskcode` numérico de 0 a 3, mapeado directamente a
  `info`/`low`/`medium`/`high` (`_ZAP_RISKCODE` en `severity.py`) — su
  escala tiene 4 niveles, la del sistema tiene 5, así que **ningún
  hallazgo de ZAP puede llegar nunca a `critical`**.
- **Nikto** no reporta severidad ni CVSS en su salida, así que todos sus
  hallazgos se fuerzan, sin excepción, a `low`
  (`nikto_normalizer.py`) — no es una medición, es una decisión
  conservadora de diseño para no inventar una señal que la herramienta
  no da.
- **Nuclei** es la única herramienta cuya etiqueta nativa se adopta
  directamente y puede llegar a `critical`.

En la práctica, esto significa que la distribución de severidad de un
escaneo es en buena medida un artefacto de qué herramienta detectó cada
hallazgo, no solo del objetivo analizado. Cualquier reporte de
distribución de severidad (incluida la campaña de medición del
`docs/audit-corrections/`) debe desagregarse por herramienta además de
mostrar el agregado, para que este sesgo sea visible en los datos en vez
de quedar oculto en un solo número.

## Limitaciones conocidas (a propósito, para revisar más adelante si hace falta)

- **La `BACKEND_API_KEY` queda visible en el bundle JS del Frontend.**
  Vite la inlinea en build time (`VITE_API_KEY`); cualquiera que abra el
  dashboard puede leerla con "ver código fuente" o las DevTools del
  navegador. No es un secreto real frente a un atacante con acceso al
  Frontend — solo evita el uso casual sin credenciales por parte de
  alguien que ni siquiera abrió el dashboard.
- **No hay noción de usuarios.** No se puede saber *quién* disparó un
  scan concreto o generó un reporte concreto, ni revocar acceso a una
  sola persona sin rotar la key para todos los que la usan (Frontend y
  n8n).
- **No hay rate limiting ni protección de fuerza bruta** sobre el header
  `X-API-Key` / `X-Internal-Token`. Un intento de fuerza bruta contra la
  key no queda ni detectado ni frenado a este nivel.
- **Rotar la key no es instantáneo.** Como `BACKEND_API_KEY` está
  inlineada en el bundle del Frontend en build time, rotarla implica
  reconfigurar `.env` **y rebuildear** el contenedor `frontend`, no solo
  cambiar una variable de entorno en caliente.
- **No hay TLS/HTTPS en ningún servicio.** Todo el tráfico interno
  (incluidas ambas keys) viaja en texto plano dentro de `app-network`.
  Razonable para un laboratorio que corre en `localhost`; no lo sería si
  esto se expusiera fuera de la máquina de desarrollo.
- **La descarga de reportes ya no es un link directo.** Como un `<a href>`
  no puede llevar headers custom, `GET /reports/{id}/download` pasó a
  requerir `X-API-Key` — el Frontend lo resuelve haciendo `fetch` con el
  header y convirtiendo la respuesta en un blob descargable
  (`frontend/src/api/client.ts::downloadFile`/`triggerDownload`). Es un
  detalle de implementación, no una debilidad, pero vale documentarlo
  porque cambia el patrón esperado si se agrega un nuevo endpoint de
  descarga en el futuro.

## Decisiones descartadas y por qué

- **Login real (usuario/contraseña) + JWT**: se evaluó explícitamente
  (ver historial del Módulo 9) y se descartó por alcance — hubiera
  requerido una tabla `users`, endpoints de login/logout, manejo de
  expiración de sesión, y una pantalla de login en el Frontend. Para un
  laboratorio de un solo operador, el costo no se justificaba frente al
  riesgo real que mitiga una API key compartida.
- **Credentials nativas de n8n** para los headers de los nodos HTTP en
  vez de `$env.*`: se descartó porque requeriría un paso manual de
  configuración en la UI de n8n antes de poder levantar el pipeline,
  rompiendo la premisa de "todo levanta con `docker compose up -d`, sin
  pasos manuales" que sostiene el resto del proyecto.

## Camino de mejora futura, si hace falta

Si en algún momento este proyecto necesita distinguir usuarios reales,
revocar acceso individual, o exponerse fuera de `localhost`:

1. Reemplazar la API key compartida por login (usuario/contraseña) + JWT
   de corta duración, con refresh token.
2. Agregar rate limiting a nivel de gateway/reverse proxy (ej. Nginx
   `limit_req`) delante del Backend.
3. Poner TLS delante de todos los servicios expuestos (al menos
   Frontend/Backend), vía un reverse proxy con certificados (Let's
   Encrypt en un deployment real, certificados self-signed para
   desarrollo).
4. Auditoría: registrar qué usuario disparó cada scan/reporte, no solo
   `triggered_by: "n8n-pipeline"` como hoy.
