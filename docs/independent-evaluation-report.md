# Evaluación Independiente de Tesis — VulnScan Platform

**Fecha:** 2026-08-19
**Rol asumido:** evaluador universitario externo, sin vínculo con el desarrollo del proyecto
**Alcance:** documento completo (`Informe Tesis ... (2)_corregido.docx`) + código fuente completo (los 5 servicios, base de datos, workflow de n8n, infraestructura)
**Rama evaluada:** `main` (post-merge, commit `9ad8539`)

## 0. Nota metodológica sobre esta evaluación

Esta es una evaluación **deliberadamente independiente** de `docs/self-audit-report.md`, que ya existe en el repositorio con un puntaje autoasignado de 9/10. Ese reporte tiene un conflicto de interés estructural: fue producido por el mismo asistente que después implementó y verificó sus propias correcciones, y luego volvió a puntuarse a sí mismo tras corregir lo que él mismo había encontrado. Un tribunal real no debería tomar ese 9/10 como una nota independiente — es, en el mejor de los casos, un checklist de calidad interno, no una evaluación externa.

Para esta evaluación: se leyó el documento completo de punta a punta con ojo crítico, sin dar por buena ninguna afirmación de "esto ya se corrigió". Para el código, se lanzaron dos revisiones independientes con instrucciones explícitas de no confiar en comentarios, READMEs ni en `docs/self-audit-report.md` — verificar todo contra el código real, actuando como si el proyecto se viera por primera vez. Ambas revisiones, en paralelo y sin comunicación entre sí, llegaron independientemente a **7,5/10** para sus respectivos alcances, y cada una encontró errores reales que ninguna ronda de auditoría previa (incluida la mía) había detectado. Eso es la señal más confiable de todo este ejercicio: con suficiente escrutinio fresco, siempre aparece algo nuevo — lo cual es normal en cualquier sistema de este tamaño, y es exactamente lo que una evaluación rigurosa debe asumir en vez de descartar.

## 1. Evaluación del documento

### 1.1 Fortalezas

- **Honestidad metodológica genuinamente inusual para el nivel.** El trabajo declara explícitamente qué no se hizo (brazo manual no ejecutado), por qué (sesgo de espera activa, sesgo de familiaridad del operador — Sección 9.9), y qué implica eso para la fuerza probatoria de sus propios resultados (Sección 14.3: "deben interpretarse estrictamente como observaciones descriptivas preliminares, compatibles con las hipótesis planteadas pero sin fuerza probatoria estadística independiente"). Esto es exactamente lo que un evaluador riguroso quiere ver, y es infrecuente encontrarlo con este nivel de explicitud en un trabajo final de Tecnicatura.
- **El hallazgo negativo (0% de recall de alta confianza contra ambos catálogos) se reporta sin maquillar.** Un trabajo más débil lo habría ocultado o minimizado. Aquí se explica la causa (muro de autenticación en DVWA, desalineamiento de vocabulario en Juice Shop) y se reconoce como limitación metodológica legítima, no como fracaso oculto.
- **Bibliografía sólida**: 25 referencias en formato APA 7.ª edición, con DOIs verificables, mezcla apropiada de fuentes académicas (Bridges et al. 2023, Amankwah et al. 2020 — este último evaluando ZAP contra DVWA específicamente, un antecedente muy pertinente) y técnicas. No se detectaron citas fabricadas.
- **Arquitectura y decisiones de ingeniería bien argumentadas**, no solo descritas: la Sección 10.2 explica *por qué* la red de laboratorio no se marca `internal` (compromiso documentado, no descuido), y la Sección 15 defiende con solidez el valor formativo del diseño incluso frente a un componente empírico débil.
- **Consideraciones éticas, análisis de riesgos (ISO/IEC 27005) y limitaciones organizadas en tres categorías** — estructura completa, no un capítulo de relleno.

### 1.2 Debilidades — observaciones que un tribunal exigente señalaría

**D1. El frente del documento promete una comparación que nunca se resuelve donde se promete.**
El Objetivo General (§4.1), el Objetivo Específico N.º 6 (§4.2) y la Pregunta de Investigación N.º 2 (§5) plantean explícitamente una comparación cuantitativa de tiempos contra un proceso manual. Esa comparación se descarta —con buena justificación— recién en la Hipótesis H1 reformulada (§6), la Metodología (§9), los Resultados (§12.2) y las Conclusiones (§16). El problema no es la decisión de no medir el brazo manual (está bien justificada), sino que **§4 y §5 nunca se actualizaron para reflejarlo**: un lector que se detenga en los Objetivos o las Preguntas de Investigación —las primeras secciones sustantivas del trabajo— se lleva la impresión de que esa comparación es un entregable real, y solo se entera de que no lo es muchas páginas después. Es un defecto editorial concreto, no solo de honestidad (que sí está presente aguas abajo): el trabajo no está internamente sincronizado en sus propias secciones de apertura.

**D2. Las hipótesis, tal como quedaron reformuladas, tienen poco riesgo empírico real.**
H1 reformulada mide que el tiempo de orquestación (0,85 s) es marginal frente al tiempo total del pipeline (259,06 s) — 99,7% del tiempo es ejecución de herramientas. Esto es casi una verdad por construcción: en cualquier pipeline automatizado razonablemente bien hecho, el overhead de orquestación va a ser pequeño frente al tiempo de las herramientas que corren dentro. No hace falta una hipótesis para anticiparlo. H2 (hallazgos idénticos en 5 corridas) es, en palabras del propio documento, "casi inevitable" dado un target estático y contenedores fijos. El texto es honesto sobre esto, lo cual es un mérito, pero el resultado neto es que **las dos hipótesis efectivamente contrastadas aportan poca información nueva** — no porque estén mal medidas, sino porque fueron redefinidas hacia una versión de bajo riesgo de la pregunta original, más ambiciosa, que sí se planteó pero nunca se ejecutó.

**D3. El hallazgo central de detección (0% recall de alta confianza) queda sin resolver, no solo sin ocultar.**
Es meritorio que se reporte con transparencia. Pero un proyecto cuyo objetivo general es "la detección, análisis y reporte de vulnerabilidades" termina sin poder demostrar positivamente que detecta, con confianza razonable, las vulnerabilidades documentadas de sus propios dos targets de laboratorio. Las explicaciones ofrecidas (muro de autenticación, desalineamiento de vocabulario del instrumento de medición) son plausibles, pero son explicaciones, no correcciones — el sistema, tal como está desplegado y evaluado, no demuestra la capacidad central que anuncia. Esto pesa más que una simple "limitación" en la evaluación de un tribunal, porque toca la funcionalidad nuclear del proyecto, no un aspecto secundario.

**D4. El marco epistemológico (§9.2) es más ambicioso que la evidencia que el estudio efectivamente produce.**
§9.2 se enmarca explícitamente en el "paradigma positivista-empirista" y afirma que "la validación de soluciones tecnológicas mediante evidencia empírica cuantificable constituye el estándar metodológico de referencia" para el campo. Es una afirmación correcta en general, pero el estudio que sigue —n=5, un solo target principal, sin grupo de control, sin brazo manual— no está a la altura de ese marco declarado. No es un problema de rigor en la ejecución (la Sección 9.9 documenta las amenazas a la validez con seriedad), sino de calibración retórica: el aparato metodológico (diseño cuasi-experimental, variables operacionalizadas, paradigma epistemológico) es más elaborado que lo que los datos recolectados pueden sostener.

**D5. Densidad de prosa.** Pese a las rondas de corrección de estilo ya aplicadas, varios párrafos —particularmente en §9.1, §13 y §15— siguen siendo oraciones muy largas con múltiples incisos entre rayas. No es un defecto grave, pero contrasta con la meta declarada de reducir la longitud oracional media.

### 1.3 Evaluación del documento en sí: **7,5/10**

Un trabajo sólido, honesto y bien estructurado, con una redacción metodológica que supera el estándar típico del nivel. Lo que impide una nota más alta no es falta de esfuerzo sino una brecha real entre lo que las secciones de apertura (Objetivos, Preguntas de Investigación) prometen y lo que el cuerpo del trabajo efectivamente entrega — y el hecho de que el resultado empírico central sobre la capacidad de detección del sistema queda sin resolver positivamente.

## 2. Evaluación del código

Metodología: dos revisiones independientes en paralelo, sin acceso a `docs/self-audit-report.md` ni a los mensajes de commit, instruidas para verificar todo contra el código real. Ambas llegaron a **7,5/10** para sus respectivos alcances. Resumen de los hallazgos más relevantes para un evaluador académico (lista completa con archivo:línea disponible bajo pedido):

### 2.1 Backend + Base de datos + Scanner (7,5/10)

- **Alto** — `scan_task_service.py`: el `try/except` que protege la ingesta solo envuelve la llamada al normalizador, no las escrituras a la base de datos que le siguen en el mismo bloque. Un valor que exceda el ancho de una columna `VARCHAR` (p. ej. `Service.product`/`version`, `String(100)`, sin truncar por ningún normalizador salvo `title`) no se captura como "fallo de normalización" —contradiciendo el objetivo explícito del propio docstring del módulo— y hace perder también el `ScanTask` que se suponía debía sobrevivir independientemente. Además, este bug es **estructuralmente invisible** para la suite de tests actual, que corre contra SQLite en memoria (no aplica límites de `VARCHAR` como Postgres).
- **Alto** — Dos de cinco endpoints CRUD de `targets` (`PATCH`, `DELETE`) sin cobertura de test alguna; detrás de esa falta de cobertura hay un bug real: `TargetUpdate.is_active` está tipado como `bool | None` pero la columna es `NOT NULL` — un `PATCH` con `{"is_active": null}` produce un 500 no manejado en vez de un 422 limpio.
- **Medio** — `Scan.pipeline_run_id` se documenta (en el propio modelo y en `docs/database.md`) como el campo que correlaciona un scan con su ejecución de n8n, pero ningún código lo escribe jamás — a diferencia de `Finding.service_id`, que sí está declarado honestamente como no poblado, este no lo está.
- **Medio** — `complete_scan` no tiene guardas de máquina de estados (se puede volver a completar/fallar un scan ya terminal) y no tiene ningún test.
- **Medio** — `GET /scans/{id}/findings` —el endpoint del que depende la generación de todos los reportes— no tiene ningún test.
- **Medio** — Condición de carrera no atómica en `get_or_create_service` (a diferencia del patrón ya usado para el mismo problema en `target_service.py`, que sí lo resuelve).

### 2.2 Reports + Frontend + n8n + Infraestructura (7,5/10)

- **Alto** — El nodo `Complete Scan` del workflow de n8n es el único de toda la cadena principal sin `continueOnFail: true`. Si esa llamada falla transitoriamente, la ejecución de n8n aborta por completo y el scan queda en `running` para siempre — exactamente el mismo bug que el propio proyecto documenta haber corregido para el caso de "sin puerto HTTP", reaparecido en otro nodo de la misma cadena.
- **Alto** — Los timeouts HTTP de los nodos `Scan: Nmap` y `Scan: WhatWeb` (60s hardcodeados) son más cortos que el timeout por defecto real del Scanner Service (900s) para esas mismas llamadas — la misma clase de bug que el proyecto documenta haber corregido específicamente para ZAP, sin aplicar el mismo razonamiento a Nmap/WhatWeb.
- **Medio** — El Webhook Trigger de n8n no tiene autenticación propia, y el puerto de n8n se publica al host por defecto; `docs/security.md` no menciona esta tercera vía de entrada no protegida (documenta bien las otras dos).
- **Medio** — Escrituras de archivos de reporte no atómicas (riesgo de servir un archivo truncado bajo concurrencia).
- **Medio** — El endurecimiento de contenedores (`read_only`, `cap_drop`) está aplicado de forma completa solo en `reports`; en el resto es parcial — documentado como trabajo incompleto, no como afirmación falsa, pero sigue siendo parcial.
- **Bajo** — Cobertura de tests del frontend real pero delgada (3 archivos de test, cubriendo un componente cada uno).

### 2.3 Evaluación del código en sí: **7,5/10**

