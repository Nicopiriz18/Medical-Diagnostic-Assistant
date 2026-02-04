from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.models.clinical import AnalyzeRequest, AnalyzeResponse
from app.services.analyzer import analyze_case

app = FastAPI(title="Medical Diagnostic Assistant", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # en prod: restringir
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/v1/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest):
    try:
        assessment = await analyze_case(req.case_text)
        return {"assessment": assessment}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
