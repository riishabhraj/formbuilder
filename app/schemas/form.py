from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class FormField(BaseModel):
    field_id: str
    type: str
    label: str
    required: bool

class FormBase(BaseModel):
    title: str
    description: str
    fields: List[FormField]

class FormCreate(FormBase):
    pass

class Form(FormBase):
    id: int
    creator_id: int

    class Config:
        from_attributes = True

class FormResponse(BaseModel):
    status: str
    data: Form 