Arquitectura genuinamente en capas (no solo descrita), patrones de adaptador y normalización realmente extensibles, seguridad razonada en profundidad (no solo casillas marcadas), tests existentes de calidad real cuando existen. Pero con una cantidad de errores reales, nuevos y no triviales —dos revisiones independientes, cada una encontrando hallazgos "Alto" distintos— que indica que las rondas de auditoría previas, aunque genuinas y bien ejecutadas, no agotaron los problemas del sistema. Eso es normal en software de este tamaño, pero es la razón concreta por la que el código no alcanza una nota más alta.

## 3. Observaciones transversales

- **`docs/self-audit-report.md` como artefacto del propio proyecto.** Su existencia demuestra una práctica de ingeniería madura (autoevaluación, uso de herramientas de code-review, seguimiento de hallazgos hasta su resolución) que un tribunal debería valorar positivamente como evidencia de proceso. Pero su puntaje (9/10) no debería citarse ante un tribunal como si fuera una nota externa: fue generado y luego re-otorgado por la misma parte que hizo las correcciones que ese puntaje premia. Sugerencia: si el documento final hace referencia a este archivo, aclarar explícitamente que es una autoevaluación de proceso, no una evaluación de terceros.
- **El patrón de "misma clase de bug, corregida en un lugar y no en el vecino"** aparece dos veces en esta ronda (el timeout de ZAP corregido pero no el de Nmap/WhatWeb; el `continueOnFail` bien aplicado en la rama de "sin puerto HTTP" pero ausente en `Complete Scan`). Esto sugiere que las correcciones se hicieron reactivamente, hallazgo por hallazgo, sin un paso final de "generalizar este patrón a todos los lugares análogos" — una lección de proceso más que un defecto puntual.
- **La honestidad del documento y la honestidad del código son consistentes entre sí.** Es notable que tanto el documento como el código comparten el mismo rasgo: declaran sus propias limitaciones con más franqueza que el promedio. Eso es una fortaleza real y transversal del proyecto como un todo, más allá de los hallazgos puntuales.

## 4. Puntaje final: **7,5 / 10**

| Dimensión | Puntaje | Peso relativo |
|---|---|---|
| Documento (rigor metodológico, coherencia, redacción) | 7,5/10 | ~45% |
| Código — Backend/DB/Scanner | 7,5/10 | ~30% |
| Código — Reports/Frontend/n8n/Infra | 7,5/10 | ~25% |

Los tres ejes convergen de forma independiente en el mismo número, lo cual da confianza en que 7,5/10 es una nota estable y no un promedio artificial. Es una nota de **trabajo final sólido, por encima del promedio esperado para una Tecnicatura**, con ingeniería real (no solo aspiracional) y una honestidad académica poco común, pero con brechas concretas y verificables: una desalineación entre lo que el frente del documento promete y lo que el cuerpo entrega, un resultado central de detección que queda sin resolver, hipótesis de bajo contenido empírico tras su reformulación, y una cantidad no trivial de errores de código reales que dos revisiones independientes encontraron sin dificultad pese a las múltiples rondas de auditoría previas.

No es una nota de 9 ni de 10: para llegar ahí, el trabajo necesitaría cerrar la brecha de detección (aunque sea parcialmente, con escaneo autenticado como ya se propone en Trabajos Futuros), sincronizar §4-§5 con el alcance real entregado, y una ronda más de revisión de código enfocada específicamente en generalizar los patrones de corrección ya aplicados a sus casos análogos no corregidos.

## 5. Recomendaciones priorizadas

**De mayor a menor impacto esperado sobre una re-evaluación:**

1. **Sincronizar §4.1, §4.2 (objetivo 6) y §5 (pregunta 2) con el alcance realmente entregado.** Es el cambio de menor esfuerzo y mayor impacto en la evaluación: reformular esas tres menciones para que no prometan una comparación que el resto del documento ya aclara que no se hizo, en vez de dejar que el lector lo descubra tarde.
2. **Corregir `Complete Scan` (agregar `continueOnFail`) y los timeouts de `Scan: Nmap`/`Scan: WhatWeb`** — generalizar el patrón ya aplicado correctamente en otros nodos del mismo workflow.
3. **Envolver las escrituras de `scan_task_service.py` en la misma protección transaccional que ya protege la llamada al normalizador**, y truncar los campos `VARCHAR` que hoy no se truncan (`Service.product/version`, `Finding.finding_type/confidence`, `CveReference.cve_id`).
4. **Agregar al menos un test contra Postgres real** (no solo SQLite) para la ruta de ingesta — es la única forma de que la suite pueda detectar la clase de bug del punto 3.
5. **Cerrar la brecha de detección, aunque sea parcialmente**: implementar el escaneo autenticado ya previsto en Trabajos Futuros contra al menos uno de los dos targets de laboratorio, y volver a medir recall — convertiría el hallazgo negativo actual en una demostración positiva de la capacidad central del sistema.
6. **Tests para `PATCH`/`DELETE /targets/{id}`, `POST /scans/{id}/complete`, `GET /scans/{id}/findings`** — cierran los huecos de cobertura más consecuentes encontrados en esta revisión.
7. **Aclarar en `docs/security.md` la ausencia de autenticación en el Webhook Trigger de n8n**, y evaluar si conviene agregarla.

## 6. Remediación aplicada (2026-08-20)

Las 7 recomendaciones de la Sección 5 se aplicaron íntegramente, en el mismo orden de prioridad, con verificación en vivo contra el stack real en cada paso (no solo `pytest`: reconstrucción de cada imagen Docker tocada, reimportación/reactivación del workflow de n8n, y llamadas HTTP reales contra los servicios corriendo).

1. **§4.1/§4.2/§5 del documento sincronizadas.** Se reformuló el Objetivo General, el Objetivo Específico N.º 6 y se anotó la Pregunta de Investigación N.º 2 para no prometer la comparación cronometrada manual-vs-automatizado que nunca se ejecutó, dejándola explícitamente como trabajo futuro (nuevo párrafo en §17). Verificado: integridad de TOC/footer/`updateFields` del `.docx` intacta tras el cambio.
2. **`Complete Scan` con `continueOnFail`, timeouts de `Scan: Nmap`/`Scan: WhatWeb` atados a `$env.SCANNER_MAX_TIMEOUT_SECONDS`.** Mismo patrón ya usado en `Scan: ZAP`, generalizado. Verificado con una corrida real del pipeline de punta a punta.
3. **Escrituras de `scan_task_service.py` protegidas con `db.begin_nested()`** (savepoint), no solo la llamada al normalizador — un fallo ahora hace rollback de las escrituras parciales sin perder el `ScanTask` ya flusheado. **Truncado centralizado en la capa de repositorio** para `Service.product/version`, `Finding.finding_type/confidence`, `CveReference.cve_id`/`cvss_vector`.
4. **Test contra Postgres real agregado** (`backend/tests/services/test_scan_task_service.py::test_ingest_truncates_oversized_service_fields_against_real_postgres`, marcado `@pytest.mark.postgres`), usando un schema descartable vía `schema_translate_map` sobre la misma base — sin esto, el bug del punto 3 habría sido invisible para siempre (SQLite en memoria no aplica límites `VARCHAR`). Corrido y verificado contra la base Postgres real del stack, no simulado.
5. **Escaneo autenticado implementado completo (Nikto + Nuclei + ZAP)** contra DVWA — nuevo helper de login (`scanner/app/services/dvwa_auth.py`), inyección de cookie de sesión por herramienta (`-Add-header` en Nikto, `-H` en Nuclei, add-on Replacer vía `-config` en ZAP), modo opt-in (`options.authenticated=true`, sin cambios en el comportamiento por defecto del workflow de n8n). Remedido recall/precisión/F1 contra el catálogo real de DVWA (Tabla 14 del documento, Anexo E): Nikto pasó de 0 hallazgos parseables a 15 (recall 0,273), ZAP mejoró de recall 0,273 a 0,364, Nuclei sin cambios (0,273 en ambas condiciones). **Con honestidad completa**: el recall de *alta confianza* (CVE exacto o tipo+ubicación) permanece en 0% incluso autenticado — los 38 matches nuevos siguen siendo, igual que antes, de la capa más débil (coincidencia de palabra clave). El muro de acceso era una causa real y ahora corregible, pero no la única limitación identificada en la Sección 1.2/2.1.
6. **Tests agregados para los 3 endpoints sin cobertura** (`PATCH`/`DELETE /targets/{id}`, `POST /scans/{id}/complete`, `GET /scans/{id}/findings`), más un bug real encontrado y corregido al escribirlos: `TargetUpdate.is_active` aceptaba `null` y producía un 500 en vez de un 422 (`bool | None` → `bool` con validación).
7. **Webhook Trigger de n8n autenticado, no solo documentado.** Nuevo secreto compartido `N8N_WEBHOOK_SECRET` (mismo patrón que `BACKEND_API_KEY`/`INTERNAL_API_KEY`): el Backend lo manda como header `X-Webhook-Secret` (`pipeline_service.py`), y un nodo `Check Webhook Secret` (IF, `$env.N8N_WEBHOOK_SECRET`) inmediatamente después del trigger responde 401 (`Respond Unauthorized`) sin ejecutar nada del pipeline si no matchea, o 200 (`Respond OK`) y continúa en paralelo si matchea — sin usar credenciales nativas de n8n (que exigirían un paso manual de configuración en la UI, rompiendo la premisa de `docker compose up -d` sin pasos manuales; ver `docs/security.md`). Verificado en vivo: sin header o con valor incorrecto → 401; con el valor correcto → 200 y el pipeline corre de punta a punta con normalidad. `docs/security.md` actualizado con el mecanismo completo, no solo con la limitación.

**Verificación por servicio** (suites completas corridas dentro de cada contenedor reconstruido):

| Servicio | Tests antes | Tests después | Resultado |
|---|---|---|---|
| `backend` | 103 | 122 | ✅ todos pasan, incluido el nuevo test marcado `postgres` contra la base real |
| `scanner` | 54 | 67 | ✅ todos pasan |
| `reports` | 28 | 28 | ✅ sin cambios en este servicio, suite corrida igual para confirmar que nada se rompió transversalmente |
| `n8n` | — | — | ✅ workflow reimportado y reactivado dos veces (Fase 2, Fase 7); pipeline real contra `dvwa` completó de punta a punta después de cada cambio |

No se hicieron cambios fuera del alcance de las 7 recomendaciones listadas. Los cambios no están commiteados a git todavía; quedan para revisión y decisión explícita del usuario sobre cómo agruparlos en commits (mismo criterio que las rondas de remediación anteriores).

## 7. Seguimiento posterior (2026-08-22)

Tras esta evaluación, se decidió explícitamente **no ejecutar el brazo manual** — no por descartar D2, sino porque el operador disponible (el propio autor) construyó los catálogos de verdad de referencia que la medición usaría, un problema de contaminación más severo que el sesgo de familiaridad ya declarado en §9.9, y esta misma evaluación tampoco lo había priorizado entre sus 7 recomendaciones pese a señalarlo en D2. En su lugar se atacó lo que sí quedaba accionable de esta evaluación: D4 (calibrar §9.2 al alcance real) y D5 (densidad de prosa en §9.1) corregidos; la amenaza de validez externa (§9.9) reforzada con una réplica real de la campaña de medición contra `juice-shop` (4/5 corridas exitosas, orquestación 0,63 s vs. 0,85 s en `dvwa` — mismo orden de magnitud); y varios de los hallazgos "Alto"/"Medio" de §2.1/2.2 que no habían entrado en las 7 recomendaciones (condición de carrera en `get_or_create_service`, `Scan.pipeline_run_id` sin poblar, validación de `options` en los adaptadores, escrituras de reporte no atómicas, hardening de `backend`) — detalle completo en `docs/self-audit-report.md` §9, no duplicado acá.

D3 (0% de recall de alta confianza) sigue sin resolverse — no se intentó nada nuevo sobre eso en esta ronda. Esta réplica contra `juice-shop` expuso además un hallazgo nuevo, no corregido: una condición de carrera real entre el nodo `Generate Report` de n8n y la limpieza de `scripts/measurement_campaign.py` (`docs/self-audit-report.md` §9 tiene el detalle) — evidencia de que, como esta misma evaluación advirtió en su propia Sección 3, sigue apareciendo algo nuevo con cada ronda de escrutinio fresco.

## 8. Segunda evaluación independiente (2026-08-22)

