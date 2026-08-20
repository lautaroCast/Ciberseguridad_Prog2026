# Reporte de Auditoría Propio — VulnScan Platform

**Fecha:** 2026-08-15 (auditoría) · **Remediación aplicada:** 2026-08-16
**Autor:** Auditoría independiente asistida por IA (Claude), a pedido de Lautaro Castillo
**Rol asumido:** evaluador de tesis (Tecnicatura Universitaria en Programación, UTN FRM)
**Rama auditada:** `audit-tiers-1-8`

> **Estado: todos los hallazgos de este reporte fueron corregidos y verificados** (tests re-ejecutados contra las imágenes reconstruidas, migración aplicada contra la base real, workflow de n8n reimportado, pipeline real corrido end-to-end). Ver el plan de remediación en `docs/self-audit-report.md#7-remediación-aplicada-2026-08-16` al final de este archivo para el detalle de qué se hizo y cómo se verificó cada ítem. Los hallazgos abajo se dejan con su texto original (para que el reporte siga siendo un registro fiel de lo que se encontró) y una nota **RESUELTO** indicando la corrección aplicada.

## 1. Alcance y metodología

Esta auditoría cubre **documento + código real**, a diferencia de la auditoría externa original (`Auditoria_Tesis_VulnScan_Racconto_Castillo.pdf`), que explícitamente no pudo revisar el código fuente. El objetivo es complementar esa auditoría, no repetirla: los 18 hallazgos críticos (C-01 a C-18) y los hallazgos medios/bajos de esa ronda ya están corregidos y documentados en `docs/audit-corrections/`.

Se revisaron:

- **El documento final** (`Informe Tesis ... (2)_corregido.docx`): consistencia interna, cifras cruzadas, Resumen, seis secciones de metodología, anexos nuevos (F-J), estructura y formato.
- **El código fuente completo**, mediante cuatro auditorías independientes en paralelo:
  1. Backend + Base de datos
  2. Scanner Service + Reports Service
  3. Suite de tests (backend, scanner, reports, E2E)
  4. Frontend + workflow de n8n + `docker-compose.yml`/Dockerfiles

Cada hallazgo de código cita archivo y línea, y fue verificado por lectura directa del código (no inferido de la documentación). Los dos hallazgos críticos de código se re-verificaron manualmente antes de incluirse en este reporte.

No se asumió nada sobre partes no observables directamente (por ejemplo, si CI ejecuta los tests dentro de Docker) — donde no pudo verificarse, se indica explícitamente como tal.

## 2. Aspectos positivos (resumen breve)

- **Arquitectura honesta, no solo aspiracional.** El patrón adaptador (Scanner), el patrón registro (normalización) y la separación routers→services→repositories (Backend) están realmente implementados, no solo descriptos en la documentación.
- **Seguridad con evidencia real, no solo afirmada.** El escape HTML/PDF automático tiene un test de regresión que prueba un `<script>` literal escapado; la protección contra path traversal en la *descarga* de reportes también tiene su propio test de regresión bien construido. `docs/security.md` es inusualmente franco sobre las limitaciones reales del sistema (sin TLS, sin rate limiting, API key visible en el bundle del frontend).
- **Sin inyección SQL ni `shell=True`** en ningún punto del código (verificado por grep), y sin superficie XSS en el frontend (ningún `dangerouslySetInnerHTML`/`innerHTML`/`eval`).
- **Ingesta transaccional correcta**: `scan_task_service.py` persiste `ScanTask` + hallazgos normalizados en una sola transacción con `flush()`, cumpliendo la garantía documentada de "nunca un resultado parcial".
- **Tests existentes de calidad real, no humo**: los tests de normalización verifican valores concretos de campos, no solo "no explota"; `test_scan_runner.py` cubre reglas de negocio sutiles (código de salida no-cero con hallazgos = éxito); `scripts/integration_test.py` es un E2E genuino contra el stack real, con verificación de bytes de los 4 formatos de reporte.
- **El documento en su estado actual** no tiene placeholders `[COMPLETAR]`, tiene TOC real de Word, 14 tablas rotuladas con fuente, lista de acrónimos, y bibliografía verificada (DOIs contra Crossref).

## 3. Hallazgos — Documento

