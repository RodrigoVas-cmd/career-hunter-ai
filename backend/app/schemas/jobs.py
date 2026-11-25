from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ConnectorDiscoverRequest(BaseModel):
    source_kind: str = Field(pattern="^(greenhouse|lever|jsonld)$")
    target: str = Field(min_length=2, max_length=500)  # board token, company slug, or URL
    company_name: Optional[str] = Field(default=None, max_length=200)


class ManualJobCreate(BaseModel):
    company_name: str = Field(min_length=1, max_length=200)
    title: str = Field(min_length=2, max_length=255)
    description: str = Field(min_length=10)
    original_url: str = Field(min_length=5, max_length=800)
    source_name: str = Field(default="Manual", max_length=120)
    location: Optional[str] = None
    modality: Optional[str] = Field(default=None, pattern="^(remoto|hibrido|presencial)$")
    seniority: Optional[str] = None
    salary_range_text: Optional[str] = None
    mandatory_requirements: List[str] = []
    desirable_requirements: List[str] = []
    eliminatory_requirements: List[str] = []


class JobRequirementResponse(BaseModel):
    id: str
    requirement_type: str
    text: str

    model_config = {"from_attributes": True}


class JobPostingResponse(BaseModel):
    id: str
    company_name: str
    title: str
    description: str
    original_url: str
    location: Optional[str] = None
    modality: Optional[str] = None
    seniority: Optional[str] = None
    salary_range_text: Optional[str] = None
    availability_status: str
    published_at: Optional[datetime] = None
    discovered_at: datetime
    is_favorite_company: bool = False
    requirements: List[JobRequirementResponse] = []

    model_config = {"from_attributes": True}


class DiscoverResultResponse(BaseModel):
    source_kind: str
    fetched_count: int
    created_count: int
    updated_count: int
    jobs: List[JobPostingResponse] = []


class CompanyWatchCompanyResult(BaseModel):
    favorite_company_id: str
    company_name: str
    careers_page_url: Optional[str] = None
    status: str
    jobs_found: int = 0
    error_message: Optional[str] = None


class CompanyWatchRunResponse(BaseModel):
    monitored_count: int
    error_count: int
    total_jobs_found: int
    results: List[CompanyWatchCompanyResult] = []


class MatchingWeights(BaseModel):
    functional_experience: float = Field(default=25.0, ge=0, le=100)
    mandatory_skills: float = Field(default=25.0, ge=0, le=100)
    seniority_scope: float = Field(default=15.0, ge=0, le=100)
    desirable_skills: float = Field(default=10.0, ge=0, le=100)
    sector_transferable: float = Field(default=10.0, ge=0, le=100)
    location_modality: float = Field(default=10.0, ge=0, le=100)
    career_objectives: float = Field(default=5.0, ge=0, le=100)


class JobMatchResponse(BaseModel):
    id: str
    job_posting_id: str
    company_name: str
    job_title: str
    original_url: str
    location: Optional[str] = None
    modality: Optional[str] = None
    seniority: Optional[str] = None
    is_favorite_company: bool
    total_score: float
    priority_score: float
    classification: str
    is_eligible: bool
    confidence_level: float
    dimension_scores: Dict[str, float]
    explanation: Dict[str, Any]
