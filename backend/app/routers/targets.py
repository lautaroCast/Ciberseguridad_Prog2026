"""CRUD endpoints for `targets`.

Whitelist/uniqueness enforcement is not duplicated here — it lives in
app/services/target_service.py. Domain exceptions raised by that layer
(TargetNotFoundError, TargetNotAllowedError, TargetNameConflictError) are
translated to HTTP responses by the exception handlers registered once in
app/main.py, so routes below just call the service and let errors
propagate — no per-route try/except.
"""

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.target import TargetCreate, TargetRead, TargetUpdate
from app.services import target_service

router = APIRouter(prefix="/targets", tags=["targets"])


@router.get("", response_model=list[TargetRead])
def list_targets(is_active: bool | None = None, db: Session = Depends(get_db)) -> list[TargetRead]:
    return target_service.list_targets(db, is_active=is_active)


@router.post("", response_model=TargetRead, status_code=status.HTTP_201_CREATED)
def create_target(payload: TargetCreate, db: Session = Depends(get_db)) -> TargetRead:
    return target_service.register_target(
        db, name=payload.name, host=payload.host, description=payload.description
    )


@router.get("/{target_id}", response_model=TargetRead)
def get_target(target_id: uuid.UUID, db: Session = Depends(get_db)) -> TargetRead:
    return target_service.get_target_or_raise(db, target_id)


@router.patch("/{target_id}", response_model=TargetRead)
def update_target(
    target_id: uuid.UUID, payload: TargetUpdate, db: Session = Depends(get_db)
) -> TargetRead:
    # exclude_unset distinguishes "field omitted" from "field explicitly set
    # to null" — payload.description=None only reaches the service/repo if
    # the client actually sent `"description": null`, which is what lets a
    # PATCH clear a previously-set description instead of being a no-op.
    updates = payload.model_dump(exclude_unset=True)
    return target_service.update_target(db, target_id, updates)


@router.delete("/{target_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_target(target_id: uuid.UUID, db: Session = Depends(get_db)) -> None:
    target_service.delete_target(db, target_id)
