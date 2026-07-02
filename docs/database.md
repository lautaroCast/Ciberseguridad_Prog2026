# Modelo de datos

Esquema de PostgreSQL que persiste todo el ciclo de vida de un análisis:
target registrado → ejecución del pipeline → tareas por herramienta →
servicios/tecnologías detectados → hallazgos normalizados → CVEs asociados →
reportes generados. Definido en [`database/models/`](../database/models) y
versionado con Alembic en [`database/migrations/`](../database/migrations).

## Diagrama entidad-relación

```mermaid
erDiagram
    TARGETS ||--o{ SCANS : "es escaneado en"
    SCANS ||--o{ SCAN_TASKS : "ejecuta"
    SCANS ||--o{ SERVICES : "descubre"
    SCANS ||--o{ TECHNOLOGIES : "identifica"
    SCANS ||--o{ FINDINGS : "produce"
    SCANS ||--o{ REPORTS : "genera"
    SCAN_TASKS ||--o{ FINDINGS : "reporta"
    SERVICES ||--o{ FINDINGS : "asociado a (opcional)"
    FINDINGS ||--o{ CVE_REFERENCES : "referencia"

    TARGETS {
        uuid id PK
        string name UK
        string host
        text description
        bool is_lab_target
        bool is_active
        timestamptz created_at
        timestamptz updated_at
    }
    SCANS {
        uuid id PK
        uuid target_id FK
        enum status
        string pipeline_run_id "n8n execution id"
        string triggered_by
        timestamptz started_at
        timestamptz finished_at
        text error_message
        timestamptz created_at
    }
    SCAN_TASKS {
        uuid id PK
        uuid scan_id FK
        string tool_name "nmap, nuclei, nikto..."
        enum status
        text command
        text raw_output
        string raw_output_path
        timestamptz started_at
        timestamptz finished_at
        text error_message
        timestamptz created_at
    }
    SERVICES {
        uuid id PK
        uuid scan_id FK
        string host
        int port
        string protocol
        string service_name
        string product
        string version
        text banner
        timestamptz created_at
    }
    TECHNOLOGIES {
        uuid id PK
        uuid scan_id FK
        string name
        string version
        string category
        string detected_by
        string confidence
        timestamptz created_at
    }
    FINDINGS {
        uuid id PK
        uuid scan_id FK
        uuid scan_task_id FK
        uuid service_id FK "nullable"
        string title
        text description
        string finding_type
        text evidence
        string confidence
        numeric cvss_score
        string cvss_vector
        enum severity
        timestamptz created_at
    }
    CVE_REFERENCES {
        uuid id PK
        uuid finding_id FK
        string cve_id
        numeric cvss_score
        string cvss_vector
        text description
        string source_url
        timestamptz created_at
    }
    REPORTS {
        uuid id PK
        uuid scan_id FK
        enum format "pdf, html, markdown, json"
        string file_path
        timestamptz generated_at
        string generated_by
    }
    USERS {
        uuid id PK
        string email UK
        string hashed_password
        string full_name
        enum role
        bool is_active
        timestamptz created_at
    }
```

`USERS` no tiene FK hacia el resto del esquema todavía: es un placeholder
(Módulo 1) para una futura capa de autenticación multiusuario y no lo
consume ningún servicio en esta etapa del proyecto.

## Descripción de cada tabla

| Tabla | Responsabilidad |
|---|---|
| `targets` | Sistemas registrados para análisis. `is_lab_target` es el flag que el Backend (Módulo 3) usa para aplicar la whitelist: solo se pueden escanear targets del laboratorio local. |
| `scans` | Una ejecución del pipeline de 12 etapas sobre un target. `pipeline_run_id` correlaciona la fila con la ejecución de n8n que la origina. |
| `scan_tasks` | Una invocación de una herramienta concreta (Nmap, Nuclei, Nikto, WhatWeb, ZAP...) dentro de un scan. `tool_name` es texto libre, no enum, para poder sumar herramientas nuevas sin migración. |
| `services` | Puertos/servicios de red descubiertos durante el reconocimiento (Nmap). |
| `technologies` | Stack tecnológico fingerprinteado (WhatWeb u otra herramienta). Alimenta la etapa de "selección inteligente de herramientas" del pipeline. |
| `findings` | Hallazgo normalizado: forma común a la que se traduce la salida de cualquier herramienta antes de persistir. `finding_type` también es texto libre por el mismo motivo que `tool_name`. |
| `cve_references` | CVEs asociados a un finding (relación 0..N, un finding puede tener varios CVEs). |
| `reports` | Metadatos de un reporte generado (PDF/HTML/Markdown/JSON); el archivo en sí vive en el volumen `reports-data`. |
| `users` | Placeholder para autenticación multiusuario futura. |

## Decisiones de diseño

- **UUID como clave primaria** (`gen_random_uuid()`, nativo desde PostgreSQL 13+, sin necesidad de extensión) en vez de enteros autoincrementales, para no filtrar el volumen de filas a través de la API.
- **Enums nativos de PostgreSQL** solo para vocabularios cerrados y estables: `scan_status`, `scan_task_status`, `severity_level`, `report_format`, `user_role`. Todo lo que necesita poder ampliarse sin tocar el esquema (`tool_name`, `finding_type`) es un `string` indexado.
- **`cve_references` como tabla propia** en vez de una columna `cve_id` en `findings`, porque una sola herramienta (Nuclei, ZAP) puede reportar varios CVEs para un mismo hallazgo.
- **Borrado en cascada** desde `targets` hacia abajo: eliminar un target elimina su historial completo de scans/findings/reportes: es el comportamiento esperado en un laboratorio donde los targets pueden recrearse.

## Migraciones

Ver [`database/README.md`](../database/README.md) para el flujo de trabajo completo (cómo aplicar, generar y validar migraciones con Alembic).
