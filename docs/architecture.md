# Arquitectura y plan de desarrollo

Vista general de cómo está armado VulnScan Platform y por qué, pensada
como punto de entrada: cada sección enlaza al documento o `README.md` de
servicio que tiene el detalle completo, en vez de repetirlo acá.

## Qué resuelve

Automatiza el ciclo completo de un análisis de vulnerabilidades sobre
aplicaciones vulnerables desplegadas localmente: reconocimiento →
identificación de tecnologías → escaneo → normalización → clasificación
por severidad → persistencia → generación de reportes → notificación.
Ver [`docs/lab.md`](lab.md) para el alcance legal (solo laboratorio
local, nunca sistemas de terceros).

## Vista de servicios

```
Frontend (React/TS) → Backend API (FastAPI) → n8n (orquestador)
                              ↓                      ↓
                         PostgreSQL          Scanner Service
                              ↑          (Nmap · Nuclei · Nikto · WhatWeb · ZAP)
                              │                      │
                       Reports Service ◄─────────────┘
                    (PDF · HTML · Markdown · JSON)
```

| Servicio | Responsabilidad | Documento |
|---|---|---|
| **Frontend** | Dashboard React + TypeScript: CRUD de targets, disparo del pipeline, findings, descarga de reportes | [`frontend/`](../frontend) |
| **Backend** | Único punto público de la API: targets, scans, ingesta/normalización de resultados, reportes | [`backend/README.md`](../backend/README.md) |
| **Scanner Service** | Ejecuta Nmap/WhatWeb/Nikto/Nuclei/ZAP, sin estado propio, sin base de datos | [`scanner/README.md`](../scanner/README.md) |
| **Reports Service** | Renderiza PDF/HTML/Markdown/JSON a partir de un payload autocontenido, sin estado propio | [`reports/README.md`](../reports/README.md) |
| **n8n** | Orquesta el pipeline de 12 etapas llamando al Backend y al Scanner por HTTP — sin lógica de negocio propia | [`n8n/README.md`](../n8n/README.md) |
| **PostgreSQL** | Persiste todo el ciclo de vida (targets → scans → findings → reportes) | [`docs/database.md`](database.md) |
| **Lab (Juice Shop + DVWA)** | Aplicaciones vulnerables de laboratorio, red segmentada | [`lab/README.md`](../lab/README.md) |

## Principios de arquitectura

- **Desacoplamiento por contrato HTTP** entre todos los servicios — nada
  comparte base de datos ni sistema de archivos salvo lo explícitamente
  documentado (ver "Por qué push, no pull" en
  [`reports/README.md`](../reports/README.md)).
- **n8n como orquestador, no como ejecutor**: la lógica de negocio
  (whitelist, normalización, clasificación de severidad) vive en código
  Python versionado; n8n solo llama a esa lógica en el orden correcto.
  Ver [`n8n/README.md`](../n8n/README.md).
- **Patrón plugin en el motor de escaneo y en la normalización**: agregar
  una herramienta nueva es un adapter + una línea de registro, no tocar
  las herramientas existentes. Ver la sección "The plugin pattern" en
  [`scanner/README.md`](../scanner/README.md) y
  ["Normalization and severity classification"](../backend/README.md)
  en el Backend.
- **Laboratorio en red segmentada** (`lab-network`): solo el Scanner
  Service la conecta con el resto de la plataforma. La garantía real de
  "nunca escanear nada fuera del laboratorio" la da la whitelist del
  Backend, no la topología de red — ver [`docs/lab.md`](lab.md).
- **El Backend es el único punto público de la API.** n8n no se expone al
  frontend directamente; su Form Trigger es un atajo de desarrollo/demo,
  no una vía de producción. Ver "Why the trigger isn't exposed directly
  to the frontend/user" en [`n8n/README.md`](../n8n/README.md).
- **Extensible sin romper nada**: nuevas herramientas, nuevas apps
  vulnerables o nuevos formatos de reporte se agregan como módulos
  nuevos, sin modificar los existentes. Ver la skill
  `add-scanner-tool` en `.claude/skills/` para el checklist concreto de
  agregar una herramienta.

## El pipeline de 12 etapas

