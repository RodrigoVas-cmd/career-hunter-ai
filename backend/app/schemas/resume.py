from datetime import datetime
from typing import Any, Dict, List

from pydantic import BaseModel


class ResumeResponse(BaseModel):
    id: str
    user_id: str
    original_filename: str
    file_format: str
    file_size_bytes: int
    extracted_data_json: Dict[str, Any] = {}
    ambiguities_json: List[Dict[str, Any]] = []
    parse_status: str
    is_primary: bool
    created_at: datetime

    model_config = {"from_attributes": True}
