import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ADMIN_BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(ADMIN_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(ADMIN_BACKEND_DIR))

TEST_DB_PATH = ADMIN_BACKEND_DIR / "test_admin_control_center.db"
os.environ["ADMIN_DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"
os.environ["ADMIN_ENVIRONMENT"] = "development"
os.environ["ADMIN_JWT_SECRET_KEY"] = "test-admin-jwt-secret-key-at-least-32-chars"

from app.core.database import SessionLocal, engine, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models.base import AdminBase, SharedBase  # noqa: E402
from app.models.shared import SharedPlan, SharedPlanFeature, SharedSubscription, SharedUser  # noqa: E402


@pytest.fixture()
def db_session():
    AdminBase.metadata.drop_all(bind=engine)
    SharedBase.metadata.drop_all(bind=engine)
    SharedBase.metadata.create_all(bind=engine)
    AdminBase.metadata.create_all(bind=engine)

    db = SessionLocal()
    now = datetime.now(timezone.utc)
    p_free = SharedPlan(id="plan-free", code="free", name="Free", price_brl_cents=0, is_active=True)
    p_pro = SharedPlan(id="plan-pro", code="pro", name="Pro", price_brl_cents=4990, is_active=True)
    p_prem = SharedPlan(id="plan-prem", code="premium", name="Premium", price_brl_cents=8990, is_active=True)
    db.add_all([p_free, p_pro, p_prem])
    db.add_all([
        SharedPlanFeature(id=str(uuid.uuid4()), plan_id="plan-free", feature_key="monthly_analyses", limit_value=5, description="5 análises/mês"),
        SharedPlanFeature(id=str(uuid.uuid4()), plan_id="plan-pro", feature_key="monthly_analyses", limit_value=150, description="150 análises/mês"),
        SharedPlanFeature(id=str(uuid.uuid4()), plan_id="plan-prem", feature_key="monthly_analyses", limit_value=500, description="500 análises/mês"),
    ])
    u_pro = SharedUser(
        id="user-pro-1",
        email="pro_existente@exemplo.com",
        hashed_password="hash",
        full_name="Usuário Pro Existente",
        role="user",
        is_active=True,
        onboarding_step=5,
        onboarding_completed=True,
        created_at=now,
        updated_at=now,
    )
    u_free = SharedUser(
        id="user-free-1",
        email="free_novo@exemplo.com",
        hashed_password="hash",
        full_name="Usuário Free Novo",
        role="user",
        is_active=True,
        onboarding_step=1,
        onboarding_completed=False,
        created_at=now,
        updated_at=now,
    )
    db.add_all([u_pro, u_free])
    db.add(
        SharedSubscription(
            id="sub-pro-1",
            user_id="user-pro-1",
            plan_id="plan-pro",
            status="active",
            created_at=now,
            updated_at=now,
        )
    )
    db.commit()

    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
