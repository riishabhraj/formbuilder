from pydantic import BaseModel
from typing import List, Any, Dict, Optional
from datetime import datetime

class SubmissionField(BaseModel):
    field_id: str
    value: Any

class SubmissionCreate(BaseModel):
    responses: List[SubmissionField]

class SubmissionBase(BaseModel):
    form_id: int
    data: Dict[str, Any]

class Submission(SubmissionBase):
    id: int
    submitted_at: datetime

    class Config:
        from_attributes = True

class SubmissionResponse(BaseModel):
    status: str = "success"
    message: str
    submission_id: int
    data: Optional[Dict[str, Any]] = None
    submitted_at: Optional[datetime] = None 