| # | Etapa | Dónde vive |
|---|---|---|
| 1 | Recepción del target | Webhook/Form Trigger de n8n |
| 2 | Validación | Whitelist del Backend (`BACKEND_ALLOWED_LAB_HOSTS`) |
| 3 | Normalización del target | `Resolve Pipeline Context` (n8n) |
| 4 | Reconocimiento | Scanner: Nmap |
| 5 | Identificación de tecnologías | Scanner: WhatWeb |
| 6 | Selección inteligente de herramientas | `Select HTTP Port` (n8n), a partir de la respuesta de Nmap |
| 7 | Escaneo | Scanner: Nikto, Nuclei, ZAP |
| 8-10 | Consolidación, clasificación, persistencia | `POST /scans/{id}/tasks` en el Backend (normaliza y persiste en una transacción) |
| 11 | Generación de reporte | `POST /scans/{id}/reports` en el Backend → Reports Service |
| 12 | Notificación | Descarga + envío del reporte por mail (n8n) |

Detalle completo de qué nodo de n8n implementa cada etapa, por qué corren
secuenciales y no en paralelo, y cómo funciona la selección de
herramientas: [`n8n/README.md`](../n8n/README.md).

## Modelo de datos

Ver [`docs/database.md`](database.md) para el diagrama entidad-relación
completo y la descripción de cada tabla. Resumen: `targets` → `scans` →
`scan_tasks` (una invocación de una herramienta) → `findings` (forma
normalizada, común a cualquier herramienta) → `cve_references`;
`reports` guarda metadata de cada archivo generado.

## Seguridad

Ver [`docs/security.md`](security.md) para el modelo completo. Resumen:
autenticación por API key compartida (`BACKEND_API_KEY` para el
Backend, `INTERNAL_API_KEY` para Scanner/Reports) — decisión explícita
por alcance, no un sistema de usuarios. El documento detalla qué protege,
qué no, y el camino de mejora si el proyecto necesitara crecer más allá
de un laboratorio de un solo operador.

## Plan de desarrollo por módulos

El proyecto se construyó de forma incremental, manteniendo siempre un
`docker compose up -d` funcional al final de cada módulo.

| # | Módulo | Qué agrega |
|---|---|---|
| 0 | Scaffolding del repositorio | Estructura de carpetas, `docker-compose.yml` base, redes/volúmenes |
| 1 | Base de datos | Esquema PostgreSQL + migraciones Alembic (ver [`docs/database.md`](database.md)) |
| 2 | Laboratorio vulnerable | Juice Shop + DVWA en red segmentada (ver [`lab/README.md`](../lab/README.md)) |
| 3 | Backend API core | Registro y CRUD de targets, whitelist de hosts del laboratorio |
| 4 | Scanner Service | Adapters de Nmap/Nuclei/Nikto/WhatWeb/ZAP, patrón plugin |
| 5 | Normalización y clasificación | `scan_tasks`/`findings`, severidad por herramienta, CVEs |
| 6 | Orquestación n8n | Pipeline de 12 etapas, dos triggers (webhook + form) |
| 7 | Reports Service | Renderizado PDF/HTML/Markdown/JSON, envío por mail |
| — | Suite de tests automatizados | Tests unitarios de backend/scanner/reports |
| 8 | Frontend Dashboard | React + TS: targets, detalle, findings, reportes |
| 9 | Integración y endurecimiento | API keys, hardening de contenedores, tests e2e, CI |
| 10 | Documentación final y pulido | Este documento + manuales de instalación/uso |

## Cómo seguir extendiendo esto

- **Agregar una herramienta de escaneo nueva**: usar la skill
  `add-scanner-tool` (`.claude/skills/add-scanner-tool/`) — cubre los
  cuatro puntos de contacto (adapter del Scanner, normalizador del
  Backend, imagen Docker, nodos de n8n) para no dejar ninguno afuera.
- **Agregar una app vulnerable nueva al laboratorio**: ver "Adding
  another vulnerable app later" en [`lab/README.md`](../lab/README.md).
- **Agregar un formato de reporte nuevo**: agregar un renderer en
  `reports/app/renderers/` siguiendo el patrón de los cuatro existentes.