| # | Severidad | Observación |
|---|---|---|
| D-1 | Media | **RESUELTO.** El Resumen no menciona el hallazgo empírico más interesante de la tesis: el recall de alta confianza contra el catálogo de DVWA es 0% (Sección 12.5), causado por que WhatWeb detecta la redirección 302 a `login.php` en vez del contenido protegido. Este es justamente el tipo de resultado negativo honesto que fortalece una tesis (evita "resultados perfectos" poco creíbles) pero, al no estar en el Resumen, un lector que solo lea esa sección se lleva una impresión más optimista que la real. → Se agregó una oración al final del último párrafo del Resumen y del Abstract, referenciando la Sección 12.5. |
| D-2 | Baja/Observación | **Evaluado, sin cambios (decisión del usuario).** El documento creció sustancialmente con los cinco anexos nuevos (F-J: `docker-compose.yml` completo, extracto de workflow JSON, salida cruda de WhatWeb, ejemplos de reportes, `.env.example` completo). Es material honesto y verificable (no inventado), pero es mucho volumen de código pegado para una tesis de nivel Tecnicatura. El usuario decidió explícitamente dejarlo como está. |
| D-3 | Abierta (no es un error) | **Sigue abierta, fuera de alcance de este remedio.** A-14 (declarar/publicar la URL del repositorio) sigue pendiente, a la espera de que el usuario decida sobre la visibilidad del repo. M-11 (declaración de originalidad/autoría) sigue bloqueada porque no se cuenta con la plantilla institucional de UTN FRM — no debe inventarse ese texto. |

No se encontraron inconsistencias numéricas nuevas (259,06 s / 4,1 % / 20,6 % / 0,85 s se mantienen coherentes entre Resumen, Sección 12 y tablas), ni problemas de estilo heading/TOC, ni fragmentos de oración fuera de orden en la revisión sección por sección ya realizada en tramos anteriores.

## 4. Hallazgos — Código

Los hallazgos con severidad **Crítica** y **Alta** fueron re-verificados por lectura directa del archivo citado durante esta síntesis (no solo tomados del reporte del subagente).

### 4.1 Crítico

**[COD-1] Path traversal / escritura arbitraria de archivos en la generación de reportes — `reports/app/services/report_generator.py:25`** — **RESUELTO**

```python
filename = f"{data.scan.id}.{_EXTENSIONS[data.format]}"
path = output_dir / filename
```

`scan.id` es un `str` sin restricción de formato (`reports/app/schemas/report.py`), y se interpola directo en una ruta de archivo **sin `.resolve()` ni verificación de que el resultado siga dentro de `output_dir`**. Esto contrasta directamente con el endpoint de *descarga* del mismo archivo (`reports/app/routers/reports.py:44-51`), que sí hace ese chequeo correctamente y hasta lo comenta explícitamente. Verificado por lectura directa: confirmado, el endpoint de escritura no tiene ningún guardia equivalente.

En el flujo documentado, `scan.id` siempre viene de un UUID generado por el Backend, así que no es explotable hoy por un usuario externo. Pero el propio Reports Service se declara "stateless, confía en que el Backend ya validó todo" — es decir, esta es la única línea de defensa ante un Backend comprometido, una `INTERNAL_API_KEY` filtrada, o un futuro caller. El equipo demostró saber prevenir exactamente este patrón (la descarga lo prueba) pero no lo aplicó de forma simétrica en la escritura. No hay ningún test que ejercite un `scan.id` malicioso.

→ **Fix**: se agregó el mismo guardia (`resolve()` + verificación `output_dir not in path.parents`) a `generate()`, con una excepción nueva (`InvalidReportRequestError`, 400) registrada en `main.py`. Tests de regresión en `test_report_generator.py` y `test_reports.py`.

### 4.2 Alto

**[COD-2] El pipeline de n8n no tiene ningún camino que marque un scan como `failed` — riesgo estructural de confiabilidad** — **RESUELTO**

`n8n/workflows/vulnscan-pipeline.json`, nodo `Select HTTP Port` (línea ~289) combinado con `Complete Scan` (líneas ~542-568). Cuando no se encuentra ningún puerto HTTP abierto (`services.length === 0`), el nodo de código retorna `[]` y toda la cadena posterior nunca se ejecuta — incluyendo `Complete Scan`, el único nodo de todo el workflow que llama a `POST /scans/{id}/complete`. El mismo bloqueo silencioso ocurre si `Scan: Nmap` falla (tiene `continueOnFail: true`, así que `Select HTTP Port` termina leyendo un objeto de error en vez de `{parsed: [...]}`).

