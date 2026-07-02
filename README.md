# VulnScan Platform

**Plataforma automatizada de detección de vulnerabilidades para laboratorios locales de ciberseguridad.**

> ⚠️ Este proyecto es exclusivamente para uso educativo y de investigación en **entornos de laboratorio locales**. No está diseñado ni autorizado para escanear sistemas públicos o de terceros. Ver [`docs/lab.md`](docs/lab.md) (Módulo 2) para el alcance legal completo.

---

## ¿Qué es esto?

VulnScan Platform orquesta el ciclo completo de un análisis de vulnerabilidades — reconocimiento, identificación de tecnologías, escaneo, normalización, clasificación por severidad, persistencia y generación de reportes — sobre aplicaciones vulnerables desplegadas localmente ([OWASP Juice Shop](https://owasp.org/www-project-juice-shop/), [DVWA](https://dvwa.co.uk/), y otras a futuro).

No es un conjunto de scripts sueltos: es una plataforma modular donde cada responsabilidad vive en su propio servicio, comunicándose por contratos HTTP bien definidos, orquestada como un pipeline reproducible en [n8n](https://n8n.io/).

```
Frontend (React/TS) → Backend API (FastAPI) → n8n (orquestador)
                              ↓                      ↓
                         PostgreSQL          Scanner Service
                              ↑          (Nmap · Nuclei · Nikto · WhatWeb · ZAP)
                              │                      │
                       Reports Service ◄─────────────┘
                    (PDF · HTML · Markdown · JSON)
```

Todo el sistema se levanta con un único comando:

```bash
cp .env.example .env
docker compose up -d
```

Sin instalaciones manuales posteriores, sin configuración adicional.

---

## Estado del proyecto

Este proyecto se desarrolla de forma incremental, módulo por módulo, manteniendo siempre un `docker compose up -d` funcional. Ver el plan de desarrollo completo en [`docs/architecture.md`](docs/architecture.md).

| Módulo | Descripción | Estado |
|---|---|---|
| 0 | Scaffolding del repositorio | ✅ Completo |
| 1 | Base de datos (PostgreSQL + Alembic) | ✅ Completo |
| 2 | Laboratorio vulnerable (Juice Shop + DVWA) | ✅ Completo |
| 3 | Backend API core (FastAPI) | ✅ Completo |
| 4 | Scanner Service (Nmap/Nuclei/Nikto/WhatWeb/ZAP) | ✅ Completo |
| 5 | Normalización y clasificación de hallazgos | ⏳ Pendiente |
| 6 | Orquestación n8n (pipeline de 12 etapas) | ⏳ Pendiente |
| 7 | Reports Service (PDF/HTML/MD/JSON) | ⏳ Pendiente |
| 8 | Frontend Dashboard (React + TS) | ⏳ Pendiente |
| 9 | Integración y endurecimiento | ⏳ Pendiente |
| 10 | Documentación final y pulido | ⏳ Pendiente |

---

## Estructura del repositorio

```
docs/         # Documentación: arquitectura, manuales, diagramas, alcance legal del laboratorio
docker/       # Recursos Docker compartidos (si no viven junto a cada servicio)
backend/      # API FastAPI: targets, scans, findings, normalización, clasificación
frontend/     # Dashboard React + TypeScript (Vite)
database/     # Migraciones Alembic, esquema SQL, diagrama ER
n8n/          # Workflows del pipeline, versionados como JSON
scanner/      # Microservicio de escaneo: adapters de Nmap, Nuclei, Nikto, WhatWeb, ZAP
reports/      # Microservicio de generación de reportes (Jinja2 + WeasyPrint)
lab/          # Definición del laboratorio de aplicaciones vulnerables
scripts/      # Utilidades: smoke tests, seed data, backups
assets/       # Diagramas fuente, capturas de pantalla
```

## Principios de arquitectura

- **Desacoplamiento por contrato HTTP** entre todos los servicios.
- **n8n como orquestador, no como ejecutor**: la lógica de negocio vive en código versionado, no en nodos de workflow.
- **Patrón plugin en el motor de escaneo**: agregar una herramienta nueva no requiere modificar las existentes.
- **Laboratorio en red segmentada** (`lab-network`, sin ruta desde frontend/n8n/backend/db): solo el Scanner Service la conecta con el resto de la plataforma. Qué se puede escanear lo decide la whitelist del Backend, no la topología de red — ver [`docs/lab.md`](docs/lab.md).
- **Extensible sin romper nada**: nuevas herramientas, nuevas apps vulnerables o nuevos formatos de reporte se agregan como módulos nuevos.

## Documentación

- [Arquitectura completa y plan de desarrollo](docs/architecture.md) *(Módulo 10)*
- [Manual de instalación](docs/installation.md) *(Módulo 10)*
- [Manual de uso](docs/usage.md) *(Módulo 10)*
- [Modelo de datos y diagrama ER](docs/database.md)
- [Alcance legal del laboratorio](docs/lab.md)

## Licencia

[MIT](LICENSE)
