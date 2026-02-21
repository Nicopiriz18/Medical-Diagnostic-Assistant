from pydantic import BaseModel, Field
from typing import List, Literal, Optional

class DifferentialDx(BaseModel):
    name: str
    likelihood: int = Field(ge=0, le=100, description="0-100 (heurístico, no validado clínicamente)")
    reasoning: str
    urgency: Literal["immediate", "urgent", "routine"]
    
    # Información detallada expandida
    general_causes: List[str] = Field(default_factory=list, description="Etiología general de la condición")
    patient_specific_factors: List[str] = Field(default_factory=list, description="Factores específicos del paciente que pueden contribuir")
    risk_factors: List[str] = Field(default_factory=list, description="Factores de riesgo identificados en este paciente")
    supporting_findings: List[str] = Field(default_factory=list, description="Hallazgos clínicos que apoyan este diagnóstico")
    contradicting_findings: List[str] = Field(default_factory=list, description="Hallazgos que contradicen o hacen menos probable este diagnóstico")
    prognosis: str = Field(default="", description="Pronóstico esperado de la condición")
    complications: List[str] = Field(default_factory=list, description="Posibles complicaciones si no se trata adecuadamente")
    recommended_tests: List[str] = Field(default_factory=list, description="Exámenes y pruebas recomendadas para confirmar el diagnóstico")
    treatment_summary: str = Field(default="", description="Resumen de las opciones de tratamiento disponibles")

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