Se verificó que el Backend **sí soporta** `status: "failed"` en ese mismo endpoint (`backend/app/routers/scans.py`) — la capacidad existe, pero nada en el workflow de n8n la invoca ante una falla intermedia. Consecuencia directa para el usuario: `ScanDetailPage.tsx` en el frontend hace polling cada 2 segundos mientras el estado no sea terminal, y no tiene ningún timeout — un scan bloqueado por esto queda "corriendo" para siempre en la UI, sin que se muestre ningún error. Esto no es un caso hipotético: ocurre con un target sin puerto HTTP abierto o con un Nmap que falla, ambos escenarios plausibles dentro del propio laboratorio.

→ **Fix**: `Select HTTP Port` ahora marca `no_http_service: true` en vez de devolver `[]` (cubre tanto "sin puerto" como "Nmap falló", ya que ambos casos colapsan a `services=[]`). Un nodo `IF: No HTTP Service Found` nuevo bifurca hacia un nodo `Mark Scan Failed - Sin Puerto HTTP` que llama a `POST /scans/{id}/complete` con `status: "failed"` y un `error_message` explicativo. Workflow reimportado y reactivado en el n8n real (`n8n import:workflow` + `update:workflow --active=true` + restart). Verificado en vivo: un pipeline real disparado contra `dvwa-demo` después del cambio completó normalmente de punta a punta (confirma que la rama "servicio encontrado" del nuevo nodo IF no rompió el camino feliz). No fue posible fabricar en vivo el escenario "sin puerto HTTP" porque los dos únicos hosts en la whitelist del laboratorio (`juice-shop`, `dvwa`) son aplicaciones web reales con puerto abierto — la rama de fallo se verificó por inspección estática del grafo de nodos/conexiones y por la exitosa reimportación (que valida la estructura del JSON).

**[COD-3] Archivo temporal huérfano en timeout para adaptadores que usan archivo de salida (Nikto, ZAP) — `scanner/app/services/scan_runner.py:45-71`** — **RESUELTO**

Cuando `subprocess.run(..., timeout=timeout)` lanza `TimeoutExpired`, la función retorna antes de llegar al bloque de limpieza de archivo temporal, que además está explícitamente condicionado a `not adapter.uses_output_file` — es decir, se salta la limpieza justo para los adaptadores que la necesitan. Dado que ZAP está documentado como "la herramienta más lenta del pipeline" y la más propensa a alcanzar `SCANNER_MAX_TIMEOUT_SECONDS`, este es un escenario realista, no hipotético. El único test de timeout existente usa Nmap (que no usa archivo de salida), así que esta fuga nunca se ejerce en los tests.

*Precisión encontrada durante la remediación*: el bloque `finally` original era, en la práctica, código muerto — `output_path` solo es truthy cuando `adapter.uses_output_file` es `True`, así que `not adapter.uses_output_file` daba siempre `False` y el `unlink` nunca corría, para ningún adaptador, ni siquiera en el camino de éxito (donde la limpieza real ocurre en otro bloque, más abajo).

→ **Fix**: se movió la limpieza a los dos bloques `except` (`TimeoutExpired`, `FileNotFoundError`) explícitamente, y se eliminó el `finally`. Test de regresión nuevo simulando un archivo parcial escrito antes del timeout.

**[COD-4] Bug de datos confirmado: el normalizador de ZAP mezcla `solution` con `evidence` — `backend/app/normalization/zap_normalizer.py:28`** — **RESUELTO**

```python
evidence=alert.get("solution")
```

El JSON de ZAP tiene un campo `solution` (texto de remediación) y un concepto distinto de evidencia anidado en `instances[].evidence`. El normalizador etiqueta el texto de remediación como si fuera evidencia y nunca extrae la evidencia real. **Todo hallazgo originado en ZAP tiene el campo `findings.evidence` semánticamente incorrecto en la base de datos.** Los tests de normalización no detectan esto porque los fixtures de prueba nunca incluyen un campo `solution`.

→ **Fix**: `evidence` ahora se construye uniendo el `evidence` de cada `instances[]` (join con `"; "`), manteniendo un `FindingData` por alerta (decisión: no cambiar la cardinalidad actual). 3 tests nuevos, incluida la regresión explícita de que `solution` nunca termina en `evidence`.

