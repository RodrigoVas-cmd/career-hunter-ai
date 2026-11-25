from datetime import date
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class UserProfileUpdate(BaseModel):
    headline: Optional[str] = Field(default=None, max_length=255)
    summary: Optional[str] = None
    contact_email: Optional[str] = Field(default=None, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=40)
    city: Optional[str] = Field(default=None, max_length=120)
    state: Optional[str] = Field(default=None, max_length=80)
    country: Optional[str] = Field(default="Brasil", max_length=80)
    seniority_level: Optional[str] = Field(default=None, max_length=64)
    linkedin_url: Optional[str] = Field(default=None, max_length=500)
    portfolio_url: Optional[str] = Field(default=None, max_length=500)
    education_json: Optional[List[Dict[str, Any]]] = None
    certifications_json: Optional[List[Dict[str, Any]]] = None
    languages_json: Optional[List[Dict[str, Any]]] = None
    projects_json: Optional[List[Dict[str, Any]]] = None
    sectors_json: Optional[List[str]] = None


class UserProfileResponse(BaseModel):
    id: str
    user_id: str
    headline: Optional[str] = None
    summary: Optional[str] = None
    contact_email: Optional[str] = None
    phone: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: str
    seniority_level: Optional[str] = None
    linkedin_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    education_json: List[Dict[str, Any]] = []
    certifications_json: List[Dict[str, Any]] = []
    languages_json: List[Dict[str, Any]] = []
    projects_json: List[Dict[str, Any]] = []
    sectors_json: List[str] = []

    model_config = {"from_attributes": True}


class ExperienceCreate(BaseModel):
    company_name: str = Field(min_length=1, max_length=200)
    role_title: str = Field(min_length=1, max_length=200)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_current: bool = False
    raw_period_text: Optional[str] = None
    responsibilities: Optional[str] = None
    proven_results: Optional[str] = None
    leadership_experience: bool = False
    sector: Optional[str] = None
    origin: str = "manual"
    evidence_excerpt: Optional[str] = None
    validation_status: str = "verified"
    ambiguity_note: Optional[str] = None


class ExperienceUpdate(BaseModel):
    company_name: Optional[str] = Field(default=None, max_length=200)
    role_title: Optional[str] = Field(default=None, max_length=200)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_current: Optional[bool] = None
    raw_period_text: Optional[str] = None
    responsibilities: Optional[str] = None
    proven_results: Optional[str] = None
    leadership_experience: Optional[bool] = None
    sector: Optional[str] = None
    validation_status: Optional[str] = None
    ambiguity_note: Optional[str] = None


class ExperienceResponse(BaseModel):
    id: str
    user_id: str
    company_name: str
    role_title: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_current: bool
    raw_period_text: Optional[str] = None
    responsibilities: Optional[str] = None
    proven_results: Optional[str] = None
    leadership_experience: bool
    sector: Optional[str] = None
    origin: str
    evidence_source_id: Optional[str] = None
    evidence_excerpt: Optional[str] = None
    validation_status: str
    ambiguity_note: Optional[str] = None

    model_config = {"from_attributes": True}


class SkillCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    category: str = "technical"
    proficiency: Optional[str] = None
    years_experience: Optional[int] = Field(default=None, ge=0, le=60)
    origin: str = "manual"
    evidence_excerpt: Optional[str] = None
    validation_status: str = "verified"
    ambiguity_note: Optional[str] = None


class SkillUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=120)
    category: Optional[str] = None
    proficiency: Optional[str] = None
    years_experience: Optional[int] = Field(default=None, ge=0, le=60)
    validation_status: Optional[str] = None
    ambiguity_note: Optional[str] = None


class SkillResponse(BaseModel):
    id: str
    user_id: str
    name: str
    category: str
    proficiency: Optional[str] = None
    years_experience: Optional[int] = None
    origin: str
    evidence_source_id: Optional[str] = None
    evidence_excerpt: Optional[str] = None
    validation_status: str
    ambiguity_note: Optional[str] = None

    model_config = {"from_attributes": True}


class CareerPreferenceUpdate(BaseModel):
    current_city: Optional[str] = None
    current_state: Optional[str] = None
    desired_locations: Optional[List[str]] = None
    work_modalities: Optional[List[str]] = None
    max_commute_minutes: Optional[int] = Field(default=None, ge=0, le=300)
    max_commute_km: Optional[int] = Field(default=None, ge=0, le=1000)
    relocation_available: Optional[bool] = None
    travel_available: Optional[bool] = None
    min_salary_brl: Optional[int] = Field(default=None, ge=0)
    desired_salary_brl: Optional[int] = Field(default=None, ge=0)
    salary_negotiable: Optional[bool] = None
    contract_types: Optional[List[str]] = None
    excluded_companies: Optional[List[str]] = None
    preferred_sectors: Optional[List[str]] = None
    professional_restrictions: Optional[str] = None
    application_languages: Optional[List[str]] = None
    search_frequency_hours: Optional[int] = Field(default=None, ge=1, le=168)
    monitoring_windows: Optional[List[str]] = None
    max_recommended_jobs: Optional[int] = Field(default=None, ge=1, le=100)
    min_match_score: Optional[int] = Field(default=None, ge=0, le=100)
    eliminatory_criteria: Optional[List[str]] = None
    notification_preferences: Optional[Dict[str, Any]] = None
    prioritize_favorite_companies: Optional[bool] = None
    openai_api_key: Optional[str] = None


class CareerPreferenceResponse(BaseModel):
    id: str
    user_id: str
    current_city: Optional[str] = None
    current_state: Optional[str] = None
    desired_locations: List[str] = []
    work_modalities: List[str] = []
    max_commute_minutes: Optional[int] = None
    max_commute_km: Optional[int] = None
    relocation_available: Optional[bool] = None
    travel_available: Optional[bool] = None
    min_salary_brl: Optional[int] = None
    desired_salary_brl: Optional[int] = None
    salary_negotiable: bool = False
    contract_types: List[str] = []
    excluded_companies: List[str] = []
    preferred_sectors: List[str] = []
    professional_restrictions: Optional[str] = None
    application_languages: List[str] = []
    search_frequency_hours: int
    monitoring_windows: List[str] = []
    max_recommended_jobs: int
    min_match_score: int
    eliminatory_criteria: List[str] = []
    notification_preferences: Dict[str, Any] = {}
    prioritize_favorite_companies: bool
    application_mode: str
    has_openai_key: bool = False

    model_config = {"from_attributes": True}
