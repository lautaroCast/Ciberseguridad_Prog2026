"""Módulo 5 — normalization: tool-specific `parsed` JSON -> DB-shaped rows.

Every normalizer in this package takes the Scanner Service's already-parsed
output for one tool and returns a `NormalizedData` (see `types.py`) of plain
dataclasses — no DB access here. `app/services/scan_task_service.py` is the
only place that turns those dataclasses into `Service` / `Technology` /
`Finding` / `CveReference` ORM rows.
"""
