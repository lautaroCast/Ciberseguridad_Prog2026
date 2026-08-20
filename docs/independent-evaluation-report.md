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
