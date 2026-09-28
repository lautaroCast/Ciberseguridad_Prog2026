# Corridas citadas por el informe final

Este directorio conserva los artefactos crudos de las tres corridas que el Capítulo 12
del informe reporta, identificadas por su `scan_id`:

| Condición | `scan_id` | Hallazgos | Tablas del informe |
|---|---|---|---|
| DVWA sin autenticar | `f9760239…` | 32 | 15, 19 (col. DVWA), 20 |
| DVWA autenticado | `0a605f82…` | 56 | 17, 18, 19 (col. autenticado), 20 |
| OWASP Juice Shop | `c2421b99…` | 28 | 16, 19 (col. Juice Shop), 20 |

Los archivos `_findings.json` y `_tasks.json` son la salida cruda del pipeline y no se
han modificado. Los `_match_report.json` de este directorio **se recalcularon con la
versión actual de `match_findings.py`** el 2026-09-28.

## Advertencia sobre la versión del comparador

El comparador y los catálogos se revisaron el 2026-08-24 (commit `d285e67`). Las cifras
de recall, precisión y F1 que el informe reporta se calcularon con la versión anterior.
Sobre los mismos hallazgos, la versión actual produce valores distintos:

| Condición | Precisión ZAP / Nuclei / Nikto | Sin correspondencia |
|---|---|---|
| DVWA — informe | 0,92 / 0,70 / — | 21,9 % |
| DVWA — comparador actual | 0,50 / 0,10 / — | 75,0 % |
| DVWA aut. — informe | 0,73 / 0,79 / 0,47 | 32,1 % |
| DVWA aut. — comparador actual | 0,36 / 0,05 / 0,00 | 83,9 % |
| Juice Shop — informe | 0,83 / 0,00 / 0,11 | 78,6 % |
| Juice Shop — comparador actual | 0,83 / 0,00 / 0,11 | 78,6 % |

La diferencia no procede de los hallazgos, que son los mismos, sino del criterio de
correspondencia entre un hallazgo y una entrada del catálogo. Es la situación que la
Sección 8.9 del informe describe: un recall no es interpretable sin declarar con qué
criterio se emparejó.

Los artefactos `sample_run_*` del directorio padre corresponden a **otras corridas**
—entre ellas una corrida autenticada del 2026-08-24, de 55 hallazgos— y no son las que
el informe reporta.