**[COD-5] Riesgo de inyección de argumentos vía `target` en Nmap — `scanner/app/adapters/nmap_adapter.py:22`** — **RESUELTO**

`command.append(target)` agrega el target como argv final crudo. Los adaptadores HTTP (WhatWeb, Nikto, Nuclei, ZAP) son inmunes porque incrustan `target` dentro de una cadena mayor (`f"{scheme}://{target}:{port}"`) que sigue a un flag; Nmap es el único que lo pasa suelto. Un valor de `target` que empiece con `-` (p. ej. `--script=/tmp/evil.nse`) sería interpretado por nmap como un flag, no como un host. Solo explotable si algo aguas arriba del Scanner Service reenvía un valor no confiable — el Scanner no valida nada por su cuenta más allá de longitud.

→ **Fix**: `field_validator` nuevo en `ScanRequest.target` (`scanner/app/schemas/scan.py`) que rechaza cualquier valor que empiece con `-` — aplica a los 5 adaptadores por igual, no solo a Nmap. Tests nuevos en `scanner/tests/schemas/test_scan.py`.

**[COD-6] Sin cobertura de tests en los tres módulos de mayor riesgo del backend** — **RESUELTO**

`scan_task_service.py` (ingesta transaccional — "el core del Módulo 5" según su propio docstring), `pipeline_service.py` (el único punto de contacto con n8n, incluyendo la rama que marca un scan como `failed`), y el router completo de `reports.py` (incluida la lógica de proxy de descarga con traducción de 404) **tienen cero tests**, ni unitarios ni de router. Esto es exactamente el código donde vive COD-1 y COD-2 — los módulos de integración entre servicios, no la lógica de negocio aislada. `scripts/integration_test.py` es el único punto que los ejerce, y solo corre manualmente (`workflow_dispatch`), nunca en cada push/PR.

→ **Fix**: `test_scan_task_service.py` (6 tests: camino feliz con servicios/findings reales, sin `parsed`, status `failed`, fallo de normalizador no propaga, scan desconocido), `test_pipeline_service.py` (4 tests: éxito con payload verificado, fallo marca `FAILED`, target inactivo, target desconocido), `test_reports.py` (8 tests: create/list/download felices, errores upstream, 404, regresión COD-11) — todos nuevos.

**[COD-7] Documentación de n8n contradice la implementación real (dos casos)** — **RESUELTO**

`n8n/README.md` afirma que ZAP corre "sin límite artificial", pero el nodo `Scan: ZAP` tiene un timeout HTTP de 600000 ms (10 min) hardcodeado — y ese valor es *menor* que el límite duro del propio scanner (`SCANNER_MAX_TIMEOUT_SECONDS=900`, 15 min), por lo que n8n puede matar un ZAP que aún estaba dentro de su propio límite configurado. Además, el README describe una implementación de `Resolve Pipeline Context` (`try/catch $('NodeName')`) que el comentario del propio nodo dice haber reemplazado por ser "frágil" — el README documenta una versión abandonada por bug.

→ **Fix**: el timeout de `Scan: ZAP` ahora es una expresión n8n (`(Number($env.SCANNER_MAX_TIMEOUT_SECONDS) || 900) * 1000 + 30000`) atada al mismo valor que usa el scanner, en vez de un número fijo independiente — se agregó `SCANNER_MAX_TIMEOUT_SECONDS` a las variables de entorno del contenedor `n8n` en `docker-compose.yml` para que la expresión resuelva el valor real. `n8n/README.md` corregido en ambos puntos (mecanismo real de `Resolve Pipeline Context`, y explicación del nuevo timeout dinámico de ZAP).

### 4.3 Medio

