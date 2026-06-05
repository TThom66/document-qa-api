from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import List

# Creates a document for the API. If the document has more than 50,000 characters, reject it.
class DocumentCreate(BaseModel):
    title: str
    content: str

    @field_validator("content")
    @classmethod
    def content_max_length(cls, v):
        if len(v) > 50000:
            raise ValueError("Document content cannot exceed 50,000 characters")
        return v

class DocumentResponse(BaseModel):
    id: int
    title: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True

class QuestionRequest(BaseModel):
    question: str

class QuestionResponse(BaseModel):
    document_id: int
    question: str
    answer: str

# Creates a user with a provided username and password. If the password is less than 8 characters, reject it.
class UserCreate(BaseModel):
    username: str
    password: str

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v

class UserResponse(BaseModel):
    id: int
    username: str
    created_at: datetime

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

# Creates a question template, which is an object that stores multiple questions to ask at once.
# If the template given has more than 10 questions, reject it.
class TemplateCreate(BaseModel):
    title: str
    questions: List[str]

    @field_validator("questions")
    @classmethod
    def questions_max_count(cls, v):
        if len(v) > 10:
            raise ValueError("Templates cannot exceed 10 questions")
        return v

class TemplateResponse(BaseModel):
    id: int
    title: str
    questions: List[str]
    created_at: datetime

    class Config:
        from_attributes = True

class TemplateApplyRequest(BaseModel):
    document_id: int

class TemplateApplyResponse(BaseModel):
    template_title: str
    document_title: str
    results: List[dict]