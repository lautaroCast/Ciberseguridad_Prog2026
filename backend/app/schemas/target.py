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
    # Unlike `description` (nullable DB-side, so `null` is a legitimate
    # "clear it" value), `Target.is_active` is NOT NULL — typing this as
    # `bool | None` let a PATCH with `{"is_active": null}` reach
    # target_repository.update_target's blind setattr() and crash with an
    # unhandled IntegrityError (500) instead of a clean 422. `exclude_unset`
    # (see the router) is what makes the field still optional to omit
    # entirely; the default below is never actually used, since an omitted
    # field never appears in `model_dump(exclude_unset=True)`.
    is_active: bool = True


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