- ~~**[COD-8]** El Scanner Service no valida el target de forma independiente...~~ **Falso positivo — corregido 2026-08-15.** Re-verificado por lectura directa: `scanner/app/routers/scans.py:34` (`if payload.target not in settings.allowed_lab_hosts: raise HTTPException(422, ...)`) ya enforcea la whitelist de forma independiente en el propio Scanner Service, con un comentario explícito documentando que es el segundo punto de defensa en profundidad (corrección C-13, ya aplicada antes de esta auditoría). El subagente que originó este hallazgo solo revisó `scanner/app/schemas/scan.py` y `scan_runner.py`, no `scanner/app/routers/scans.py`. No se requiere ningún cambio de código.
- **[COD-9]** **RESUELTO.** `Target.is_active` se puede setear vía `PATCH /targets/{id}` pero `create_scan`/`trigger_pipeline` nunca lo verifican — un target marcado inactivo igual puede ser escaneado. → Nuevo `get_active_target_or_raise` (usado solo en `create_scan`/`trigger_pipeline`, no en lecturas) y `TargetInactiveError` (409). Tests nuevos en ambos servicios.
- **[COD-10]** **RESUELTO (alcance: documentación, decisión confirmada con el usuario).** `Finding.service_id` está documentado en el diagrama ER (`docs/database.md`) como una relación real ("asociado a servicio, opcional"), pero ningún código del Backend lo popula jamás — es una funcionalidad documentada que no existe en la implementación. Implementar la relación completa (host+puerto matching) hubiese requerido tocar los 5 normalizadores, el schema de ingesta y el payload de n8n — desproporcionado para severidad Media y con riesgo de concentrarse en el mismo archivo que COD-2. → `docs/database.md` corregido para describir la columna como existente pero no poblada, con una nota explicativa.
- **[COD-11]** **RESUELTO.** Header injection de bajo riesgo: `backend/app/routers/reports.py` interpola `report.file_path` (viene de la respuesta JSON del Reports Service) directo en `Content-Disposition` sin sanitizar. → Se valida `file_path` contra `^[A-Za-z0-9._-]+$` antes de usarlo en la URL upstream y en el header; `InvalidReportFilePathError` (500) si no matchea. Test de regresión.
- **[COD-12]** **RESUELTO.** Frontend: `FindingRead.description` y `FindingRead.evidence` — el campo más importante de un hallazgo de seguridad — se obtienen de la API pero nunca se muestran en ninguna pantalla (`ScanDetailPage.tsx`). Es una función incompleta, no un placeholder: el modelo de datos y la llamada ya existen, falta solo la UI. → Fila expandible al hacer click en el título de un finding, mostrando descripción y evidencia. Tests de componente (vitest + Testing Library) verificando que el detalle está oculto por defecto y aparece al expandir.
- **[COD-13]** **RESUELTO.** Sin índices en varias foreign keys (`scans.target_id`, `technologies.scan_id`, `reports.scan_id`, `findings.scan_task_id`, `cve_references.finding_id`) — sin impacto a escala de laboratorio, pero un problema real a medida que crece el historial de escaneos. → Migración Alembic nueva (`5857d2b759ae`) + `Index(...)` agregado a los 5 modelos SQLAlchemy correspondientes. Aplicada y verificada contra la base Postgres real (`\di ix_*` confirma los 5 índices nuevos).
- **[COD-14]** **RESUELTO.** Inconsistencia de endurecimiento de contenedores: `backend` corre como usuario no-root igual que `reports`, pero a diferencia de `reports` no tiene `cap_drop: [ALL]` / `security_opt: [no-new-privileges:true]` / `read_only: true` en `docker-compose.yml`, pese a la misma justificación ("no necesita binarios ni capacidades especiales"). → Se agregó `cap_drop: [ALL]` + `security_opt: [no-new-privileges:true]` a `backend` (sin `read_only`/`tmpfs`, cuya factibilidad no está verificada para este servicio). Confirmado que el contenedor sigue healthy con las capacidades restringidas.
- **[COD-15]** **RESUELTO.** `db` (Postgres) publica su puerto directo al host (`docker-compose.yml`) sin ningún comentario que lo justifique, a diferencia de `scanner`/`reports`, que explícitamente documentan por qué *no* publican el suyo — contradice el propio principio de exposición mínima que el proyecto aplica en todos los demás servicios. → Se agregó un comentario explicando que es un trade-off deliberado (acceso local de desarrollo vía psql/DBeaver), no un descuido; se mantuvo el puerto publicado.
- **[COD-16]** **RESUELTO.** Sin límite de tamaño en `POST /scans/{scan_id}/tasks` (`raw_output`/`parsed`); combinado con la ausencia de rate limiting ya reconocida en `docs/security.md`, una API key filtrada permite agotamiento de almacenamiento sin límite. → `max_length` agregado a `command` (2000), `raw_output` (5.000.000 caracteres) y `error_message` (5000) en `ScanTaskIngest`.

### 4.4 Bajo / Nitpick

