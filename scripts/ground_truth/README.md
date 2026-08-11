# Ground truth: recall/precisión/F1 por herramienta (auditoría, hallazgo C-09)

Responde al hallazgo C-09 de la auditoría externa: la tesis nunca midió qué
proporción de las vulnerabilidades *reales* de Juice Shop/DVWA detecta cada
herramienta, ni cuántos falsos positivos produce — solo contaba hallazgos,
que el propio auditor señala que no es lo mismo que cobertura.

## Contenido

- `juice_shop_challenges_raw.yml` — el catálogo oficial de challenges de
  Juice Shop, extraído *tal cual* del contenedor real en ejecución
  (`docker exec vulnscan-juice-shop ... fs.readFileSync('/juice-shop/data/static/challenges.yml')`),
  no reescrito a mano.
- `build_juice_shop_catalog.py` — filtra ese catálogo a las categorías
  plausiblemente detectables por Nmap/WhatWeb/Nikto/Nuclei/ZAP (ver su
  propio docstring para la justificación categoría por categoría) y
  produce `juice_shop_catalog.json` (52 entradas).
- `build_dvwa_catalog.py` — construye el catálogo de DVWA a partir de la
  estructura real de directorios de módulos vulnerables del contenedor
  (`docker exec vulnscan-dvwa ls /var/www/html/vulnerabilities/`), produce
  `dvwa_catalog.json` (11 entradas).
- `match_findings.py` — matchea hallazgos reales del pipeline contra un
  catálogo, en 3 niveles de confianza (CVE exacto → tipo+ubicación →
  keyword débil, nunca mezclados en un solo número), y calcula
  recall/precisión/F1/FPR por herramienta más solapamiento entre
  herramientas.

## Hallazgo importante ya confirmado (léer antes de citar cualquier número de DVWA)

**Todas las páginas de módulos vulnerables de DVWA exigen sesión
autenticada.** Confirmado empíricamente en esta sesión: una request sin
autenticar a `/vulnerabilities/sqli/` devuelve `302 Found` →
`Location: ../../login.php`. El pipeline actual escanea **sin
autenticar** (ver `docs/security.md` y §14.2 de la tesis). Esto significa
que, tal como está desplegado el sistema hoy, **ninguna de las 11
entradas del catálogo de DVWA es alcanzable en la práctica** —
`reachable_unauthenticated: false` en las 11. Ver el docstring de
`build_dvwa_catalog.py` para el detalle completo.

La corrida de muestra incluida (`sample_run_dvwa_*.json`, contra el scan
real `f9760239-...` de una sesión anterior) lo confirma: **el 100% de los
25 matches obtenidos son de nivel 3 (keyword débil)** — cero matches por
CVE o por tipo+ubicación (`match_tier_breakdown` en
`sample_run_dvwa_match_report.json`). Es decir, el recall no-nulo que
muestra el reporte de muestra (~27% por herramienta) es ruido de matching
por palabra clave, no evidencia real de que las herramientas alcanzaron
una página vulnerable — coherente con el hallazgo del párrafo anterior.
El recall real contra páginas efectivamente alcanzables es 0%, y esa es
la cifra que debe citarse en la tesis, con esta explicación.

Esto es en sí mismo un hallazgo legítimo para el capítulo de resultados y
limitaciones: el pipeline, tal como está, no puede evaluar su cobertura
real de detección contra DVWA porque nunca llega a ver una página
vulnerable. Una línea de trabajo futuro distinta de "escaneos
autenticados" ya declarada: un paso de login previo en el pipeline antes
de invocar las herramientas web.

## Juice Shop: mismo síntoma, causa distinta

Se corrió también contra Juice Shop (`sample_run_juice_shop_*.json`,
scan real `c2421b99-...`, producido con
`_run_juice_shop_scan.py` — a diferencia de DVWA, este sí tiene un script
dedicado para reproducirlo). Juice Shop no tiene el problema de
autenticación de DVWA — sus páginas son alcanzables sin sesión por
diseño — pero el resultado es el mismo: **el 100% de los 6 matches
obtenidos también son de nivel 3 (keyword débil)**, cero por CVE o
tipo+ubicación. El recall aparente más alto fue 7,7% (ZAP). Como no hay
un impedimento de acceso que lo explique, la causa más probable es un
desalineamiento de vocabulario entre los catálogos oficiales (nombres de
desafíos OWASP) y las descripciones que las propias herramientas generan
para sus hallazgos — el matching por texto libre (nivel 3) no tiende ese
puente de forma confiable. Ver
`docs/audit-corrections/C-09.md` para el tratamiento completo con ambos
targets y la redacción final para la tesis.

## Cómo correr esto contra un scan real

```bash
# Dentro del contenedor backend (mismo patrón que integration_test.py)
docker compose exec backend python scripts/ground_truth/match_findings.py \
  --findings-json <findings.json de GET /scans/{id}/findings> \
  --scan-tasks-json <tasks.json de GET /scans/{id}/tasks> \
  --catalog-json scripts/ground_truth/dvwa_catalog.json \
  --target-label dvwa \
  --output resultado.json
```

`sample_run_dvwa_findings.json` / `sample_run_dvwa_tasks.json` /
`sample_run_dvwa_match_report.json` son la salida real de esa corrida
contra el scan `f9760239-f342-44c1-9486-21aa0aa125b5` — quedan como
evidencia reproducible, no como parte de la campaña de medición formal
(esa vive en `scripts/measurement_campaign_results/`, Fase 4).

## Limitación honesta del propio matching

El nivel 3 (keyword) puede producir tanto falsos positivos (coincidencia
casual de una palabra) como falsos negativos (una detección real descrita
con otras palabras). Cualquier número de recall/precisión que dependa
mayoritariamente del nivel 3 debe tratarse como indicativo, no como
prueba — por eso el script siempre reporta el desglose por nivel
(`match_tier_breakdown`) en vez de un solo número ciego.