**Nota de conflicto de interés, otra vez explícita**: esta evaluación la generó el mismo asistente que implementó buena parte de las correcciones que evalúa (el seguimiento de §7, más una ronda posterior de fixes al frontend). Es la misma limitación estructural que la Sección 0 ya señaló sobre `docs/self-audit-report.md` — aplica ahora también a este documento. Para mitigarla, se repitió el mismo método: tres revisores de código lanzados en paralelo, **sin acceso a este archivo, a `docs/self-audit-report.md`, a `docs/audit-corrections/`, ni a mensajes de commit**, instruidos a verificar todo contra el código real de `main` (commit `8e10010`) como si lo vieran por primera vez. A diferencia de la primera ronda (dos revisores: Backend+DB+Scanner y Reports+Frontend+n8n+Infra), esta vez el Frontend —que atravesó un rediseño completo desde la evaluación anterior— se evaluó por separado, con su propio revisor.

### 8.1 Documento — releído directamente, no delegado

Se releyeron con ojo crítico las secciones que D1/D4/D5 (Sección 1.2) señalaron, más el Resumen/Abstract:

- **D1 (síntoma: §4/§5 desincronizadas del resto del trabajo) — confirmado resuelto.** §4.1, §4.2 (objetivo 6) y §5 (pregunta 2) ahora declaran explícitamente, en el mismo párrafo que plantea el objetivo/pregunta, que la comparación cronometrada contra el proceso manual no se ejecutó en esta ronda y remiten a §14.2. Ya no hay desincronización entre lo que el frente del documento promete y lo que el cuerpo entrega.
- **D4 (marco epistemológico sobredimensionado) — confirmado resuelto.** §9.2 ahora encuadra explícitamente el paradigma positivista-empirista "a la escala propia de un proyecto de Tecnicatura" y remite a las propias Secciones 9.1/9.8/9.9 sobre tamaño muestral. La calibración retórica que pedía D4 está hecha.
- **D5 (densidad de prosa en §9.1, §13, §15) — parcialmente resuelto.** §9.1 tiene la oración más larga partida en dos. §13 y §15, releídos ahora, **siguen teniendo oraciones largas con incisos entre rayas** (ej. §15, párrafo sobre el paradigma SOAR, y el párrafo sobre la eliminación de tareas manuales) — no se tocaron en esta ronda. No es un defecto grave, pero D5 no está cerrado del todo, solo parcialmente.
- **D2 y D3 no fueron abordados en esta ronda** (decisión explícita, ver §7) y se mantienen sin cambios de fondo: las hipótesis reformuladas siguen teniendo poco riesgo empírico, y el recall de alta confianza sigue en 0%.
- **Consistencia interna**: el commit de referencia declarado en §11.1 y en la intro de Anexos (antes `9ad8539`, ya desactualizado incluso antes de esta ronda) se corrigió a `8e10010`, el HEAD real de `main` tras todos los merges de esta ronda.

**Evaluación del documento: 8/10** (sube de 7,5). Sube porque el defecto editorial más citado por la ronda anterior (D1) está genuinamente resuelto, y D4 también — ambos eran, en palabras de la propia evaluación anterior, "el cambio de menor esfuerzo y mayor impacto". No sube más porque las dos debilidades sustantivas (D2: hipótesis de bajo riesgo empírico; D3: capacidad de detección sin demostrar positivamente) —las que de verdad pesan en un tribunal exigente— siguen intactas, y D5 quedó a mitad de camino.

### 8.2 Código — tres revisores frescos en paralelo, cada uno con su propio alcance

**Backend + Base de datos + Scanner: 8/10.** Hallazgos nuevos, no señalados en ninguna ronda anterior: `technology_repository.create_technology` no trunca `version`/`category`/`confidence` pese a que `finding_repository`/`service_repository` sí truncan sistemáticamente los mismos tipos de campo (inconsistencia real, no solo cosmética); `report_service.generate_report` no valida la forma de la respuesta JSON del Reports Service antes de indexarla, así que una respuesta malformada produce un 500 crudo en vez del 502 traducido que el resto de la función sí produce para fallos upstream; el `auth_cookie` de DVWA se interpola sin validar en el `-config` de ZAP, la única superficie de inyección de argv que quedó afuera del patrón de guardas ya aplicado a `target`/`options`; falta un test de regresión para el truncado de campos de `Finding` (sí existe para `Service`). Lo sólido se mantiene: SAVEPOINT verificado contra Postgres real (no solo SQLite), doble whitelist independiente, `secrets.compare_digest`, tests con aserciones reales.

