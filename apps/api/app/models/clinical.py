from pydantic import BaseModel, Field
from typing import List, Literal, Optional

class DifferentialDx(BaseModel):
    name: str
    likelihood: int = Field(ge=0, le=100, description="0-100 (heurístico, no validado clínicamente)")
    reasoning: str
    urgency: Literal["immediate", "urgent", "routine"]

class RedFlag(BaseModel):
    severity: Literal["critical", "warning", "info"]
    message: str
    why_it_matters: str

class ActionPlanItem(BaseModel):
    priority: Literal["immediate", "urgent", "routine"]
    action: str
    rationale: str

class SOAP(BaseModel):
    subjective: str
    objective: str
    assessment: str
    plan: str

class ClinicalAssessment(BaseModel):
    differentials: List[DifferentialDx]
    red_flags: List[RedFlag]
    missing_questions: List[str]
    action_plan: List[ActionPlanItem]
    soap: SOAP
    patient_summary: str
    limitations: str

class AnalyzeRequest(BaseModel):
    case_text: str = Field(min_length=10, max_length=6000)

class AnalyzeResponse(BaseModel):
    assessment: ClinicalAssessment
