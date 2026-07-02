"""Pydantic schemas for the `targets` resource.

`is_lab_target` is deliberately absent from `TargetCreate`: whether a
target is a lab target is derived server-side from the whitelist check
(see app/services/target_service.py), never taken from client input —
otherwise a client could self-declare a non-lab host as "trusted".
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TargetCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    host: str = Field(min_length=1, max_length=255)
    description: str | None = None


class TargetUpdate(BaseModel):
    description: str | None = None
    is_active: bool | None = None


class TargetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    host: str
    description: str | None
    is_lab_target: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
