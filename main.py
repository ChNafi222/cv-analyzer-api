from fastapi import FastAPI
from pydantic import BaseModel
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = FastAPI()

@app.get("/")
def read_root():
    return{"message":"Hello from FastAPI"}


class AnalyzeRequest(BaseModel):
    cv_text:str
    job_description:str

class AnalysisResult(BaseModel):
    score: int
    matching_skills: list[str]
    missing_skills: list[str]
    summary: str

@app.post("/analyze",response_model=AnalysisResult)
def analyze(request:AnalyzeRequest):
    prompt = f"""Compare this CV to this job description.
CV: {request.cv_text}
Job Description: {request.job_description}

Return a match score out of 100, a list of matching skills, and a list of missing skills."""

    response = client.beta.chat.completions.parse(
        model = "gpt-4o-mini",
        messages=[{"role":"user","content":prompt}],
        response_format = AnalysisResult,
    )

    return response.choices[0].message.parsed
