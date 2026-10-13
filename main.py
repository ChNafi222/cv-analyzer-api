from fastapi import FastAPI,File, UploadFile,Form,Depends, HTTPException
from pydantic import BaseModel
import os

from dotenv import load_dotenv
from openai import OpenAI
from datetime import datetime,timedelta
from jose import jwt
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm

from pypdf import PdfReader
import docx
import io

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Temporary hardcoded user — replaced by a real database later
fake_users_db = {
    "nafi": {
        "username": "nafi",
        "hashed_password": pwd_context.hash("password123"),
    }
}

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

from fastapi.security import OAuth2PasswordBearer
from jose import JWTError

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None or username not in fake_users_db:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        return username
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")


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
def analyze(request:AnalyzeRequest, current_user: str = Depends(get_current_user)):
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

def extract_text(file: UploadFile) -> str:
    contents = file.file.read()

    if file.filename.endswith(".pdf"):
        reader = PdfReader(io.BytesIO(contents))
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    elif file.filename.endswith(".docx"):
        document = docx.Document(io.BytesIO(contents))
        return "\n".join(paragraph.text for paragraph in document.paragraphs)

    else:
        raise ValueError("Unsupported file type. Please upload a PDF or DOCX.")


@app.post("/analyze-file", response_model=AnalysisResult)
def analyze_file(job_description: str = Form(...), cv_file: UploadFile = File(...), current_user: str = Depends(get_current_user) ):
    cv_text = extract_text(cv_file)

    prompt = f"""Compare this CV to this job description.
CV: {cv_text}
Job Description: {job_description}

Return a match score out of 100, a list of matching skills, and a list of missing skills."""

    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format=AnalysisResult,
    )

    return response.choices[0].message.parsed

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = fake_users_db.get(form_data.username)
    if not user or not pwd_context.verify(form_data.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    token = create_access_token({"sub": user["username"]})
    return {"access_token": token, "token_type": "bearer"}

