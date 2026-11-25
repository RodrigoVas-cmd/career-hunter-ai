from typing import List, Optional

from pydantic import BaseModel, Field


class TargetRoleCreate(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    desired_seniority: Optional[str] = None
    area: Optional[str] = None
    priority: str = Field(default="media", pattern="^(alta|media|baixa)$")
    synonyms: List[str] = []
    desired_sectors: List[str] = []
    min_salary_brl: Optional[int] = Field(default=None, ge=0)
    desired_salary_brl: Optional[int] = Field(default=None, ge=0)
    locations: List[str] = []
    modalities: List[str] = []
    mandatory_criteria: List[str] = []
    status: str = Field(default="ativo", pattern="^(ativo|pausado)$")


class TargetRoleUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=2, max_length=200)
    desired_seniority: Optional[str] = None
    area: Optional[str] = None
    priority: Optional[str] = Field(default=None, pattern="^(alta|media|baixa)$")
    synonyms: Optional[List[str]] = None
    desired_sectors: Optional[List[str]] = None
    min_salary_brl: Optional[int] = Field(default=None, ge=0)
    desired_salary_brl: Optional[int] = Field(default=None, ge=0)
    locations: Optional[List[str]] = None
    modalities: Optional[List[str]] = None
    mandatory_criteria: Optional[List[str]] = None
    status: Optional[str] = Field(default=None, pattern="^(ativo|pausado)$")
    user_approved: Optional[bool] = None


class TargetRoleResponse(BaseModel):
    id: str
    user_id: str
    title: str
    desired_seniority: Optional[str] = None
    area: Optional[str] = None
    priority: str
    synonyms: List[str] = []
    desired_sectors: List[str] = []
    min_salary_brl: Optional[int] = None
    desired_salary_brl: Optional[int] = None
    locations: List[str] = []
    modalities: List[str] = []
    mandatory_criteria: List[str] = []
    status: str
    is_ai_suggested: bool
    ai_justification: Optional[str] = None
    user_approved: bool

    model_config = {"from_attributes": True}


class TargetRoleSuggestion(BaseModel):
    title: str
    justification: str
    based_on_evidence: str
    synonyms: List[str] = []


class FavoriteCompanyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    official_website: Optional[str] = None
    careers_page_url: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: str = "Brasil"
    sector: Optional[str] = None
    priority: str = Field(default="media", pattern="^(alta|media|baixa)$")
    roles_of_interest: List[str] = []
    departments: List[str] = []
    notes: Optional[str] = None


class FavoriteCompanyUpdate(BaseModel):
    priority: Optional[str] = Field(default=None, pattern="^(alta|media|baixa)$")
    roles_of_interest: Optional[List[str]] = None
    departments: Optional[List[str]] = None
    notes: Optional[str] = None
    monitoring_status: Optional[str] = None
    careers_page_url: Optional[str] = None


class CompanyInfo(BaseModel):
    id: str
    name: str
    official_website: Optional[str] = None
    careers_page_url: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: str
    sector: Optional[str] = None

    model_config = {"from_attributes": True}


class FavoriteCompanyResponse(BaseModel):
    id: str
    user_id: str
    company_id: str
    priority: str
    roles_of_interest: List[str] = []
    departments: List[str] = []
    notes: Optional[str] = None
    monitoring_status: str
    company: CompanyInfo

    model_config = {"from_attributes": True}


class CSVImportResult(BaseModel):
    imported_count: int
    skipped_count: int
    errors: List[str] = []
