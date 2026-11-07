from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, desc, select

from app.db import get_session
from app.models import Task, TaskCreate, TaskRead, TaskUpdate

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


def _get_task_or_404(session: Session, task_id: int) -> Task:
    task = session.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("", response_model=TaskRead, status_code=201)
def create_task(payload: TaskCreate, session: Session = Depends(get_session)):
    task = Task(**payload.model_dump())
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


@router.get("", response_model=list[TaskRead])
def list_tasks(session: Session = Depends(get_session)):
    return session.exec(
        select(Task).order_by(desc(Task.created_at), desc(Task.id))
    ).all()


@router.get("/{task_id}", response_model=TaskRead)
def retrieve_task(task_id: int, session: Session = Depends(get_session)):
    return _get_task_or_404(session, task_id)


@router.patch("/{task_id}", response_model=TaskRead)
def update_task(
    task_id: int,
    payload: TaskUpdate,
    session: Session = Depends(get_session),
):
    task = _get_task_or_404(session, task_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    task.updated_at = datetime.now(timezone.utc)
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


@router.delete("/{task_id}", status_code=204)
def delete_task(task_id: int, session: Session = Depends(get_session)):
    task = _get_task_or_404(session, task_id)
    session.delete(task)
    session.commit()
    return None
