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

## Estado actual (5ª evaluación independiente, 2026-08-24): el 0% de recall de alta confianza era un artefacto del matching, no de detección

**Corrección importante sobre las dos secciones que siguen** (dejadas
más abajo, sin editar, como registro histórico de lo que se creía antes
de esta corrección): el "recall real 0%" que se citaba en la tesis y en
esta misma página resultó ser, tras una revisión independiente
(`docs/independent-evaluation-report.md` §10-12), un artefacto de tres
problemas reales en el propio script de matching y los normalizadores
— no una limitación genuina de las herramientas de escaneo:

1. **`finding_type` era una cadena plana por herramienta**
   (`"web_vulnerability"` para todo ZAP, `"web_misconfiguration"` para
   todo Nikto, el tipo de protocolo crudo para Nuclei) — nunca podía
   coincidir con el vocabulario real de los catálogos
   (`injection`/`xss`/`security_misconfiguration`/...), así que el
   nivel 2 (tipo+ubicación) de `match_findings.py` no podía disparar
   *nunca*, sin importar cuán correcto fuera el hallazgo. Corregido:
   `backend/app/normalization/category.py`, clasificación real por
   CWE (ZAP), texto del mensaje (Nikto) y tags de template (Nuclei).
2. **ZAP descartaba la URI de cada instancia**, dejando solo el texto
   de evidencia — el nivel 2 tampoco tenía con qué comparar la
   ubicación aunque `finding_type` ahora sí coincidiera. Corregido:
   `zap_normalizer.py` conserva la URI de cada instancia.
3. **El nivel 3 (keyword) asignaba por orden de archivo, no por
   especificidad** — dos entradas de catálogo que comparten una palabra
   demasiado genérica (ej. "injection" en más de una entrada de DVWA)
   dejaban que la que aparece primero en el JSON se quedara con el
   finding, aunque la otra fuera la coincidencia correcta. Corregido:
   los candidatos se recolectan globalmente y se asignan por
   especificidad (más keywords coincidentes gana).

**Resultado real, medido de nuevo tras estas 3 correcciones** (corrida
autenticada Nikto+Nuclei+ZAP contra DVWA, scan real, ver
`sample_run_dvwa_authenticated_match_report.json`):

| Herramienta | Recall | Precisión | Desglose por nivel |
|---|---|---|---|
| ZAP | 90,9% (10/11 entradas) | 54,5% | 4 tipo+ubicación (nivel 2, alta confianza), resto keyword |
| Nuclei | 9,1% | 5,6% | 1 keyword |
| Nikto | 0% | 0% | — |

**Las 11 entradas del catálogo de DVWA quedaron cubiertas** (0 sin
cubrir) contra el escaneo autenticado — un cambio real frente al 0% de
recall de alta confianza reportado en las secciones históricas de abajo.
4 de esos matches son ahora de nivel 2 (tipo+ubicación, confianza media-
alta, antes estructuralmente imposible), no solo nivel 3. Nikto en 0%
sigue siendo un hallazgo honesto y real: sus 15 hallazgos son
misconfiguraciones/banners genéricos, ninguno coincide con las 11
categorías del catálogo (SQLi/XSS/CSRF/etc.) — Nikto no está diseñado
para probar esas clases de vulnerabilidad activamente.

**Juice Shop, tras la misma corrección**: el efecto fue distinto. La
primera versión de esta corrección generó 10 "matches" nuevos, pero al
revisarlos a mano resultaron ser en su mayoría falsos positivos —
palabras genéricas de las descripciones completas de los challenges
(`"with"`, `"your"`, `"which"`, ...) colándose como keywords y matcheando
hallazgos genéricos de Nikto (ej. "Suggested security header missing")
contra desafíos de XSS/inyección sin relación real. Corregido con una
lista de stopwords y una regla más estricta (el texto de la descripción
solo se usa cuando el nombre + las palabras semilla de categoría no
alcanzan). Resultado final, honesto: **1 match real** (nivel 3) contra
la corrida estándar sin autenticar — el recall de Juice Shop sigue
siendo bajo porque el pipeline estándar (no autenticado, ZAP en modo
pasivo) genuinamente no genera muchos hallazgos de las categorías
cubiertas por el catálogo, no por un problema de matching.

**Lección para la próxima vez que se toque este matcher**: una
corrección de "vocabulario demasiado pobre" puede fácilmente
sobrecorregir hacia "vocabulario demasiado amplio" (cualquier palabra
de 4+ letras de una oración completa). Verificar cada match nuevo a
mano contra el finding real antes de confiar en que un número más alto
es una mejora genuina — exactamente lo que este mismo proyecto ya
aprendió con el sesgo de escala de severidad.

## Secciones históricas (antes de la corrección — contexto, no vigente)

### Hallazgo importante, ya superado (léer antes de citar cualquier número de DVWA)

**Todas las páginas de módulos vulnerables de DVWA exigen sesión
autenticada.** Confirmado empíricamente en esta sesión: una request sin
autenticar a `/vulnerabilities/sqli/` devuelve `302 Found` →
`Location: ../../login.php`. El pipeline **estándar** (no autenticado)
escanea sin sesión (ver `docs/security.md` y §14.2 de la tesis) — pero
la Recomendación #5 ya agregó un modo de escaneo autenticado opcional
(`options.authenticated: true`), usado en la corrida que sí demuestra
recall real arriba. Este párrafo describe el estado *sin* ese modo.

La corrida de muestra sin autenticar (`sample_run_dvwa_*.json`, contra el
scan real `f9760239-...` de una sesión anterior) mostraba **el 100% de
los 25 matches de nivel 3 (keyword débil)** — cero por CVE o
tipo+ubicación. Con el matcher de esa época (antes de las 3 correcciones
de arriba), ese número no distinguía "el matching es ruido" de "el
matching está estructuralmente roto" — ambos producían el mismo
síntoma. La sección de arriba resuelve esa ambigüedad: con el matcher
corregido, el escaneo autenticado sí produce matches de nivel 2 reales.

### Juice Shop: mismo síntoma histórico, causa distinta

Se corrió también contra Juice Shop (`sample_run_juice_shop_*.json`,
scan real `c2421b99-...` de una sesión anterior, producido con
`_run_juice_shop_scan.py`). Juice Shop no tiene el problema de
autenticación de DVWA — sus páginas son alcanzables sin sesión por
diseño — pero el resultado histórico también era 100% nivel 3. Ver la
sección de arriba para el resultado re-medido con el matcher corregido:
la causa allí sí era mayormente un desalineamiento de vocabulario en el
propio catálogo (`description_keywords` derivados del nombre narrativo
del challenge, no de su categoría técnica), ya corregido en
`build_juice_shop_catalog.py`. Ver
`docs/audit-corrections/C-09.md` para el tratamiento original completo
con ambos targets.

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
