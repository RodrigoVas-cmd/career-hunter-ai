from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.applications import Notification
from app.models.user import CareerPreference, User

router = APIRouter(prefix="/notifications", tags=["Notificações"])

OPENAI_GUIDE_URL = "https://help.openai.com/en/articles/4936850-where-do-i-find-my-openai-api-key"
OPENAI_KEYS_URL = "https://platform.openai.com/api-keys"


class NotificationItemResponse(BaseModel):
    id: str
    title: str
    body: str
    category: str
    is_read: bool
    is_system_alert: bool = False
    action_url: str | None = None
    external_guide_url: str | None = None


def create_user_notification(
    db: Session,
    *,
    user_id: str,
    title: str,
    body: str,
    category: str = "info",
) -> Notification:
    notif = Notification(
        user_id=user_id,
        title=title,
        body=body,
        category=category,
        is_read=False,
    )
    db.add(notif)
    return notif


@router.get("", response_model=List[NotificationItemResponse])
def list_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    prefs = (
        db.query(CareerPreference)
        .filter(CareerPreference.user_id == current_user.id)
        .first()
    )
    has_key = bool(prefs and prefs.openai_api_key)

    items: List[NotificationItemResponse] = []
    if not has_key:
        items.append(
            NotificationItemResponse(
                id="system-openai-missing",
                title="Conecte sua chave API do ChatGPT (OpenAI) — Altamente Recomendado",
                body=(
                    "Para gerar currículos ATS estratégicos em PDF com adequação profunda à vaga "
                    "e respostas personalizadas de recrutamento, conecte sua chave da OpenAI em Configurações. "
                    f"Veja como criar sua chave no guia oficial da OpenAI ({OPENAI_GUIDE_URL}) "
                    f"ou acesse {OPENAI_KEYS_URL}."
                ),
                category="warning",
                is_read=False,
                is_system_alert=True,
                action_url="/app/configuracoes",
                external_guide_url=OPENAI_GUIDE_URL,
            )
        )

    rows = (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
        .limit(50)
        .all()
    )
    for r in rows:
        items.append(
            NotificationItemResponse(
                id=r.id,
                title=r.title,
                body=r.body,
                category=r.category,
                is_read=r.is_read,
                is_system_alert=False,
            )
        )
    return items


@router.patch("/{notification_id}/read", status_code=status.HTTP_204_NO_CONTENT)
def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if notification_id.startswith("system-"):
        return
    notif = (
        db.query(Notification)
        .filter(Notification.id == notification_id, Notification.user_id == current_user.id)
        .first()
    )
    if not notif:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notificação não encontrada.")
    notif.is_read = True
    db.commit()