- **RESUELTO.** Renderer Markdown no escapa HTML — correcto para el `.md` en sí, pero si algún día se renderiza a HTML río abajo, un título de hallazgo malicioso (viniendo de una herramienta de escaneo contra un target deliberadamente vulnerable) se vuelve XSS almacenado. Riesgo latente, no vulnerabilidad actual. → Se agregó una advertencia explícita en el docstring de `markdown_renderer.py`, tal como pedía el propio hallazgo (documentar, no cambiar el comportamiento).
- **RESUELTO.** Sin React error boundary en el frontend: cualquier excepción de render sin capturar deja la SPA en blanco sin posibilidad de recuperación. → Componente `ErrorBoundary` nuevo envolviendo la app en `main.tsx`, con mensaje y botón de recarga. Tests de componente.
- **RESUELTO.** El frontend no tenía ningún test automatizado (`*.test.*`), a diferencia de backend/scanner/reports, que sí tienen suites completas — asimetría real de cobertura. → Se agregó `vitest` + `@testing-library/react` + `jsdom` como devDependencies, script `npm test`, y se sumó `npm test` al job `frontend-build` de CI. 5 tests nuevos (`SeverityBadge`, `ErrorBoundary`, `ScanDetailPage`/COD-12).
- El healthcheck de `dvwa` solo verifica que el puerto TCP responda, no que la aplicación sirva contenido válido — documentado como compromiso intencional en el propio comentario, así que no es un hallazgo oculto. **Sin acción** (el propio hallazgo lo marca como no-oculto).
- **RESUELTO.** `BACKEND_SECRET_KEY` está declarado en `.env.example` pero no se usa en ningún lado del código — configuración muerta, probablemente residuo de un diseño de autenticación descartado. → Línea eliminada de `.env.example` (confirmado por grep que no se referencia en ningún otro lugar del repo).
- **RESUELTO.** Tests de adaptadores del scanner cubren JSON válido y vacío, pero no JSON truncado/corrupto (escenario real cuando un proceso es matado por timeout, exactamente el caso de COD-3). → Un test `test_malformed_json_raises`/`test_malformed_jsonl_line_raises` agregado a cada uno de los 4 adaptadores (WhatWeb, Nikto, Nuclei, ZAP).
- **RESUELTO.** `build_command` solo está testeado unitariamente para Nmap; los otros 4 adaptadores (WhatWeb, Nikto, Nuclei, ZAP) no tienen test de construcción de comando, pese a que esa línea de comando es la superficie de ataque real. → 2 tests de `build_command` agregados a cada uno de los 4 adaptadores restantes (8 tests nuevos).

## 5. Evaluación final (al momento de la auditoría, 2026-08-15)

### Puntaje original: **8/10**

**Justificación (histórica, antes de la remediación).** Esta es una tesis de nivel Tecnicatura sólidamente ejecutada: la arquitectura de microservicios está genuinamente implementada (no solo descripta), las afirmaciones de seguridad que el documento hace están mayormente respaldadas por tests de regresión reales (no solo prosa), y la documentación —tras las 12 rondas de correcciones ya aplicadas sobre la auditoría externa original— está en un estado pulido: sin placeholders, con TOC real, tablas rotuladas, bibliografía verificada, y un anexado honesto de artefactos reales del sistema en funcionamiento.

Lo que evitaba un puntaje más alto no era la falta de esfuerzo ni de rigor documental, sino una brecha real entre lo que el documento afirmaba sobre la confiabilidad del sistema y lo que el código efectivamente garantizaba: un bug estructural en el pipeline de n8n (COD-2) que podía dejar un scan bloqueado en estado "running" para siempre sin que la interfaz lo indique, un bug de datos confirmado en el normalizador de ZAP (COD-4), y una asimetría de defensa (COD-1) donde el mismo patrón de seguridad se había aplicado correctamente en un endpoint pero no en su contraparte. A esto se sumaba que exactamente los tres módulos que conectan servicios entre sí —ingesta, disparo del pipeline, y el router de reportes del backend— tenían cero cobertura de tests.

### Puntaje tras la remediación (2026-08-16): **9/10**

