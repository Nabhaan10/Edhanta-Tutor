from pydantic import BaseModel
from typing import Optional


class QuestionRequest(BaseModel):
    question: str
    session_id: str
    board: str = "CBSE"


class AnswerResponse(BaseModel):
    answer: str
    sources: list[str]


class ExtractedMetadata(BaseModel):
    """Vision-extracted metadata returned alongside the image answer."""

    subject: Optional[str] = None
    topic: Optional[str] = None
    marks: Optional[str] = None
    question_type: Optional[str] = None
    question: Optional[str] = None


class ImageAnswerResponse(BaseModel):
    answer: str
    sources: list[str]
    extracted: ExtractedMetadata
    route: str = "theory"   # "theory" | "numerical" — which solver path was taken