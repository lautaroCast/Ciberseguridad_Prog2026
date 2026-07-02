"""CRUD endpoints for `targets`.

Whitelist/uniqueness enforcement is not duplicated here — it lives in
app/services/target_service.py; this module's only job is translating
between HTTP and that service layer.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.target import TargetCreate, TargetRead, TargetUpdate
from app.services import target_service
from app.services.target_service import (
    TargetNameConflictError,
    TargetNotAllowedError,
    TargetNotFoundError,
)

router = APIRouter(prefix="/targets", tags=["targets"])


@router.get("", response_model=list[TargetRead])
def list_targets(is_active: bool | None = None, db: Session = Depends(get_db)) -> list[TargetRead]:
    return target_service.list_targets(db, is_active=is_active)


@router.post("", response_model=TargetRead, status_code=status.HTTP_201_CREATED)
def create_target(payload: TargetCreate, db: Session = Depends(get_db)) -> TargetRead:
    try:
        return target_service.register_target(
            db, name=payload.name, host=payload.host, description=payload.description
        )
    except TargetNotAllowedError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Host '{exc}' is not part of the local lab whitelist. "
                "Only hosts defined in lab/ (Módulo 2) can be registered as targets."
            ),
        ) from exc
    except TargetNameConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A target named '{exc}' already exists.",
        ) from exc


@router.get("/{target_id}", response_model=TargetRead)
def get_target(target_id: uuid.UUID, db: Session = Depends(get_db)) -> TargetRead:
    try:
        return target_service.get_target_or_raise(db, target_id)
    except TargetNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Target '{exc}' not found."
        ) from exc


@router.patch("/{target_id}", response_model=TargetRead)
def update_target(
    target_id: uuid.UUID, payload: TargetUpdate, db: Session = Depends(get_db)
) -> TargetRead:
    try:
        return target_service.update_target(
            db, target_id, description=payload.description, is_active=payload.is_active
        )
    except TargetNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Target '{exc}' not found."
        ) from exc


@router.delete("/{target_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_target(target_id: uuid.UUID, db: Session = Depends(get_db)) -> None:
    try:
        target_service.delete_target(db, target_id)
    except TargetNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Target '{exc}' not found."
        ) from exc