Se aplicaron y verificaron **todos** los hallazgos de este reporte (Crítico, Alto, Medio, Bajo/Nitpick, y D-1), no solo los recomendados como prioritarios en la Sección 6 original. El puntaje no llega a 10/10 porque: (a) D-2 (extensión de los anexos F-J) y D-3 (URL del repo, declaración de originalidad) siguen abiertos por decisión/dependencia del usuario, no por trabajo pendiente de esta ronda; y (b) la verificación en vivo de COD-2 quedó parcialmente limitada por el alcance del laboratorio (ningún host de la whitelist permite fabricar el escenario "sin puerto HTTP" para observarlo correr de punta a punta), aunque sí se verificó exhaustivamente por inspección estática, reimportación exitosa en n8n real, y una corrida end-to-end real que ejercita la rama no afectada del mismo nodo.

## 6. Sugerencias / Recomendaciones para subir el puntaje (histórico — ya aplicadas)

**De mayor a menor impacto esperado sobre la evaluación:**

1. ~~Corregir COD-2 (n8n no marca scans como `failed`)~~ — **hecho**.
2. ~~Corregir COD-1 (path traversal en escritura de reportes)~~ — **hecho**.
3. ~~Corregir COD-4 (bug del normalizador de ZAP)~~ — **hecho**.
4. ~~Agregar tests para `scan_task_service.py`, `pipeline_service.py` y el router de `reports.py`~~ — **hecho**.
5. ~~Correr `scripts/integration_test.py` en CI en cada push/PR~~ — **hecho** (`.github/workflows/e2e.yml` ahora dispara en `push`/`pull_request`, no solo manual).
6. ~~Mover el hallazgo del recall 0% contra DVWA al Resumen~~ (D-1) — **hecho**.
7. Opcional/menor: D-2 (acortar anexos F-J) — **evaluado, el usuario decidió dejarlo como está**; ~~corregir las dos contradicciones de `n8n/README.md` (COD-7)~~ — **hecho**; ~~unificar el endurecimiento de contenedores entre `backend` y `reports` (COD-14)~~ — **hecho**.

## 7. Remediación aplicada (2026-08-16)

Ejecutado según plan de remediación aprobado por el usuario (`docs/self-audit-report.md` como fuente, plan detallado fase por fase). Resumen de verificación por servicio, tras reconstruir cada imagen Docker con el código corregido:

| Servicio | Tests antes | Tests después | Resultado |
|---|---|---|---|
| `reports` | 25 | 27 | ✅ todos pasan |
| `scanner` | 39 | 54 | ✅ todos pasan |
| `backend` | 82 | 100 | ✅ todos pasan |
| `frontend` | 0 | 5 (nuevo: vitest) | ✅ todos pasan, `npm run build`/`lint` sin errores |
| `database` (migración) | — | — | ✅ `alembic upgrade head` aplicada contra Postgres real; 5 índices nuevos confirmados con `\di ix_*` |
| `n8n` | — | — | ✅ workflow reimportado y reactivado; pipeline real contra `dvwa-demo` completó de punta a punta tras el cambio |

No se hicieron cambios fuera del alcance de los hallazgos listados arriba (p. ej., no se actualizaron dependencias del frontend con vulnerabilidades conocidas de `npm audit` como `react-router` — quedan fuera de esta auditoría). Los cambios no están commiteados a git todavía; se dejan para revisión y decisión explícita del usuario sobre cómo agruparlos en commits.

## 8. Segunda pasada: code-review automatizado sobre la propia remediación (2026-08-18)

Se corrió `/code-review` contra el diff completo de la Sección 7. Encontró **10 problemas reales introducidos o expuestos por la propia remediación** — todos re-verificados por lectura directa antes de corregir, ninguno descartado como falso positivo. 9 de 10 corregidos y verificados (tests reconstruidos, workflow de n8n reimportado); 1 quedó explícitamente fuera de alcance por decisión de proporcionalidad.

