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
import models
from database import engine, get_db
from sqlalchemy.orm import Session

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

models.Base.metadata.create_all(bind=engine)


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Temporary hardcoded user — replaced by a real database later
# fake_users_db = {
#     "nafi": {
#         "username": "nafi",
#         "hashed_password": pwd_context.hash("password123"),
#     }
# }

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

from fastapi.security import OAuth2PasswordBearer
from jose import JWTError

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    return user

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
def analyze_file(job_description: str = Form(...), cv_file: UploadFile = File(...), current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
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

    result = response.choices[0].message.parsed

    new_analysis = models.Analysis(
        user_id=current_user.id,
        score=result.score,
        matching_skills=",".join(result.matching_skills),
        missing_skills=",".join(result.missing_skills),
        summary=result.summary,
    )
    db.add(new_analysis)
    db.commit()

    return result

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not pwd_context.verify(form_data.password, user.hashed_password):
      raise HTTPException(status_code=401, detail="Incorrect username or password")

    token = create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}



class SignupRequest(BaseModel):
    username : str
    password : str


@app.post("/signup")
def signup(request: SignupRequest , db :Session = Depends(get_db)):
    existing_user = db.query(models.User).filter(models.User.username == request.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already taken")

    hashed_password = pwd_context.hash(request.password)
    new_user = models.User(username=request.username, hashed_password=hashed_password)

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": f"User '{new_user.username}' created successfully"}



@app.post("/analyze", response_model=AnalysisResult)
def analyze(request: AnalyzeRequest, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    prompt = f"""Compare this CV to this job description.
CV: {request.cv_text}
Job Description: {request.job_description}

Return a match score out of 100, a list of matching skills, and a list of missing skills."""

    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format=AnalysisResult,
    )

    result = response.choices[0].message.parsed

    new_analysis = models.Analysis(
        user_id=current_user.id,
        score=result.score,
        matching_skills=",".join(result.matching_skills),
        missing_skills=",".join(result.missing_skills),
        summary=result.summary,
    )
    db.add(new_analysis)
    db.commit()

    return result