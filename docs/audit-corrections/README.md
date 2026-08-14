# Paquete de correcciones — auditoría externa de la tesis

Corrige los hallazgos de `Auditoria_Tesis_VulnScan_Racconto_Castillo.pdf`
(3,6/10, 96 hallazgos, 18 críticos) acotado a los **tramos 1-8** de los 12
que prioriza el propio auditor (§19) — el auditor estima que completar
1-8 lleva la tesis a ~6,5/10. Formato APA, publicación del repositorio y
pulido de redacción (tramos 9-12) quedan fuera de esta ronda, con la
excepción de la bibliografía (ver nota abajo).

**Formato de entrega:** paquete Markdown "antes → después" por hallazgo,
no una edición directa del .docx/PDF de la tesis (no hay herramienta para
eso en este entorno). El usuario traslada cada "texto nuevo" al documento
final a mano.

**Corrección de scope (2026-08-10):** una primera versión de este
directorio (2026-08-06) marcó la bibliografía (C-16, C-17) como fuera de
alcance, "tramo 9-12". Era una lectura errónea de la tabla de prioridades
real del auditor — es Prioridad 5, dentro de los tramos 1-8. Corregido
tras releer el informe completo; ver `hidden-floating-lagoon.md` (el plan
maestro, fuera de este repo) para el detalle de la corrección.

## Índice de hallazgos críticos (18/18)

| # | Hallazgo | Tramo | Estado | Archivo |
|---|---|---|---|---|
| C-01 | El capítulo de resultados no contiene ningún dato | 1 | fixed-in-docs | `C-01.md` |
| C-02 | Marcador editorial en Resumen/Abstract | 11 | **out-of-scope** | `C-02.md` |
| C-03 | Nueve pasajes afirman en pasado haber medido | 3 | fixed-in-docs | `C-03.md` |
| C-04 | Las tres hipótesis quedan sin contrastar | 1, 4 | fixed-in-docs | `C-04.md` |
| C-05 | Objetivo general declarado alcanzado sin evidencia | 3 | fixed-in-docs (en `C-03.md`) | `C-03.md` |
| C-06 | H3 no es falsable | 4 | fixed-in-docs | `C-06.md` |
| C-07 | Umbral del 50% de H1 sin presupuesto temporal | 4 | fixed-in-docs (en `C-04.md`) | `C-04.md` |
| C-08 | "Espera activa" imputada al brazo manual | 10 | resuelto por eliminación | `C-08.md` |
| C-09 | Sin verdad de referencia (recall/precisión/FP) | 2 | fixed-in-docs | `C-09.md` |
| C-10 | ZAP quickscan ciego frente a Juice Shop (SPA) | 8 | fixed-in-docs | `C-10.md` |
| C-11 | Escala de severidad estructuralmente sesgada | 8 | fixed-in-docs | `C-11.md` |
| C-12 | Contradicción interna "defensa en profundidad" | 7 | fixed-in-docs | `C-12.md` |
| C-13 | Whitelist no reside donde está la capacidad de red | 7 | **fixed-in-code** + fixed-in-docs | `C-13.md` |
| C-14 | API sin autenticación no analizada | 8 | fixed-in-docs (ya resuelto en Módulo 9) | `C-14.md` |
| C-15 | "Ninguna lógica de negocio en n8n" desmentido | 7 | fixed-in-docs | `C-15.md` |
| C-16 | Referencia fabricada (Hussain et al.) | 5 | fixed-in-docs | `C-16.md` |
| C-17 | Segunda referencia no verificable (Sharma y Bahl) | 5 | fixed-in-docs | `C-17.md` |
| C-18 | Cero figuras y cero imágenes | 6 | fixed-in-docs | `C-18.md` |

## Hallazgos altos (A-XX) cubiertos dentro de los tramos 1-8

No tienen archivo propio — se resolvieron plegados dentro del `C-XX.md`
temáticamente más cercano, para no duplicar el esquema de archivos:

| Hallazgo | Resuelto en |
|---|---|
| A-05 (número de hallazgos ≠ cobertura) | `C-09.md` |
| A-06, A-07 (H2 mal operacionalizada) | `C-04.md` |
| A-11 (specs de la máquina anfitriona) | `C-01.md` |
| A-12 (versiones de herramientas + plantillas de Nuclei) | `C-01.md` |
| A-17, A-18, A-19, A-21, A-22 (densidad de citas, huérfanas, actualidad, discusión sin citas, estado del arte) | `bibliography.md` |
| A-27 (contradicción "sin estado" del Reports Service) | resuelto en `docs/security.md`, commit `fd0be87` |
| A-29 (precedencia CVSS score vs. etiqueta) | `C-11.md` |
| A-38 (frontend representado como inexistente en el diagrama) | `C-18.md` (ya no aplica: Frontend implementado) |
| A-39 (sin capturas del producto del sistema) | `C-18.md` (resuelto) |

Otros hallazgos altos dentro de 1-8 pero fuera del alcance elegido por el
usuario para esta ronda (documentados como tal, no omitidos): A-08, A-09,
A-10 (amenazas a la validez, contradicción §9.7/§14.3 — tramo 10);
A-13, A-14, A-15 (repositorio y artefactos de despliegue — tramo 9).

## Fuera de alcance (tramos 9-12, decisión explícita del usuario)

Formato APA, sangría francesa, numeración de páginas, rotulado de las 19
tablas, publicación del repositorio, consolidación de los capítulos 1-3,
y el resto de los hallazgos M-XX/B-XX de redacción y formato. Ver
`C-02.md` como ejemplo documentado de un hallazgo específico dejado
fuera.

## Datos y artefactos que respaldan este paquete

- `scripts/measurement_campaign_results/` — campaña de medición real (5
  corridas contra `dvwa`, entorno completo capturado programáticamente).
- `scripts/ground_truth/` — catálogos de verdad de referencia (Juice
  Shop, DVWA) y matcher de recall/precisión/F1.
- `figures/` — diagramas de componentes, DER y secuencia del pipeline,
  renderizados como PNG reales.
- `bibliography.md` — 10 referencias arbitradas reales, verificadas
  contra Crossref, que reemplazan a las dos fabricadas/no verificables.

## Verificación

Ver Fase 7 del plan maestro (`hidden-floating-lagoon.md`, fuera de este
repo) para la lista completa de criterios de aceptación por hallazgo y el
repaso final contra las "preguntas que hará el tribunal" del propio
informe de auditoría.
