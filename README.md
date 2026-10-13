# AI CV & Job Match Analyzer

A backend REST API that compares a candidate's CV against a job description using OpenAI, returning a structured match score, matching/missing skills, and a summary. Built with FastAPI, PostgreSQL, and JWT authentication.

## Features

- **AI-powered analysis** — submit CV text (or upload a PDF/DOCX directly) alongside a job description and get back a structured match score, matching skills, missing skills, and a summary, powered by OpenAI's structured outputs.
- **File upload support** — accepts real PDF and Word (.docx) CVs and extracts the text server-side.
- **JWT authentication** — signup/login with hashed passwords (bcrypt) and signed JWT access tokens.
- **Persistent history** — every analysis is saved to PostgreSQL, linked to the user who ran it.

## Tech stack

- **FastAPI** — web framework
- **PostgreSQL** (hosted on [Neon](https://neon.tech)) — database
- **SQLAlchemy** — ORM
- **OpenAI API** (`gpt-4o-mini`) — CV/job-description analysis with structured outputs
- **JWT** (`python-jose`) + **bcrypt** (`passlib`) — authentication
- **pypdf** / **python-docx** — CV file text extraction


## Setup

1. Clone the repo and create a virtual environment:
```bash
   git clone https://github.com/ChNafi222/cv-analyzer-api.git
   cd cv-analyzer-api
   python3 -m venv venv
   source venv/bin/activate
```

2. Install dependencies:
```bash
   pip install -r requirements.txt
```

3. Create a `.env` file in the project root:

OPENAI_API_KEY=your-openai-api-key
SECRET_KEY=your-generated-secret-key
DATABASE_URL=postgresql+psycopg2://user:password@host/dbname?sslmode=require


4. Run the server:
```bash
   uvicorn main:app --reload
```

5. Open `http://127.0.0.1:8000/docs` for the interactive API docs.

## API Endpoints

| Method | Endpoint        | Auth required | Description                                 |
|--------|-----------------|----------------|-----------------------------------------------|
| POST   | `/signup`       | No             | Create a new user account                    |
| POST   | `/login`        | No             | Log in, returns a JWT access token            |
| POST   | `/analyze`      | Yes            | Analyze CV text against a job description     |
| POST   | `/analyze-file` | Yes            | Analyze an uploaded PDF/DOCX CV against a job description |

Protected routes require an `Authorization: Bearer <token>` header, obtained from `/login`.

## Database schema

- **User** — `id`, `username`, `hashed_password`
- **Analysis** — `id`, `user_id` (FK → User), `score`, `matching_skills`, `missing_skills`, `summary`