| # | Hallazgo | Fix |
|---|---|---|
| 1 | El guardia de path traversal de COD-1 no rechazaba un `scan.id` con "/" que sigue *dentro* de `output_dir` (p. ej. `"abc/def"`) — pasaba el chequeo y explotaba con un `FileNotFoundError` no manejado al intentar escribir en un subdirectorio inexistente. | Guardia reescrito para exigir que el archivo resuelto sea hijo directo de `output_dir` (`path.parent != output_dir`), no solo "no escapa". Extraído a un helper compartido (`reports/app/paths.py`) usado tanto en escritura como en descarga — también resuelve la duplicación del ítem 10. |
| 2 | El nodo nuevo `Mark Scan Failed - Sin Puerto HTTP` (COD-2) no tenía `continueOnFail`, a diferencia de todo el resto del workflow — si esa llamada fallaba, la ejecución de n8n abortaba y el scan quedaba sin marcar, recreando el bug que el nodo existe para evitar. | `continueOnFail: true` agregado al nodo. |
| 3 | El límite de 5MB en `raw_output` (COD-16) podía rechazar una salida de ZAP legítimamente grande — agravado por el propio join de evidencia de COD-4 — y como `Ingest: ZAP` tiene `continueOnFail: true`, el 422 se tragaba en silencio, dejando el reporte final sin hallazgos de ZAP sin ningún error visible. | Límite subido a 50MB (deja intacta la mitigación de agotamiento de almacenamiento, hace la colisión con salidas reales prácticamente inalcanzable). |
| 4 | El sticky note "Sticky Note - Recon" del propio canvas de n8n seguía describiendo el comportamiento viejo ("retorna cero items, para toda la cadena automáticamente") después de reescribir `Select HTTP Port` — la misma clase de desfasaje doc-vs-código que motivó COD-7, reintroducida en un lugar que no revisé (actualicé `n8n/README.md` pero no los sticky notes del propio workflow). | Contenido del sticky note actualizado para describir el mecanismo real (`IF: No HTTP Service Found` → `Mark Scan Failed`). |
| 5 | `scripts/ground_truth/match_findings.py`: `finding.get('evidence', '')` no cubre el caso de valor `None` (solo clave ausente) — el fix de COD-4 hace que `evidence` sea `None` con más frecuencia, y `str(None).lower()` mete el substring literal `"none"` en el texto usado para el matching por keyword, con riesgo de inflar artificialmente el recall/precision calculado (datos de medición de la tesis). | Cambiado a `finding.get('evidence') or ''` (y lo mismo para `title`/`description` por consistencia). |
| 6 | `backend/app/routers/reports.py`: el regex de COD-11 usaba `^...$` con `.match()`; en Python, `$` matchea también justo antes de un `\n` final, así que un `file_path` terminado en salto de línea pasaba el chequeo. | Cambiado a `fullmatch()` sin anclas (equivalente a `\A...\Z`), que exige consumir la cadena completa. |
| 7 | El chequeo de "es un filename seguro" de COD-11 se aplicaba solo en la *lectura* (`download_report`), no en la *escritura* (`report_service.generate_report`, donde `file_path` se persiste tal cual viene de la respuesta HTTP del Reports Service) — la misma asimetría que enseñó COD-1, no cerrada del todo acá. | Chequeo movido a un helper único (`report_service.is_safe_filename`) reutilizado en escritura (`generate_report`, nueva `InvalidReportFilePathError`) y lectura (router), en vez de dos implementaciones independientes. |
| 8 | `Finding.evidence` (columna `Text`, sin límite) podía crecer sin cota tras el join de instancias de COD-4, a diferencia de `raw_output`/`error_message` que sí recibieron límites explícitos en esta misma remediación. | `_evidence_from_instances` trunca a 10.000 caracteres. |
| 9 | El nuevo validador de `target` (COD-5) cubre el flag-injection vía `target`, pero los valores de `options` (`ports` de Nmap, `severity`/`tags` de Nuclei, `max_time` de Nikto, `aggression` de WhatWeb) siguen sin validar y llegan igual de crudos al argv del subproceso. | **No corregido — gap preexistente, no introducido por esta remediación, y no formaba parte del plan aprobado.** Requeriría validar 4 adaptadores más y decidir el mensaje de error a nivel `scan_runner.execute()` (hoy un `ValueError` ahí no tiene un manejo limpio). Queda propuesto como seguimiento, no aplicado unilateralmente. |
| 10 | La lógica de "es un path seguro" quedó implementada 3 veces de forma independiente (regex en backend, `resolve()+parents` en la escritura y en la descarga del Reports Service). | Resuelto junto con el ítem 1: un solo helper por servicio (`reports/app/paths.py` para Reports Service; `report_service.is_safe_filename` para Backend), sin acoplar los dos servicios entre sí (siguen siendo procesos independientes, sin código compartido). |

Verificación tras estos 9 fixes: `backend` 100→103 tests, `reports` 27→28 tests, todos pasan; workflow de n8n reimportado/reactivado nuevamente. El ítem 9 queda como observación abierta, a decidir con el usuario si se aborda en una ronda futura.
