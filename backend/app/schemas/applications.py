from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

VALID_OPERATIONAL_STATUSES = {
    "descoberta",
    "qualificada",
    "favorita",
    "em_preparacao",
    "aguardando_revisao",
    "aguardando_aprovacao",
    "envio_em_andamento",
    "enviada_confirmada",
    "pendente_confirmacao",
    "falha_envio",
    "resposta_recebida",
    "teste_solicitado",
    "entrevista_agendada",
    "entrevista_realizada",
    "proxima_etapa",
    "proposta_recebida",
    "contratado",
    "reprovado",
    "desistencia",
    "encerrada",
    "descartada",
}


class ApplicationCreate(BaseModel):
    job_posting_id: Optional[str] = None
    company_name: Optional[str] = Field(default=None, max_length=200)
    role_title: Optional[str] = Field(default=None, max_length=255)
    source_url: Optional[str] = Field(default=None, max_length=800)
    is_manual: bool = False


class ApplicationUpdate(BaseModel):
    operational_status: Optional[str] = None
    process_stage: Optional[str] = None
    note: Optional[str] = None


class ResumeVersionResponse(BaseModel):
    id: str
    user_id: str
    base_resume_id: str
    job_posting_id: Optional[str] = None
    version_label: str
    content_json: Dict[str, Any] = {}
    changes_summary_json: List[str] = []
    approved_by_user: bool
    docx_path: Optional[str] = None
    pdf_path: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class QuestionCreate(BaseModel):
    question_text: str = Field(min_length=3)
    field_type: str = Field(default="texto_longo", max_length=40)
    options: List[str] = []
    max_chars: Optional[int] = Field(default=None, ge=10, le=10000)


class AnswerUpdate(BaseModel):
    approved_answer: str = Field(min_length=1)


class ApplicationAnswerResponse(BaseModel):
    id: str
    application_id: str
    question_text: str
    question_category: str
    draft_answer: Optional[str] = None
    approved_answer: Optional[str] = None
    evidence_refs_json: List[str] = []
    requires_human_input: bool

    model_config = {"from_attributes": True}


class ApplicationApprovalResponse(BaseModel):
    id: str
    application_id: str
    payload_hash: str
    is_valid: bool
    approved_at: datetime

    model_config = {"from_attributes": True}


class ApplicationEventResponse(BaseModel):
    id: str
    application_id: str
    event_type: str
    description: Optional[str] = None
    metadata_json: Dict[str, Any] = {}
    occurred_at: datetime

    model_config = {"from_attributes": True}


class InterviewCreate(BaseModel):
    stage_name: str = Field(min_length=2, max_length=120)
    scheduled_at: Optional[datetime] = None
    notes: Optional[str] = None


class InterviewUpdate(BaseModel):
    stage_name: Optional[str] = Field(default=None, max_length=120)
    scheduled_at: Optional[datetime] = None
    status: Optional[str] = Field(default=None, pattern="^(scheduled|completed|cancelled)$")
    notes: Optional[str] = None


class InterviewResponse(BaseModel):
    id: str
    application_id: str
    stage_name: str
    scheduled_at: Optional[datetime] = None
    status: str
    notes: Optional[str] = None

    model_config = {"from_attributes": True}


class SubmissionConfirmRequest(BaseModel):
    confirmed: bool = True
    ambiguous: bool = False
    confirmation_note: Optional[str] = None


class ApplicationResponse(BaseModel):
    id: str
    user_id: str
    job_posting_id: Optional[str] = None
    resume_version_id: Optional[str] = None
    company_name: str
    role_title: str
    operational_status: str
    process_stage: Optional[str] = None
    source_url: Optional[str] = None
    is_manual: bool
    submitted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    has_valid_approval: bool = False

    model_config = {"from_attributes": True}


class ApplicationDetailResponse(ApplicationResponse):
    resume_version: Optional[ResumeVersionResponse] = None
    answers: List[ApplicationAnswerResponse] = []
    approvals: List[ApplicationApprovalResponse] = []
    events: List[ApplicationEventResponse] = []
    interviews: List[InterviewResponse] = []