**Reports + n8n + Infraestructura: 7,5/10.** El hallazgo más serio de toda esta segunda ronda: **dos nodos del propio workflow de n8n (`Resolve Pipeline Context`, `Get Target (Manual)`) pueden dejar un scan colgado en `running` para siempre** — corren *antes* de que exista cualquier red de contención, no tienen `continueOnFail`, y un fallo ahí nunca llama a `/scans/{id}/complete`. Es exactamente la clase de bug que el propio proyecto documenta haber eliminado (COD-2, Recomendación #2) para el caso "sin puerto HTTP", reaparecida en dos lugares que nadie había revisado porque están *antes* en la cadena, no después. Además: el contenedor de n8n es el único de los cinco servicios sin `cap_drop`/`security_opt`/`read_only`, pese a sostener los tres secretos compartidos de la plataforma y ejecutar JavaScript arbitrario en sus Code nodes; y `N8N_BLOCK_ENV_ACCESS_IN_NODE=false` (necesario para que `$env.*` funcione) significa que cualquier nodo puede leer esos tres secretos en texto plano. El servicio de Reports en sí sigue siendo el más sólido de los cinco (path traversal, escritura atómica, autoescapado real, verificado por grep).

**Frontend: 8/10.** Primera evaluación independiente de este componente desde el rediseño completo. Manejo de estado asíncrono (polling de progreso por herramienta, hallazgos llegando a mitad de escaneo) correcto y cuidado — la clase de bug (banners de "éxito" sobre datos parciales) que trabaja peor a equipos con más experiencia. Hallazgos: el botón "Eliminar" de un target queda permanentemente deshabilitado si `scansQuery` falla, sin ningún camino de recuperación salvo recargar la página; `ConfirmDialog` no tiene un focus trap real (Tab puede sacar el foco del modal mientras sigue abierto, para una confirmación de borrado en cascada); `TargetsPage.tsx` —con su propia lógica de polling por target y ordenamiento por fecha— es la única página sin ningún test dedicado.

### 8.3 Puntaje final: **7,9/10**

| Dimensión | Puntaje | Peso |
|---|---|---|
| Documento | 8/10 | ~35% |
| Backend + DB + Scanner | 8/10 | ~25% |
| Reports + n8n + Infraestructura | 7,5/10 | ~20% |
| Frontend | 8/10 | ~20% |

Sube respecto a la primera ronda (7,5/10), pero de forma incremental, no transformadora — coherente con lo que efectivamente pasó entre una evaluación y otra: correcciones puntuales sobre debilidades ya señaladas, no un rediseño de fondo. El documento mejora genuinamente en los dos puntos de menor esfuerzo y mayor impacto que la propia evaluación anterior había priorizado (D1, D4); el código sigue mostrando el mismo patrón ya observado en la primera ronda y en la segunda pasada de `/code-review` sobre la propia remediación: rigor real pero desparejo, con la ronda de escrutinio más reciente encontrando siempre algo nuevo y genuino (el hallazgo del hang de n8n en `Resolve Pipeline Context`/`Get Target (Manual)` es, de los dos ejercicios de evaluación independiente hechos sobre este proyecto, el más serio encontrado hasta ahora — toca directamente la garantía central de "ningún escaneo queda colgado" que el propio proyecto reivindica).

Para una nota más alta, en orden de impacto esperado: (1) corregir el hang de n8n en los dos nodos señalados — es el hallazgo más serio de esta ronda y el más barato de arreglar (agregar `continueOnFail` + una llamada de fallback a `/complete`, mismo patrón ya usado en el resto del workflow); (2) endurecer el contenedor de n8n al mismo nivel que los otros cuatro; (3) cerrar la brecha de detección (D3) — sigue siendo, de las dos evaluaciones independientes, el hallazgo sustantivo más citado y menos tocado; (4) terminar D5 en §13/§15.

## 9. Tercera evaluación independiente (2026-08-22)

Mismo método, misma advertencia de conflicto de interés que las dos veces
anteriores (Sección 0 y Sección 8) — sigue aplicando. Tres revisores de
código frescos en paralelo, sin acceso a ningún reporte previo ni a
mensajes de commit, contra `main` (commit `3ed0daf`, después de que la
Sección 8 se aplicó y mergeó). Además, releí yo mismo §13 con ojo crítico
para confirmar si D5 (densidad de prosa) quedó cerrado del todo.

### 9.1 Documento

**D5 confirmado cerrado.** §13, releído fresco, tiene oraciones de
longitud razonable (2-3 cláusulas, sin incisos entre rayas encadenados)
— no necesitaba la misma intervención que §9.1/§15 ya recibieron. D1 y
D4 se mantienen resueltos (sin cambios desde la Sección 8). D2 y D3
siguen sin tocarse, por la misma decisión de alcance de siempre.

**Evaluación del documento: 8/10** (sin cambio respecto a la ronda
anterior — D5 era la única pieza que faltaba de las de bajo costo, y
cerrarla no mueve la aguja tanto como D1/D4 la movieron la vez pasada).

### 9.2 Código — tres revisores frescos, cada uno con hallazgos nuevos y genuinos

**Backend + DB + Scanner: 8/10.** `report_service.is_safe_filename`
(`_SAFE_FILENAME = re.compile(r"[A-Za-z0-9._-]+")`) rechaza correctamente
`../../etc/passwd` (hay slash) pero **no rechaza un `file_path` de
exactamente `".."`** — ambos caracteres están individualmente permitidos
y no hace falta ningún slash para que un solo componente traversal pase
`fullmatch`. Es el mismo chequeo que ya cerró un agujero de traversal
(COD-1) y todavía deja uno más angosto abierto. También: `CveReference.
source_url` es el único campo de `create_cve_reference` que no se trunca
(código muerto hoy, nadie lo puebla, pero el mismo patrón de
truncado que sí se aplicó a `cve_id`/`cvss_vector` en la misma función se
saltó este); y `complete_scan` sigue con un check-then-act no atómico
(dos llamadas concurrentes a `/complete` podrían pisarse el
`error_message`/`finished_at` una a la otra).

**Reports + n8n + Infraestructura: 8/10.** El hallazgo más interesante de
toda esta ronda: **`Complete Scan` tiene `continueOnFail: true`, pero
nada corriente abajo verifica si la llamada realmente tuvo éxito.** Si
falla, la ejecución sigue igual hacia `Generate Report` → `Send Report
Email` → `Pipeline Complete`, como si el scan se hubiera completado —
mientras la fila en la base de datos queda colgada en `running` para
siempre. Es una variante distinta del mismo problema que motivó toda la
Sección 8: `continueOnFail` evita que la ejecución aborte, pero no evita
que un fallo silencioso dispare el resto del pipeline como si nada
hubiera pasado. Además, el nuevo nodo `Compare Webhook Secret
(Constant-Time)` (agregado en esta misma ronda) es el primer nodo del
camino de producción y **no tiene `continueOnFail`** — exactamente la
posición "antes de que exista cualquier red de contención" que motivó
arreglar `Resolve Pipeline Context`, replicada sin querer en el propio
nodo que se agregó para otra cosa.

**Frontend: 7/10 — el único puntaje que bajó.** El focus trap de
`ConfirmDialog.tsx` agregado en la Sección 8 tiene una regresión real y
reproducible: su `useEffect` de foco inicial depende de `[onCancel]`, y
`TargetDetailPage.tsx` (su único llamador real) pasa una función flecha
inline que cambia de identidad en cada render — y ese componente
re-renderiza cada 4 s mientras hay un scan no terminal (su propio
`refetchInterval`). Cada uno de esos re-renders vuelve a disparar
`cancelRef.current?.focus()`, arrancándole el foco a "Eliminar todo" en
medio de una interacción real, no hipotética. Es exactamente la función
que se endureció esta ronda, con un bug de raíz en el único lugar real
donde se usa.

### 9.3 Puntaje final: **7,8/10**

| Dimensión | Puntaje | Peso |
|---|---|---|
| Documento | 8/10 | ~35% |
| Backend + DB + Scanner | 8/10 | ~25% |
| Reports + n8n + Infraestructura | 8/10 | ~20% |
| Frontend | 7/10 | ~20% |

**Baja levemente respecto a la ronda anterior (7,9/10), y eso es
información real, no ruido.** Cerrar el hang de n8n (el hallazgo más
serio de la Sección 8) funcionó y se verificó en vivo — pero el propio
proceso de arreglarlo introdujo un nodo nuevo con el mismo tipo de gap
(`Compare Webhook Secret` sin `continueOnFail`), y el endurecimiento del
focus trap del frontend introdujo una regresión real en su único uso
real. El patrón que las tres rondas de evaluación de este proyecto
vienen mostrando de forma consistente se sostiene: **arreglar hallazgos
reales no sube la nota de manera monótona** cuando cada arreglo tiene
superficie para introducir un problema nuevo — es la razón por la que
este proyecto sigue corriendo revisores frescos en cada ronda en vez de
confiar en que "ya se corrigió" acumula puntaje sin más.

Para una próxima ronda, en orden de impacto: (1) el bug del focus trap
(barato: separar el foco inicial en un efecto de solo-montaje,
independiente del `useEffect` con `onCancel`); (2) `Complete Scan` +
`Compare Webhook Secret (Constant-Time)` sin verificación de éxito ni
`continueOnFail` respectivamente; (3) el `".."` sin cubrir en
`is_safe_filename`; (4) D3 sigue siendo, de las tres rondas, el hallazgo
sustantivo más citado y menos tocado.

## 10. Cuarta evaluación independiente (2026-08-23)

**Nota de conflicto de interés, otra vez explícita** (aplica igual que en
las Secciones 0, 8 y 9): esta evaluación la generó el mismo asistente que
implementó los 6 fixes de la Sección 9. Mismo método de mitigación:
tres revisores de código lanzados en paralelo, **sin acceso a este
archivo, a `docs/self-audit-report.md`, a `docs/audit-corrections/`, ni a
mensajes de commit**, instruidos a tratar comentarios/sticky-notes/
docstrings como no confiables y verificar todo contra el código real de
`main` (commit `410a522`, después de mergear la Sección 9) como si lo
vieran por primera vez.

### 10.1 Documento — releído directamente contra D1/D4/D5

Se releyó §4.2 (objetivo 6) y §5 (pregunta 2) —los síntomas concretos de
D1— directamente en el `.docx` actual, párrafo por párrafo, en vez de
asumir que sigue como en la ronda anterior:

- **D1 sigue confirmado resuelto.** El objetivo 6 (§4.2) y la pregunta 2
  (§5) todavía declaran explícitamente, en el mismo párrafo, que la
  comparación cronometrada contra el proceso manual no se ejecutó en
  esta ronda y remiten a §14.2/§14.3 — no hay regresión ni desincronía
  nueva.
- **D4 y D5 sin cambios** desde que la Sección 9 los confirmó cerrados
  (D5) o la Sección 8 los cerró (D4) — no se tocó nada del documento en
  la ronda de fixes de la Sección 9, así que no había razón para
  esperar una regresión aquí, y no se encontró ninguna.
- **D2 y D3 siguen sin abordarse**, misma decisión de alcance de siempre
  (ver §7).

**Evaluación del documento: 8/10** (sin cambio). Nada se editó en el
documento desde la ronda anterior, así que un puntaje distinto habría
sido una señal de revisión descuidada, no de progreso real.

### 10.2 Código — tres revisores frescos, cada uno con hallazgos nuevos y genuinos

**Backend + DB + Scanner: 7,5/10** (baja de 8/10). Hallazgo más
relevante: `nuclei_normalizer.py` solo llama `severity.from_label(...)`
y nunca cae al `severity.from_cvss_score(...)` que ya existe, está
unit-testeado y nunca se invoca desde ningún camino de producción — un
template de Nuclei con `cvss-score` alto pero sin `severity` de texto
propio queda archivado como INFO pese a un CVSS real y alto, tocando
directamente el objetivo central de triage de severidad del sistema.
También nuevo: `delete_target` no tiene guarda alguna contra borrar un
target con scans todavía `PENDING`/`RUNNING` — el cascade `ondelete`
borra en silencio Scan/ScanTask/Finding en pleno vuelo, y las siguientes
llamadas de n8n a `/scans/{id}/tasks`/`/complete` devuelven 404 sin
ningún aviso; `Service.host`/`Service.protocol` son las únicas columnas
de esa tabla que no se truncan, pese a que el propio patrón de truncado
sistemático (Recomendación #3/#4) sí se aplicó a sus columnas vecinas
(`service_name`/`product`/`version`); el truncado de `Finding.title`
sigue duplicado en cada uno de los 5 normalizadores en vez de vivir en
el repositorio como el resto de los campos truncados —el propio
comentario del módulo lo admite—, así que un sexto adaptador futuro que
olvide repetir el `[:255]` reproduciría la misma clase de bug que las
Recomendaciones #3/#4 existieron para cerrar.

**Reports + n8n + Infraestructura: 7,5/10** (baja de 8/10). El nuevo
`retryOnFail` de `Complete Scan` (agregado en la Sección 9) resuelve el
blip transitorio, pero **si las 3 reintentos se agotan igual —Backend
genuinamente caído, no un blip— el workflow sigue adelante hacia
`Generate Report` → `Send Report Email` → `Pipeline Complete` como si el
scan se hubiera completado**, mientras la fila queda en `running` para
siempre: el propio sticky note lo llama "riesgo residual reconocido",
pero es una inconsistencia de comportamiento sin resolver, no un
no-problema documentado. Además, ningún nodo `Scan: *`/`Ingest: *` tiene
`retryOnFail` pese a que sí tienen `continueOnFail` — el mismo patrón de
reintento que se aplicó a `Complete Scan` no se generalizó a los nodos
que llaman a los mismos servicios externos (Scanner/Backend) y pueden
fallar de forma igual de transitoria, así que un blip ahí descarta en
silencio todos los hallazgos de esa herramienta sin señal alguna. Otros
hallazgos nuevos: el encabezado de `docker-compose.yml` promete "cero
pasos manuales" tras `docker compose up -d`, pero nada en el compose
importa/activa el workflow de n8n — solo `.github/workflows/e2e.yml`
lo hace, vía tres comandos `docker compose exec` que no existen en
ningún lugar del compose; `BACKEND_API_KEY` se hornea en el bundle JS
público del frontend (`VITE_API_KEY`), visible para cualquiera que abra
las devtools, deshaciendo el propósito del secreto compartido para ese
cliente; el puerto de Postgres se publica al host por defecto sin que
nada dentro del stack lo necesite (inconsistente con el resto del
diseño, que no publica puertos salvo que algo externo los use); CI no
corre lint/type-check ni ningún escaneo de dependencias/seguridad para
los tres servicios Python.

**Frontend: 6/10 — el puntaje más bajo de las cuatro rondas de
evaluación de este proyecto.** El hallazgo más serio: en **tres lugares
distintos** (`TargetsPage.tsx`, y dos veces en `ScanDetailPage.tsx`), un
fallo real de fetch en segundo plano es indistinguible de —o se
presenta activamente como— un resultado legítimo vacío o completo. En
`TargetsPage.tsx`, el error de `scanQueries[index]` nunca se lee; si esa
consulta falla, la fila muestra "nunca escaneado" exactamente igual que
un target genuinamente nunca escaneado. En `ScanDetailPage.tsx`, un
fallo en `findingsQuery` deja `findings = []`, y para un scan no-corriendo
esto dispara el texto **"Las N herramientas corrieron y ninguna reportó
nada. Esto es un resultado, no un error."** — una afirmación
directamente falsa cuando la causa real es un error de red, mostrada al
lado de un `ErrorBanner` real que contradice el propio texto en la misma
pantalla. Un fallo de `tasksQuery` renderiza los 5 tools como
"pendiente", visualmente idéntico a un scan que todavía no arrancó. Para
un dashboard de hallazgos de seguridad, esta clase de error —"no sé" se
ve igual que "no hay nada"— es un riesgo real de que un operador
descarte una falla de infraestructura como ausencia de vulnerabilidades.
Además: `reportsQuery.error` no tiene ningún banner ni manejo, a
diferencia de las otras dos mutaciones de esa misma página; una única
instancia de `downloadMutation` compartida entre todas las filas de
reportes produce indicadores de "descargando"/error incorrectos si dos
descargas se solapan; todas las "tablas" de la aplicación son grids de
`div` sin ningún elemento `&lt;table&gt;` semántico, perdiendo toda
estructura de fila/columna para lectores de pantalla; los módulos de
lógica pura (`lib/format.ts`, `lib/severity.ts`, `lib/status.ts`,
`lib/tools.ts`) y el cliente de API no tienen ningún test dedicado.

### 10.3 Puntaje final: **7,4/10**

| Dimensión | Puntaje | Peso |
|---|---|---|
| Documento | 8/10 | ~35% |
| Backend + DB + Scanner | 7,5/10 | ~25% |
| Reports + n8n + Infraestructura | 7,5/10 | ~20% |
| Frontend | 6/10 | ~20% |

**Baja respecto a la ronda anterior (7,8/10), y de forma más marcada que
la caída entre la segunda y la tercera ronda (7,9→7,8).** El patrón que
las cuatro rondas de evaluación de este proyecto vienen mostrando de
forma consistente se sostiene y se profundiza: los 6 fixes de la
Sección 9 se verificaron correctamente para lo que arreglaban, pero
ninguno de los tres alcances quedó sin hallazgos nuevos y genuinos —y
el Frontend, en particular, muestra por primera vez un problema
*sistémico* (repetido en tres lugares distintos, no un bug aislado) en
vez de un hallazgo puntual como en rondas anteriores. Esto no es
evidencia de que el proyecto esté empeorando en términos absolutos —el
código sigue mostrando disciplina real (guardas de path traversal,
comparación en tiempo constante, savepoints, truncado sistemático,
tests con aserciones reales)— sino de que **escrutinio fresco e
independiente sigue encontrando algo genuino en cada ronda**, que es
exactamente la premisa metodológica que sostiene este documento desde
la Sección 0.

Para una próxima ronda, en orden de impacto esperado: (1) el patrón de
error-como-resultado-legítimo en el Frontend (3 instancias, mismo
arreglo conceptual: leer y renderizar `.error` de cada query en vez de
solo `.data`) — es el hallazgo más serio de esta ronda por tocar la
confiabilidad de lo que un operador de seguridad ve en pantalla; (2) el
fallback de severidad de Nuclei nunca conectado (`from_cvss_score`
existe, está testeado, no se usa) — barato de arreglar, alto impacto en
la función central de triage; (3) generalizar `retryOnFail` a los nodos
`Scan:*`/`Ingest:*` de n8n, y decidir qué debe pasar si `Complete Scan`
agota sus 3 reintentos (¿debería `Generate Report` verificar el status
antes de correr?); (4) sacar `BACKEND_API_KEY` del bundle del frontend
—ya no cumple su función como secreto compartido estando ahí—; (5) D3
sigue siendo, de las cuatro rondas, el hallazgo sustantivo más citado y
menos tocado.

## 11. Remediación aplicada (2026-08-23)

Antes de corregir nada, se verificó cada hallazgo de la Sección 10
contra el código y la documentación real (no solo contra el reporte del
revisor) — la instrucción permanente del usuario de planificar antes de
corregir. Esa verificación encontró que **dos de los "hallazgos"
nuevos ya eran decisiones documentadas de rondas anteriores**, mismo
patrón que el falso positivo COD-8 de una ronda anterior:

- **`BACKEND_API_KEY` en el bundle del Frontend**: `docs/security.md`
  ya documenta esta limitación exacta (incluida la recomendación #4 de
  esta misma sección, escrita antes de verificar — corrección: no se
  aplica, ya es una decisión tomada y explicada, no un gap fresco).
- **Puerto de Postgres publicado por defecto**: ya tiene un comentario
  explícito de una ronda anterior (COD-15, "deliberate developer-
  convenience trade-off, not an oversight") en `docker-compose.yml`.

De los hallazgos restantes, se corrigieron 4 backend (Medio) + 2 n8n
(Alto/Medio) + 1 inconsistencia de documentación + 5 frontend
(Alto/Medio), y se difirieron explícitamente el resto (Bajos, o de
alcance mayor al de esta ronda — CI con lint/type-check/scan de
dependencias para los 3 servicios Python, y el refactor de las tablas
div-grid a `<table>` semántico). Razonamiento completo de cada fix (qué
arreglo obvio se descartó y por qué) en
`C:\Users\lauti\.claude\plans\synthetic-tinkering-puzzle.md`; resumen:

- **Backend**: fallback de `severity.from_cvss_score` conectado en
  `nuclei_normalizer` solo cuando falta la etiqueta propia de la
  herramienta (no siempre, para no pisar la etiqueta explícita ya
  documentada como confiable); `delete_target` ahora rechaza borrar un
  target con scans no terminales (`TargetHasActiveScansError`, 409) —
  requirió mover `TERMINAL_STATUSES` a `database/models/enums.py` como
  `TERMINAL_SCAN_STATUSES` para que `target_service.py` pudiera
  importarlo sin ciclo con `scan_service.py`; `Service.host`/`protocol`
  truncados igual que sus columnas vecinas; `Finding.title` centralizado
  en `finding_repository.create_finding` en vez de duplicado en 3
  normalizadores.
- **n8n**: nuevo `IF: Complete Scan Failed` entre `Complete Scan` y
  `Generate Report` — si los 3 reintentos de `Complete Scan` se agotan,
  el pipeline ya no sigue adelante como si el scan hubiera cerrado
  (mismo patrón de IF-gate ya usado 4 veces en el workflow); `retryOnFail`
  agregado **solo** a los 5 nodos `Ingest: *` (llamadas cortas al
  Backend) y deliberadamente **no** a los 5 `Scan: *` (llamadas de
  minutos de duración, donde tripliciar el costo de un fallo real iría
  contra el objetivo de pipeline de 4-6 minutos).
- **Documentación**: el encabezado de `docker-compose.yml` afirmaba "sin
  pasos manuales" cuando `n8n/README.md` ya documenta honestamente que
  el workflow requiere un import/activate manual por volumen nuevo —
  corregido para que ambos documentos digan lo mismo.
- **Frontend**: el mismo patrón de bug en 4 lugares distintos (el error
  de una query nunca se distinguía de un resultado vacío/completo
  legítimo) corregido en un solo pase — `TargetsPage`'s historial de
  scans por target, y `ScanDetailPage`'s `reportsQuery`/`findingsQuery`/
  `tasksQuery`, esta última la más grave (el texto "esto es un
  resultado, no un error" se mostraba literalmente al lado de un error
  real). `downloadMutation` compartido entre todas las filas de reportes
  (causaba estado de descarga/error incorrecto entre filas concurrentes)
  reemplazado por una instancia de `useMutation` por fila
  (`ReportRow`).

**Verificado en vivo, no solo "debería andar"**: `backend` 135→143
tests, `frontend` 43→45 tests, ambos pasando contra las imágenes
reconstruidas; `tsc --noEmit`/`oxlint`/`vite build` limpios; workflow de
n8n reimportado/reactivado, un scan real de punta a punta contra `dvwa`
completó con `pipeline_run_id` poblado (88) y generó un reporte PDF real
—confirma que el nuevo `IF: Complete Scan Failed` no rompió el camino
feliz—, 32 findings ingeridos con la distribución de severidad esperada.
Igual que en rondas anteriores, no se pudo disparar en vivo el camino de
fallo de `Complete Scan` (requeriría tumbar el Backend a mitad de
pipeline); se verificó por inspección de la conexión JSON en vez de
fingir una prueba que no se hizo.

## 12. Quinta evaluación independiente (2026-08-23)

**Nota de conflicto de interés, otra vez explícita** (Secciones 0, 8, 9,
10): esta evaluación la generó el mismo asistente que implementó los 8
fixes de la Sección 11. Mismo método: tres revisores de código frescos
en paralelo, sin acceso a este archivo ni a mensajes de commit, contra
`main` en `b0a1bd3` (después de mergear la Sección 11). Los hallazgos
más relevantes de cada revisor se verificaron a mano (lectura directa
del código) antes de incluirlos acá, no solo se tomó el reporte al pie
de la letra — esa verificación matizó uno de los hallazgos (ver más
abajo).

### 12.1 Documento

Sin cambios desde la Sección 10/11: esta ronda no tocó el `.docx` más
allá del hash de referencia (actualizado por separado, ver la Sección
11). **Evaluación del documento: 8/10, sin cambio** — no hay nada nuevo
que evaluar.

### 12.2 Código — tres revisores frescos, cada uno con hallazgos nuevos y genuinos

**Backend + DB + Scanner: 8,5/10** (sube de 7,5). Ningún hallazgo Alto
o Crítico esta vez — la ronda de fixes de la Sección 11 (guarda de
`delete_target`, truncado de `Service.host`/`protocol`, fallback de
CVSS en Nuclei, truncado centralizado de `title`) cerró exactamente lo
que las rondas anteriores habían señalado, sin introducir un problema
nuevo del mismo tipo esta vez. Dos hallazgos Medio genuinos y no
señalados antes: (1) la cookie de sesión de DVWA usada para el escaneo
autenticado (Recomendación #5) queda persistida en texto plano en
`ScanTask.command` y se devuelve sin redactar por `GET
/scans/{id}/tasks` — el propio test de `scan_runner` lo confirma
explícitamente (`assert "Cookie: ... PHPSESSID=abc" in result.command`),
así que es comportamiento intencional, no un descuido, pero sigue
siendo una violación de higiene de secretos real si esto se apuntara
alguna vez a un target con credenciales reales; (2) el Backend usa la
misma `BACKEND_API_KEY` para las rutas de operador (`targets`) y las
rutas que solo debería llamar n8n (`/scans/{id}/tasks`,
`/scans/{id}/complete`) — a diferencia del Scanner Service, que sí
separa `INTERNAL_API_KEY` de lo que el Frontend puede ver. Cualquiera
con la key que ya tiene el Frontend puede forjar hallazgos o completar
un scan directamente, saltándose el pipeline.

**Reports + n8n + Infraestructura: 7/10** (baja de 7,5). El hallazgo
más serio: `Scan: WhatWeb`/`Nikto`/`Nuclei`/`ZAP` tienen
`continueOnFail` pero **ninguno tiene un IF de verificación posterior**
— a diferencia de `Scan: Nmap` (cuyo fallo sí lo capta `Select HTTP
Port` → `IF: No HTTP Service Found`) y de `Complete Scan` (que la
Sección 11 acaba de blindar). Un scan puede llegar a `completed` sin
haber corrido ninguna de las cuatro herramientas web, sin que quede
registro de eso en ningún lado — verificado directamente en el JSON
(`continueOnFail: true`, `retryOnFail` ausente, sin nodo IF corriente
abajo). También nuevo: `Compare Webhook Secret (Constant-Time)`
compara `$env.N8N_WEBHOOK_SECRET` sin garantizar que no esté vacío — si
lo estuviera, dos cadenas vacías (largo 0 los dos lados) producen
`secret_matches: true`. **Matizado tras verificar**: el Backend sí
tiene un `field_validator` que rechaza arrancar con
`N8N_WEBHOOK_SECRET` vacío (`backend/app/config.py:88-93`), así que en
el despliegue documentado (mismo valor de `.env` para ambos servicios)
esto no es explotable hoy — pero n8n en sí mismo no repite esa
validación, así que es un hueco real de defensa en profundidad, no una
falla completa de autenticación en la configuración por defecto. Medio,
no Alto, con esa salvedad. Además: el Form Trigger de n8n no tiene
ningún chequeo de secreto (solo el Webhook Trigger lo tiene) y el
puerto de n8n está publicado — permite lanzar scans reales sin
credencial alguna si se conoce un `target_id`.

**Frontend: 7/10** (sin cambio, pero por hallazgos distintos a los ya
corregidos en la Sección 11 — el patrón de "algo nuevo en cada ronda"
se sostiene). El más interesante: `tasksQuery`/`findingsQuery` dejan de
hacer poll (`refetchInterval: pollWhileRunning`) apenas `running` pasa
a `false`, pero eso solo **detiene** el polling futuro — no dispara un
último fetch garantizado, a diferencia de `reportsQuery` (que sí usa
`enabled: !running`, un mecanismo que fuerza un fetch real en la
transición). Hasta ~2s de datos de cola (el último hallazgo o tarea
escrito justo antes del cierre) pueden faltar en lo que la UI ya
etiqueta como "lista completa". También real: cancelar el diálogo de
confirmación de borrado mientras la mutación de borrado sigue en vuelo
no la cancela — el usuario cree que canceló, pero `onSuccess` igual
navega a `/targets` momentos después (verificado: solo el botón de
confirmar respeta `pending`, Cancelar/Escape/backdrop no).

### 12.3 Puntaje final: **7,7/10**

| Dimensión | Puntaje | Peso |
|---|---|---|
| Documento | 8/10 | ~35% |
| Backend + DB + Scanner | 8,5/10 | ~25% |
| Reports + n8n + Infraestructura | 7/10 | ~20% |
| Frontend | 7/10 | ~20% |

**Sube respecto a la ronda anterior (7,4/10)**, principalmente porque
los 4 fixes de backend de la Sección 11 funcionaron sin generar un
problema nuevo del mismo tipo esta vez (algo que no había pasado en
ninguna de las tres rondas de código anteriores). Pero el patrón de
fondo de este proyecto se sostiene en las otras dos dimensiones: n8n
bajó porque un revisor fresco encontró un hueco más serio que los ya
cerrados (4 de 5 herramientas de escaneo sin ninguna red de contención,
un hallazgo que ninguna de las cuatro rondas anteriores había señalado
pese a haber revisado ese mismo workflow varias veces), y el Frontend
se mantuvo en 7 con hallazgos completamente distintos a los que motivaron
ese mismo puntaje la ronda pasada. Ninguna de las cuatro rondas de
evaluación de este proyecto ha terminado con "no hay nada más que
encontrar", y esta quinta tampoco.

Para una próxima ronda, en orden de impacto esperado: (1) IF de
verificación después de `Scan: WhatWeb`/`Nikto`/`Nuclei`/`ZAP`, mismo
patrón que ya existe para Nmap y para Complete Scan; (2) separar
`BACKEND_API_KEY` en dos tiers (operador vs. llamadas internas de n8n),
mismo patrón que el Scanner Service ya usa con `INTERNAL_API_KEY`; (3)
la corrección del "cancelar no cancela" en `ConfirmDialog`/
`TargetDetailPage`; (4) resincronizar `tasksQuery`/`findingsQuery` con
`enabled`/una invalidación explícita en la transición running→terminal,
igual que `reportsQuery`; (5) D3 sigue siendo, de las cinco rondas, el
hallazgo sustantivo más citado y menos tocado.

## 13. Sexta evaluación independiente (2026-08-24)

**Nota de conflicto de interés, otra vez explícita** (Secciones 0, 8, 9,
10, 12): esta evaluación la generó el mismo asistente que implementó
el plan estratégico de la Sección 12 (fixes de la 5ª ronda + D3). Mismo
método: tres revisores de código frescos en paralelo, sin acceso a este
archivo ni a mensajes de commit, contra `main` en `410bcd1` (después de
mergear el plan estratégico completo).

### 13.1 Documento

Sin cambios desde la Sección 12: esta ronda no tocó el `.docx` más allá
del hash de referencia. **Evaluación del documento: 8/10, sin cambio.**

### 13.2 Código — tres revisores frescos, cada uno con hallazgos nuevos y genuinos

**Backend + DB + Scanner: 8/10** (baja levemente de 8,5, dentro del
mismo rango alto). Ningún hallazgo Alto — el patrón de "sin
Critical/High" que arrancó en la ronda anterior se sostiene. Dos
hallazgos Medio genuinos y verificados: (1) `GET /reports/{id}/download`
(`backend/app/routers/reports.py:69`) llama
`upstream.raise_for_status()` **fuera** del bloque `try/except` que
envuelve la llamada — un 500/503 del Reports Service escapa como
excepción no manejada en vez del 502 limpio que el propio
`report_service.generate_report` ya produce para el mismo tipo de
fallo (verificado: el `try` solo envuelve `httpx.get(...)`, la llamada
a `raise_for_status()` es una sentencia separada después, sin ningún
`@app.exception_handler` registrado para `httpx.HTTPStatusError` en
`main.py`); (2) `Finding.service_id` es una FK real, indexada y
expuesta en la API, pero ningún código la puebla nunca — cada
`Finding` reporta `service_id: null` siempre, así que "vulnerabilidades
por servicio/puerto" —un caso de uso natural para esta plataforma— no
se puede derivar de los datos tal como están, pese a que el esquema fue
diseñado para soportarlo (reconocido en un comentario de test, nunca
resuelto). También señalado: el patrón de test contra Postgres real
para detectar truncado de `VARCHAR` (que ya existió una vez para
corregir un bug real) solo se generalizó a `service_repository`, no a
`finding_repository`/`technology_repository`/`cve_reference`, que
comparten el mismo riesgo estructural.

**Reports + n8n + Infraestructura: 6,5/10** (baja de 7). El hallazgo
más señalado por este revisor —la comparación de secreto del webhook
falla en abierto si `N8N_WEBHOOK_SECRET` está vacío— es el mismo que
la Sección 12 ya investigó y clasificó como Medio, no Alto, tras
verificar que el propio `backend/app/config.py` tiene un
`field_validator` que rechaza arrancar con ese valor vacío
(re-verificado ahora: el validador sigue presente,
`_require_n8n_webhook_secret`, línea 89). Bajo el despliegue
documentado (mismo `.env` para ambos servicios), esto sigue siendo un
hueco real de defensa en profundidad —n8n no impone la misma garantía
de forma independiente— pero no una vulnerabilidad explotable en la
configuración por defecto; se mantiene la misma severidad rebajada que
la ronda anterior, no la calificación "Alta" que este revisor le dio
sin ese contexto. Hallazgo nuevo y genuino, sí aceptado: de los 4 nodos
`Mark Scan Failed - *`/`Complete Scan` cuyo trabajo es sacar un scan de
`running`, solo `Complete Scan` recibió reintentos + verificación
posterior (rondas 4-5) — los otros 3 (`Mark Scan Failed - Target No
Disponible`, `Sin Puerto HTTP`, `Contexto Invalido`) siguen sin
reintento y sin chequeo, exactamente la misma clase de bug que motivó
arreglar `Complete Scan`, no generalizada a sus tres hermanos. También
nuevo: los 5 nodos `Scan: *` (las llamadas reales a las herramientas)
no tienen `retryOnFail`, a diferencia de los 5 `Ingest: *` que sí lo
tienen desde la ronda 4 — la llamada más cara y valiosa tiene menos
resiliencia que la más barata.

**Frontend: 8/10** (sube de 7). Primera vez que este alcance no tiene
ningún hallazgo Alto real tras verificar — el hallazgo que el revisor
marcó como "High" (el error de borrado de un target queda invisible
detrás del modal de confirmación abierto) es real y confirmado: el
`ErrorBanner` de `deleteMutation.error` se renderiza en el flujo normal
de la página, debajo del backdrop del modal (`z-index: 10`), y nada
cierra el diálogo ni mueve el error al primer plano cuando la mutación
falla mientras el diálogo sigue abierto. Dos hallazgos Medio de
accesibilidad en `ConfirmDialog` (el texto de consecuencias no está
asociado vía `aria-describedby`, el contenido de fondo no se marca
`aria-hidden`/`inert` mientras el modal está abierto) — reales, pero
coherentes con el patrón ya visto: cada ronda de este componente cierra
una brecha de accesibilidad y el escrutinio fresco encuentra la
siguiente capa.

### 13.3 Puntaje final: **7,7/10**

| Dimensión | Puntaje | Peso |
|---|---|---|
| Documento | 8/10 | ~35% |
| Backend + DB + Scanner | 8/10 | ~25% |
| Reports + n8n + Infraestructura | 6,5/10 | ~20% |
| Frontend | 8/10 | ~20% |

**Se mantiene igual que la ronda anterior (7,7/10), pero por una
composición distinta.** El plan estratégico de la Sección 12 cerró
efectivamente el hallazgo más citado en las cinco rondas anteriores
(D3) y subió el puntaje del Frontend a su mejor nota de todo el
proyecto — pero Reports+n8n+Infraestructura bajó, porque el mismo
patrón que el propio proyecto ya identificó y corrigió parcialmente
(`continueOnFail` sin verificación posterior) resultó generalizado a
solo 1 de 4 nodos que comparten el mismo riesgo, y a ninguno de los 5
nodos `Scan: *`. El patrón de fondo de las seis rondas de este proyecto
se sostiene sin excepción: cada vez que se cierra una brecha real,
aparece otra —a veces en el mismo archivo, a veces en el nodo de al
lado— que ninguna ronda anterior había señalado.

Para una próxima ronda, en orden de impacto esperado: (1) generalizar
reintentos/verificación posterior a los 3 nodos `Mark Scan Failed - *`
restantes y a los 5 `Scan: *`, cerrando el mismo patrón que
`Complete Scan` ya resolvió para sí mismo; (2) mover
`upstream.raise_for_status()` dentro del `try/except` en
`reports.py::download_report`, mismo patrón ya correcto en
`report_service.generate_report`; (3) decidir qué hacer con
`Finding.service_id` (poblarlo realmente, o documentarlo como no
poblado de forma explícita en vez de dejarlo como una FK silenciosamente
vacía); (4) el error de borrado de un target invisible detrás del
modal en `TargetDetailPage`; (5) D3 puede darse por cerrado — es la
primera ronda, de las seis, en que ningún revisor lo vuelve a citar
como hallazgo abierto.

## 14. Séptima evaluación independiente — evaluación del proyecto completo (2026-08-25)

**Nota de conflicto de interés, otra vez explícita** (Secciones 0, 8, 9,
10, 12, 13): esta evaluación la generó el mismo asistente que implementó
los fixes de la Sección 13. Mismo método, esta vez pedido explícitamente
como evaluación del **proyecto completo**: tres revisores de código
frescos en paralelo, sin acceso a este archivo ni a mensajes de commit,
contra `main` en `ecb6d42` (después de mergear los 8 fixes de la ronda
anterior), más mi propia relectura del documento.

### 14.1 Documento

Sin cambios de contenido desde la Sección 12 (solo el hash de referencia,
actualizado dos veces desde entonces). Releí el Resumen/Abstract y el
Índice para confirmar que no hay drift. **Evaluación del documento:
8/10, sin cambio.**

### 14.2 Código — tres revisores frescos, cada uno con hallazgos nuevos y genuinos

**Backend + DB + Scanner: 8/10** (se mantiene). El hallazgo más serio de
toda esta ronda, en cualquier alcance: **una sola fila con un dato
malformado puede hacer desaparecer silenciosamente todos los hallazgos
reales de una herramienta completa.** `scan_task_service.py:105-166`
envuelve el normalizado completo de un `scan_task` —cada `Service`,
`Technology`, `Finding` y `CveReference` que produjo la herramienta— en
un único `SAVEPOINT`; cualquier excepción en cualquier punto revierte
todo el bloque y resetea los contadores a cero, no solo el ítem que
falló. Verificado un disparador concreto:
`nuclei_normalizer.py:29` pasa `classification.get("cvss-score")`
directo a `Finding.cvss_score` (`Numeric(3,1)`, tope real 99,9) **sin
validar**, a diferencia de cada otro campo derivado de herramienta en el
mismo módulo, que sí se trunca defensivamente. Un template de Nuclei de
la comunidad (no saneado) con un `cvss-score` fuera de rango haría que
un scan que legítimamente encontró 50 vulnerabilidades reales reporte 0
— exactamente la clase de problema que compromete la métrica de recall
que la propia tesis mide. También nuevo: `delete_target` (agregado en
la ronda 4) sigue siendo un check-then-act sin respaldo atómico, a
diferencia de `register_target`/`complete_scan`, que sí lo tienen — el
propio código de este proyecto ya sabe resolver esta clase de carrera y
no se aplicó acá.

**Reports + n8n + Infraestructura: 7/10** (se mantiene). Hallazgo nuevo
y genuino, verificado a mano: el `error_message`/`tool_failure_summary`
que el Backend sí envía a la Reports Service (`ScanRead.error_message`
existe y viaja en el payload) se pierde en silencio porque
`reports/app/schemas/report.py`'s `ScanInfo` **no tiene ese campo** —
Pydantic descarta los campos extra por defecto, y ningún template lo
renderiza. Es decir: el pipeline ya calcula qué herramienta falló
(ronda 6), pero esa información es arquitectónicamente incapaz de llegar
al artefacto final que un operador realmente lee — el reporte PDF/HTML
puede mostrar "completed" sin ninguna mención de que faltó una
herramienta. El fail-open del webhook secret se re-verificó y se
mantiene con la misma severidad rebajada de las rondas 5-6 (el
validador de arranque del Backend sigue ahí). También reafirmado: los 5
nodos `Scan: *` siguen sin `retryOnFail` (decisión ya tomada y
reafirmada en la ronda 6) y `n8n:latest` sigue sin pinnear (deferido,
mismo razonamiento de rondas anteriores).

**Frontend: 6,5/10** (baja de 8 — el hallazgo más severo de todo el
proyecto en esta ronda). Verificado a mano contra el comportamiento real
de TanStack Query: `TargetDetailPage.tsx:69-70` y
`ScanDetailPage.tsx:218-219` hacen `if (query.error) return
<ErrorBanner .../>` **antes** de comprobar si `query.data` todavía tiene
un valor válido de un fetch anterior exitoso — TanStack Query nunca
borra `data` en un fallo de refetch en segundo plano, así que un solo
error transitorio (un blip de red durante los 4-6 minutos de polling
cada 2s mientras un scan corre) hace desaparecer toda la página —botón
de borrado, historial de scans, tabla de hallazgos, todo— y la reemplaza
por un banner de error, exactamente la clase de "dato parcial leído como
completo" (o en este caso, "un error transitorio leído como pérdida
total") que el propio proyecto se cuidó de evitar en `findingsQuery`/
`tasksQuery` en las mismas páginas. Es una inconsistencia real dentro
del mismo archivo, no solo entre archivos.

### 14.3 Puntaje final: **7,5/10**

| Dimensión | Puntaje | Peso |
|---|---|---|
| Documento | 8/10 | ~35% |
| Backend + DB + Scanner | 8/10 | ~25% |
| Reports + n8n + Infraestructura | 7/10 | ~20% |
| Frontend | 6,5/10 | ~20% |

**Baja de 7,7 a 7,5**, empujada casi enteramente por el Frontend — la
misma área que había alcanzado su techo histórico (8/10) la ronda
anterior ahora tiene el hallazgo más severo de todo el proyecto en esta
ronda. Esto no contradice el progreso de la ronda 6 (los fixes de esa
ronda siguen sosteniéndose, ninguno fue revertido ni cuestionado por
estos revisores) — es, una vez más, la misma señal que las siete rondas
de este proyecto vienen mostrando sin excepción: escrutinio fresco
siempre encuentra algo real, y esta vez le tocó a un patrón (guardas de
`error` que descartan `data` válido) que ninguna de las seis rondas
anteriores había mirado desde ese ángulo específico.

Para una próxima ronda, en orden de impacto esperado: (1) las guardas
`if (query.error) return <ErrorBanner/>` en `TargetDetailPage`/
`ScanDetailPage` deben comprobar primero si `data` sigue disponible,
mismo patrón que `findingsQuery`/`tasksQuery` ya usan en los mismos
archivos; (2) el `SAVEPOINT` todo-o-nada de `scan_task_service.py` más
la falta de validación del `cvss-score` de Nuclei — el par de hallazgos
que más directamente amenaza la métrica de recall que la tesis mide;
(3) conectar `tool_failure_summary` al `ScanInfo` de la Reports Service
para que el reporte final pueda reflejar un fallo parcial; (4) el
`delete_target` sin respaldo atómico, cerrando la única brecha de "el
proyecto ya sabe resolver esto pero no lo aplicó acá" que quedó en el
backend.

## 15. Octava evaluación independiente — evaluación del proyecto completo (2026-08-26)

**Nota de conflicto de interés, otra vez explícita** (Secciones 0, 8, 9,
10, 12, 13, 14): esta evaluación la generó el mismo asistente que
implementó los 4 fixes de la Sección 14 (commits en
`fix/seventh-independent-eval`, mergeados a `main` en `0357df2`). Mismo
método: tres revisores de código frescos en paralelo, sin acceso a este
archivo ni a mensajes de commit, instruidos a no confiar en comentarios
o notas ("ya está arreglado") y a verificar todo contra el código real,
contra `main` en `0357df2`, más mi propia relectura del documento y
verificación manual de los hallazgos más severos de cada revisor antes
de escribir esta sección.

### 15.1 Documento

Sin cambios de contenido desde la Sección 12 (solo el hash de
referencia, actualizado tres veces desde entonces, ahora `0357df2`).
**Evaluación del documento: 8/10, sin cambio.**

### 15.2 Código — tres revisores frescos, cada uno con hallazgos nuevos y genuinos

**Backend + DB + Scanner: 8,5/10** (sube de 8 — primera suba de esta
dimensión en el proyecto). Cero hallazgos Critical/High: los cuatro
fixes de la ronda anterior (sanitización de `cvss-score`, `delete_target`
atómico, más los ya sostenidos de rondas previas) se verificaron
directamente y se mantienen — el propio revisor probó explícitamente el
guard atómico de `delete_target` y la sanitización de CVSS y los
encontró correctos, no solo "según el comentario". Lo que impide un
puntaje más alto es que la misma disciplina de estas correcciones
—centralizar el saneo de un valor no confiable antes de que llegue a un
punto que puede fallar— no se generalizó a los vecinos estructuralmente
idénticos: `zap_normalizer.py:68` no castea `confidence` a `str` como sí
hace cada otro campo del mismo módulo, `nmap_normalizer.py:19` no
protege `int(item["port"])` con try/except pese a que el mismo patrón de
"un valor malo tira abajo toda la corrida" que motivó `sanitize_cvss_score`
aplica igual acá (mismo savepoint, mismo blast radius). Nuevo, genuino:
no existe ningún invariante contra dos scans concurrentes sobre el mismo
target (`scan_service.create_scan`/`pipeline_service.trigger_pipeline`
solo chequean `is_active`) — inconsistente con la disciplina de
concurrencia que el resto del código sí aplica (`complete_scan`,
`delete_target`), y con una consecuencia real contra DVWA porque
`dvwa_auth.get_authenticated_cookie` muta estado compartido del lado del
servidor (sesión de login, nivel de seguridad) que un segundo scan
concurrente también mutaría a mitad de corrida.

**Reports + n8n + Infraestructura: 7/10** (se mantiene). El fix de la
ronda anterior (`ScanInfo.error_message` llega ahora a los 3 formatos de
reporte) se verificó y sostiene. Hallazgo nuevo más severo de esta
ronda, verificado a mano: `Generate Report`, `Download Report` y
`Send Report Email` (`n8n/workflows/vulnscan-pipeline.json`) tienen
`continueOnFail: true` pero **ningún `retryOnFail`**, a diferencia de
`Complete Scan` (`retryOnFail: true, maxTries: 3`) — el mismo patrón de
"nodo de una sola llamada rápida, agregale reintento" que ya se aplicó
ahí y a los 3 nodos `Mark Scan Failed - *`, nunca generalizado a este
segundo cluster estructuralmente idéntico. Peor: el nodo terminal
`Pipeline Complete` arma un `message` diagnóstico ("Report: ... Email:
...") pero **no tiene ninguna conexión saliente** (confirmado: no
aparece como key en el objeto `connections` del JSON) — un scan puede
quedar `"completed"` en la base de datos sin que su reporte se haya
generado nunca y sin que el email se haya enviado nunca, y el único
rastro de esa falla es un campo que ningún sistema lee jamás. También
nuevo y verificado: ninguna de las rutas de error de n8n está cubierta
por CI — el job rápido (`ci.yml`) ni siquiera levanta `n8n`, y el job
E2E solo ejercita el camino feliz; los tres nodos `Code` con lógica no
trivial (`Resolve Pipeline Context`, `Select HTTP Port`, `Compare
Webhook Secret (Constant-Time)`) no tienen ningún test unitario en
ningún lado del repositorio.

**Frontend: 7/10** (sube de 6,5 — el fix de la ronda anterior sostiene
parcialmente, pero el mismo patrón reaparece sin corregir en dos lugares
más). El fix de la Sección 14 (`targetQuery`/`scanQuery` en
`TargetDetailPage`/`ScanDetailPage` comprueban `data` antes que `error`)
se verificó y se mantiene, con test de regresión real que fuerza un
refetch fallido después de un éxito. Pero el mismo revisor, instruido
específicamente a buscar este patrón en cualquier otra query de las
mismas páginas, encontró exactamente eso — verificado a mano, código
real, no solo el reporte del subagente: `ScanDetailPage.tsx:280-286`
(`tasksQuery`, la query de herramientas que hace polling cada 2s durante
todo el scan) sigue haciendo `tasksQuery.error ? <ErrorBanner/> :
<ToolTimeline/>` sin comprobar primero si `tasksQuery.data` (ya usado en
`breakdown`, línea 123) sigue disponible — el mismo archivo que ya
"sabe" resolver esto para `scanQuery`/`findingsQuery` no lo aplicó a su
tercera query. Y en `TargetsPage.tsx:194,234-254`, `scanHistoryFailed`
(derivado de `scanQuery?.error`) se comprueba antes que `latest`
(derivado de `scanQuery?.data`), ocultando un enlace al último scan ya
cargado detrás de "no se pudo cargar" ante un solo error transitorio de
polling. Ninguno de los dos casos tiene test de regresión, a diferencia
de los dos que sí se corrigieron. Hallazgo adicional, menor: la URL de
CVE (`ScanDetailPage.tsx:925-934`, `cve.source_url`) se renderiza como
`<a href>` sin validar el esquema — un feed de CVE comprometido podría
en teoría inyectar un `javascript:` href; mitigado por `target="_blank"
rel="noreferrer"` pero no eliminado.

### 15.3 Puntaje final: **7,7/10**

| Dimensión | Puntaje | Peso |
|---|---|---|
| Documento | 8/10 | ~35% |
| Backend + DB + Scanner | 8,5/10 | ~25% |
| Reports + n8n + Infraestructura | 7/10 | ~20% |
| Frontend | 7/10 | ~20% |

**Sube de 7,5 a 7,7**, empujado por el Backend (8→8,5, primera suba de
esa dimensión) y por el Frontend recuperando parte de su caída anterior
(6,5→7, ya que el hallazgo original de la ronda 7 está genuinamente
resuelto y probado). Esto **no** es evidencia de que el proyecto haya
alcanzado un techo de calidad — es, otra vez, la misma señal de las ocho
rondas: cada corrección puntual deja sin tocar a su vecino estructural
más cercano. El Frontend es el ejemplo más nítido hasta ahora: la ronda
7 corrigió el patrón `error`-antes-que-`data` en las dos queries
*principales* de dos páginas, y esta ronda lo encontró intacto en una
*segunda* query de la misma página (`ScanDetailPage`) y en una página
distinta (`TargetsPage`) — el fix nunca se generalizó a un helper o
convención compartida, se aplicó síntoma por síntoma.

Para una próxima ronda, en orden de impacto esperado: (1) las mismas
guardas `error`-antes-que-`data`, ahora en `tasksQuery`
(`ScanDetailPage.tsx`) y en las queries por-target de `TargetsPage.tsx`
— idealmente extraídas a un hook/patrón compartido esta vez, no
corregidas caso por caso otra vez; (2) `retryOnFail` en `Generate
Report`/`Download Report`/`Send Report Email`, más darle una salida real
al diagnóstico de `Pipeline Complete` (aunque sea un log estructurado o
un campo persistido, no solo una variable de ejecución que nadie lee);
(3) algún tipo de cobertura de CI para las rutas de error de n8n, aunque
sea un test que dispare el webhook con un secreto incorrecto y confirme
el 401 sin efectos secundarios; (4) el invariante de "un solo scan activo
por target", cerrando la brecha de concurrencia más concreta que quedó
en el backend.

**Estado de (3) al cierre de la ronda 8**: implementado — nueva función
`run_n8n_webhook_auth_check` en `scripts/integration_test.py`, verificada
en vivo contra el stack real (401 confirmado). (4) también implementado
— ver commit `93066de` (índice único parcial `ix_scans_one_active_per_target`).

## 16. Auditoría independiente del Documento + barrido de cierre de código (2026-08-28)

Después de la ronda 8, el usuario preguntó por qué seguir iterando sobre
código probablemente no movería mucho el promedio ponderado, y pidió un
plan que combine corrección de errores y revisión del documento,
priorizando lo de mayor impacto. Investigación previa al plan (agentes
Explore, solo lectura): un barrido de los 8 call sites de `useQuery`/
`useQueries` en el Frontend confirmó que la clase de bug `error`-antes-
que-`data` (rondas 7 y 8) está genuinamente cerrada — los 8 ya manejan
el patrón correctamente. Un barrido de `whatweb_normalizer.py` y
`nikto_normalizer.py` (los 2 normalizadores que ninguna ronda había
auditado para la clase de bug de saneo defensivo de `zap`/`nmap`/
`nuclei`) confirmó que ambos ya están limpios. De los 6 nodos IF de n8n,
solo 1 tenía cobertura de test — llevado a 2 esta ronda (ver más abajo).

Con el camino de código prácticamente agotado, el mayor impacto
disponible era el Documento: sin revisión de contenido fresca desde la
ronda 5 (solo el hash de referencia, actualizado 3 veces desde
entonces), y sus revisiones previas siempre las hizo el mismo asistente
que escribió las correcciones — útil, pero no "independiente" en el
mismo sentido que el código. Se lanzó un único revisor fresco de
propósito general (sin acceso a este archivo, a `docs/self-audit-
report.md`, ni al historial de commits), con el `.docx` extraído a
texto vía `pandoc` más acceso de lectura al repositorio real completo,
instruido con criterios genéricos de revisión académica (sin mencionar
el historial específico de este proyecto) y a verificar toda afirmación
técnica/cuantitativa contra el código y los datos reales antes de
confiar en ella.

### 16.1 Hallazgos del Documento (verificados a mano antes de reportarlos acá)

**Crítico — Anexo F (`docker-compose.yml`) y Anexo J (`.env.example`)
están desactualizados pese a presentarse como copia literal del
repositorio.** Verificado directamente contra los archivos reales en el
commit que el propio documento declara (`30693d9`): el bloque `backend`
real tiene `read_only: true`, `cap_drop: [ALL]`, `security_opt:
[no-new-privileges:true]` y las variables `N8N_WEBHOOK_SECRET`/
`N8N_CALLBACK_API_KEY` — ninguno de los cuatro aparece en la
reproducción del Anexo F. El bloque `n8n` real también tiene
`read_only`/`cap_drop`/`no-new-privileges`, ausentes igual en el anexo.
Anexo J, a la inversa, incluye `BACKEND_SECRET_KEY=change_me_local_dev_only`
— una variable que **no existe** en el `.env.example` real ni en ningún
código activo (fue eliminada en una ronda anterior por no tener uso).

**Crítico — Sección 17 (Trabajos Futuros) lista la notificación
automática de reportes por email como trabajo futuro; ya está
implementada y activa.** Verificado: `n8n/workflows/vulnscan-
pipeline.json` tiene un nodo real `Send Report Email` (tipo
`n8n-nodes-base.emailSend`, `disabled: false`, conectado desde
`Download Report`, con `retryOnFail`/`maxTries: 3` agregados en la
ronda 8), parte del flujo real `Generate Report → Download Report →
Send Report Email → Pipeline Complete`. La Sección 17 la agrupa junto a
la integración con Jira/ServiceNow/Redmine (esa sí genuinamente no
construida) como si ambas fueran trabajo pendiente.

**Alto — Anexo G subestima el tamaño real del workflow de n8n.**
Afirma "26 nodos, ~940 líneas"; el archivo real tiene **42 nodos y 1495
líneas** (verificado contando el JSON real). Los ~16 nodos no
contabilizados no son decorativos: incluyen `Check Webhook Secret`,
`Compare Webhook Secret (Constant-Time)`, `Respond OK`/`Respond
Unauthorized`, `IF: Invalid Pipeline Context`, `IF: Has Scan Id`, `IF:
Complete Scan Failed`, `Summarize Tool Failures` y `Send Report Email`
— todos nodos reales, conectados, que implementan lógica de seguridad y
manejo de fallos que el relato de 13 pasos del Anexo D nunca describe.

**Alto — Sección 13.2 / Tabla 15 describen un modelo de autenticación
de una sola clave compartida; el backend real ya implementa un modelo
de dos niveles más robusto que mitiga exactamente el riesgo discutido.**
Verificado: el texto solo menciona "el header X-API-Key obligatorio en
todo endpoint salvo /health". El código real (`backend/app/
security.py`, `callback_router` en `backend/app/routers/scans.py`)
separa `verify_api_key` (Frontend) de `verify_n8n_callback_key`
(`X-N8N-Callback-Key`/`N8N_CALLBACK_API_KEY`, solo para las 2 rutas que
n8n llama de vuelta) — precisamente para que la key del Frontend no
pueda falsificar la ingesta de resultados de scan. El Webhook Trigger
de n8n además está protegido por un secreto comparado en tiempo
constante (`N8N_WEBHOOK_SECRET`). Ninguno de los dos aparece en la
Tabla 15.

**Alto — Sección 11.7 / Anexo A no mencionan el nuevo invariante de
concurrencia de `scans` (ronda 8).** El índice único parcial
`ix_scans_one_active_per_target` (`database/models/scan.py`) no
aparece en la Tabla 7, en el SQL reproducido del Anexo A, ni en el
análisis de riesgos (13) o limitaciones (14) — un cambio de esquema y
comportamiento no reflejado.

**Medio — el "0% de recall" del Resumen/Abstract simplifica una
distinción metodológica que solo se aclara en la Sección 12.5.** Las
Tablas 12/13 muestran en realidad un recall de Nuclei/ZAP de 0,273 sin
autenticar (no 0%) — el 0% corresponde específicamente al nivel "alta
confianza" de un esquema de 3 niveles que la Sección 12.5 sí explica
correctamente después. No es una fabricación, pero el resumen ejecutivo
comprime la distinción de una forma que, leída antes que la Sección
12.5, parece contradecir las tablas.

**Medio — Anexo I muestra una salida de ejemplo (`"finding_type":
"web_vulnerability"`) que parece contradecir la corrección de
clasificación de la Sección 12.5**, porque la muestra es de un scan de
2026-08-15, anterior al fix real y vigente (`category.
from_zap_cweid`, verificado). No está señalado como muestra antigua.

**Bajo — Tabla 5 (endpoints principales) omite `GET /targets/
{target_id}/scans`**, que sí existe. Menor, dado que la tabla es
explícitamente no exhaustiva.

**Lo que se verificó limpio** (no relleno — vale decirlo): las Tablas 9
y 11, la campaña de seguimiento de Juice Shop (Sección 9.9), la Tabla 3
de versiones de librerías, y el esquema de la base de datos del Anexo A
coinciden con los artefactos reales (`scripts/measurement_campaign_
results/*.md`, `*/requirements.txt`, `database/models/*.py`) al
detalle. Las citas resuelven a venues/DOIs reales y plausibles.

**Evaluación honesta del documento**: metodológicamente es inusualmente
autocrítico para este tipo de trabajo (reporta el 0% de recall y la
ausencia del brazo manual sin maquillarlos), y sus afirmaciones
cuantitativas son trazables a artefactos reales, no inventadas. Su
debilidad es la vigencia: el código avanzó (hardening de contenedores,
modelo de dos claves, autenticación de webhook, un nodo de email activo,
un nuevo invariante de concurrencia) desde que los anexos y varias
secciones de prosa se sincronizaron por última vez — **aun cuando el
documento se ancla explícitamente a un commit que ya contiene todos
esos cambios**, socavando su propio encuadre de "verificado contra el
código real" justo en los lugares (Anexos F/G/J, Secciones 13.2/17)
donde esa afirmación se hace más explícita.

### 16.2 n8n — cobertura de test para `IF: Invalid Pipeline Context` + `IF: Has Scan Id`

De los 5 nodos IF sin cobertura identificados en la ronda 8, se agregó
test para el de mayor impacto verificado: `IF: Invalid Pipeline
Context` está en el único punto de convergencia de *toda* ejecución del
pipeline (si se rompe en silencio, afecta al 100% de los scans reales).
Verificado leyendo `Resolve Pipeline Context`: si falta `scan_id`,
`target_id` o `host`, marca `context_invalid: true` preservando
`scan_id` — `IF: Invalid Pipeline Context` (true) → `IF: Has Scan Id`
(true) → `Mark Scan Failed - Contexto Invalido`. Testeable sin tocar el
lab: crear un target/scan reales vía la API pública (sin pasar por
n8n), llamar al webhook con el secreto correcto pero sin el campo
`host`, y confirmar que el scan termina en `"failed"`. Nueva función
`run_n8n_invalid_context_check` en `scripts/integration_test.py`,
verificada en vivo contra el stack real (`OK` en ambos checks).

`IF: No HTTP Service Found` (requiere un target sin servicio HTTP,
inexistente en el whitelist actual — ampliar el lab para esto es
desproporcionado) y `IF: Target Lookup Failed` (solo camino manual/demo,
nunca producción) quedan sin test, documentado como limitación
aceptada. `IF: Complete Scan Failed` tampoco se testea (impacto
cosmético, `Complete Scan` ya tiene su propio retry).

**Estado al cierre**: los 8 hallazgos del Documento (§16.1) se
corrigieron en su totalidad esta misma sesión (plan dedicado, aprobado
y ejecutado) — ver §17.1 para el detalle de qué se aplicó y su
verificación.

## 17. Novena evaluación independiente (2026-08-28)

Con el Documento ya corregido (§16.1 aplicado en su totalidad) y los
3 barridos de código de §16.2 confirmando que las clases de bug de las
rondas 7-8 seguían cerradas, el usuario pidió correr una novena ronda
formal (3 revisores de código frescos + relectura del documento) contra
`main` en `3660006`, mismo método de siempre.

### 17.1 Documento

Las 8 correcciones de §16.1 se aplicaron directamente al `.docx` esta
sesión: Anexos F/J re-pegados completos desde los archivos reales
actuales (hardening de contenedores, modelo de 2 claves, sin
`BACKEND_SECRET_KEY`); Sección 17 ya no lista la notificación por email
como trabajo futuro (Sección 11.6 documenta el nodo `Send Report Email`
real); Anexo G corregido a 42 nodos/1495 líneas; Sección 13.2 + Tabla 15
documentan el modelo de auth de 2 niveles; Tabla 7 menciona el nuevo
índice de concurrencia; Sección 12.5 aclara alta-confianza vs. recall
global; Anexo I reemplazado por una muestra real generada en vivo esta
sesión (confirma visualmente que la clasificación y la evidencia de ZAP
ya no muestran el bug pre-fix); Tabla 5 completa. Verificado: conteos
estables, TOC/campos intactos, hash de referencia actualizado a
`3660006`, copia de entrega re-sincronizada. **Evaluación del
documento: 8/10** — mismo valor que rondas anteriores, pero ahora
respaldado por una auditoría fresca real en vez de "sin cambios desde
la ronda 5."

### 17.2 Código — tres revisores frescos, cada uno con hallazgos nuevos y genuinos

**Backend + DB + Scanner: 7/10** (baja de 8,5 — hallazgo Alto nuevo y
verificado a mano). `POST /scans/{id}/tasks` (`scan_task_service.
ingest_scan_task`) no es idempotente — inserta un `ScanTask` nuevo y
corre el normalizador completo sin chequear si ya existe uno para el
mismo `(scan_id, tool_name)` (el índice `ix_scan_tasks_scan_id_tool_name`,
verificado, es un índice plano, no único). Verificado también en el
workflow real: los 5 nodos `Ingest: *` tienen `retryOnFail: true,
maxTries: 3` con un timeout de solo 30s (`n8n/workflows/vulnscan-
pipeline.json`) — si la respuesta del Backend se demora más de eso
(plausible: `raw_output` puede llegar a 50MB, y `create_finding`/
`create_cve_reference` insertan fila por fila sin bulk insert), n8n
reintenta la misma llamada y el Backend no tiene forma de reconocerla
como un reintento: duplica `Finding`/`CveReference` de esa herramienta.
Es exactamente la misma clase "un reintento no debe duplicar el
efecto" que ya se resolvió dos veces en código vecino (`scans.status`
vía UPDATE condicional, `delete_target` vía índice único parcial) pero
nunca se generalizó al endpoint de ingesta — y es el que la propia
configuración de reintentos del pipeline más directamente ejercita.
Corrompe además la métrica que la tesis mide (recall/precisión), no es
solo un problema de performance. Sin hallazgos Critical.

**Reports + n8n + Infraestructura: 7/10** (se mantiene). Dos hallazgos
Alto reafirmados/profundizados: (1) el secreto del webhook de n8n
falla abierto si `N8N_WEBHOOK_SECRET` está vacío (cadenas de longitud
0 comparadas producen `secret_matches: true`) — mitigado hoy solo por
un efecto colateral del orden de arranque de `docker-compose.yml` (el
Backend no levanta con el secreto vacío, y n8n depende de que el
Backend esté healthy), no por una guarda propia del lado de n8n; (2)
`Generate Report → Download Report → Send Report Email` siguen sin el
mismo gate de "no continuar si el paso anterior falló" que sí se aplicó
un paso antes (`IF: Complete Scan Failed`) — reafirma el hallazgo ya
documentado en la ronda 8 como limitación aceptada, ahora con más
detalle (el `message` de diagnóstico de `Pipeline Complete` sigue sin
destino). Nuevo hallazgo Medio: `confidence`/`cvss_score` de cada
finding se normalizan pero nunca se renderizan en HTML/MD/PDF (solo en
JSON, como efecto colateral de volcar el modelo completo).

**Frontend: 8/10** (sube de 7 — techo histórico, ahora por razones
verificadas). El barrido explícito de los 8 call sites de `useQuery`/
`useQueries` confirma que la clase `error`-antes-que-`data` está
genuinamente cerrada en toda la app, con test de regresión por cada
caso. Hallazgo Medio nuevo: `stripAnsi` se aplica al `error_message` de
`ToolTimeline` pero no a las 3 apariciones estructuralmente idénticas
en `ScanBanner` ni a la tabla de historial de `TargetDetailPage` — el
mismo patrón "arreglado en un lugar, no en el vecino" una vez más, esta
vez en el frontend. También: `ConfirmDialog` no restaura el foco al
cerrarse (gap real de accesibilidad, sin test que lo cubra).

### 17.3 Puntaje final: **7,6/10**

| Dimensión | Puntaje | Peso |
|---|---|---|
| Documento | 8/10 | ~35% |
| Backend + DB + Scanner | 7/10 | ~25% |
| Reports + n8n + Infraestructura | 7/10 | ~20% |
| Frontend | 8/10 | ~20% |

**Baja de 7,7 a 7,6** — casi neutro en el promedio pese a movimientos
reales en las cuatro dimensiones: Backend cae (8,5→7, el hallazgo de
idempotencia de ingesta) y Frontend sube (7→8, su techo histórico) se
cancelan casi exactamente por peso; Documento se mantiene en el mismo
número pero ahora por una razón sustancialmente mejor (auditoría fresca
real, no ausencia de cambios). El patrón de las 9 rondas se sostiene:
ningún barrido de código, por prolijo que sea, agota la clase de
hallazgo que un revisor genuinamente fresco puede encontrar — esta vez
le tocó a la idempotencia de un endpoint que el propio pipeline
reintenta, un ángulo que ninguna de las 8 rondas anteriores había
mirado.

Para una próxima ronda, en orden de impacto esperado: (1) idempotencia
de `POST /scans/{id}/tasks` (mismo patrón de índice único parcial o
UPSERT ya usado en este código para `services`, aplicado a
`scan_tasks`/`findings`); (2) el secreto del webhook de n8n debería
fallar cerrado con una guarda propia (no solo por el orden de arranque
de `docker-compose.yml`); (3) el mismo gate de "no continuar tras un
fallo" ya aplicado a `Complete Scan → Generate Report`, generalizado a
`Generate Report → Download Report → Send Report Email`; (4) `stripAnsi`
generalizado a los otros 4 lugares que renderizan `error_message`; (5)
restauración de foco en `ConfirmDialog` al cerrarse.
