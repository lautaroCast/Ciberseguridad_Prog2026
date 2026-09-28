# Campañas de medición — correspondencia con el informe final

Cada campaña deja dos archivos: `<timestamp>.json` con los datos crudos por corrida
(tiempos por herramienta, orquestación, recuentos y distribución de severidad) y
`<timestamp>_summary.md` con el resumen legible y el entorno capturado en vivo.

Se generan con `scripts/run_measurement_campaign.sh`, que envuelve a
`scripts/measurement_campaign.py`.

## Campañas analizadas en el informe

| Artefacto | Etiqueta en el informe | Fecha | Objetivo | Corridas | Anfitrión |
|---|---|---|---|---|---|
| `20260811T004104Z` | Campaña A | 2026-08-11 | DVWA | 5 | AMD Ryzen 7 5700U / Windows 11 |
| `20260824T172108Z` | Campaña B | 2026-08-24 | OWASP Juice Shop | 5 | Apple M5 / macOS 26.6 |
| `20260824T193554Z` | Campaña C | 2026-08-24 | DVWA | 5 | Apple M5 / macOS 26.6 |

Son las tres campañas de las Secciones 12.3 a 12.6 del informe. La campaña A sostiene
las Tablas 11, 12 y 14; las campañas B y C sostienen la Tabla 21 y la Sección 12.6, y la
media de la campaña C es la referencia automatizada de la Tabla 13.

## Campañas presentes pero no integradas al análisis

| Artefacto | Fecha | Objetivo | Corridas | Por qué no se integra |
|---|---|---|---|---|
| `20260822T182945Z` | 2026-08-22 | OWASP Juice Shop | 5 (1 fallida) | Ejecución preliminar previa a las campañas B y C; la captura de entorno falló y no registró versiones ni anfitrión. |
| `20260915T060044Z` | 2026-09-15 | DVWA | 15 | Corrió sobre código del Servicio de Escaneo posterior al commit `0357df2` que el informe declara. |
| `20260916T032812Z` | 2026-09-16 | OWASP Juice Shop | 10 (1 fallida) | Ídem. |

La Sección 12.6.4 del informe las declara, explica el motivo de exclusión y analiza qué
muestran sus datos sobre la tasa de fallos parciales silenciosos y sobre la atribución
causal de la Sección 12.6.3.

## Procedencia y trazabilidad

Cada JSON registra en `environment.captured_at` la marca temporal de su propia captura.
Los artefactos de las tres campañas analizadas se capturaron en agosto de 2026 y se
incorporaron a este repositorio el 24 de septiembre de 2026, en el commit que publica
este directorio. La diferencia entre ambas fechas es de publicación, no de medición.

El script de medición **no registra el identificador de revisión del repositorio**
vigente durante cada campaña. La correspondencia se reconstruye desde `captured_at` y
el historial de `main`, y es la siguiente:

| Campaña | `captured_at` (UTC) | Estado de `main` | Fecha del commit |
|---|---|---|---|
| A | 2026-08-11 00:18 | `aadd368` | 2026-08-06 |
| B | 2026-08-24 16:59 | `b0a1bd3` | 2026-08-23 |
| C | 2026-08-24 19:21 | `ecb6d42` | 2026-08-24 |

Ninguna de las tres corrió sobre `0357df2` (etiqueta `tesis-entrega`), que describe el
estado del código al cierre del período de medición. Entre la campaña A y ese commit
median 89 commits, con seis cambios en `backend/app/normalization/`. La Sección 20 del
informe declara esta correspondencia.

Registrar la revisión en curso dentro de cada artefacto está propuesto como trabajo
futuro en la Sección 17 del informe.

## Brazo manual

Las dos corridas cronometradas del proceso manual de referencia (Tabla 10 del informe)
no pasan por este script: se registraron a mano con la hoja del Anexo K. Su transcripción
está en `docs/manual-run-sheets/`.
