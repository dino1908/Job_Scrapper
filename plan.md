# Resume-to-Job Matching Web Application - Implementation Plan

## Context

Building a web application where users upload their resume, the system analyzes it using free LLMs (Gemini, Codex), scrapes 50-200 recent jobs from multiple sources via free automation, matches them intelligently, and displays ranked results with application links.

**Why:** Automate job searching by matching resume profiles against multiple job boards, saving users time and providing personalized job recommendations.

**Requirements:**
- Backend: Python (FastAPI)
- Frontend: React
- Resume Analysis: Mistral LLM (API key provided)
- Job Sources: LinkedIn, Workday (user-provided URLs), Indeed, RemoteOK, Wellfound, Remotive
- Scraping: Free, automation-based (no paid APIs)
- Target: 50-200 jobs per scraping session
- **Approach**: Build MVP first with core functionality, then iterate and add details

## Architecture Overview

**Monorepo Structure:**
```
User → React Frontend (port 3000)
         ↓ REST API
      FastAPI Backend (port 8000)
         ↓
    ├─→ Resume Parser → LLM Analyzer (Mistral)
    ├─→ Job Scrapers (parallel) → Multiple sources
    ├─→ Job Matcher → Scoring algorithm
    └─→ SQLite Database → Jobs cache, sessions
```

## MVP Output Format

Each job result will contain:
- **Company Name**: The hiring company
- **Role Name**: Job title/position
- **Location**: Job location (remote/city/country)
- **Date of Posting**: When the job was posted (for sorting by recency)
- **Link to Apply**: Direct URL to the job application page

## Directory Structure

```
Job_Scrapper/
├── backend/
│   ├── app/
│   │   ├── main.py                     # FastAPI entry point
│   │   ├── config.py                   # Configuration
│   │   ├── database.py                 # SQLAlchemy setup
│   │   ├── models.py                   # DB models (Job, UserSession, JobMatch)
│   │   ├── schemas.py                  # Pydantic schemas
│   │   ├── api/
│   │   │   └── routes.py               # API endpoints
│   │   ├── services/
│   │   │   ├── resume_parser.py        # PDF/DOCX parsing
│   │   │   ├── llm_analyzer.py         # Gemini/Codex integration
│   │   │   ├── job_matcher.py          # Matching algorithm
│   │   │   └── scraper_orchestrator.py # Parallel scraping
│   │   ├── scrapers/
│   │   │   ├── base_scraper.py         # Abstract base class
│   │   │   ├── indeed_scraper.py       # BeautifulSoup
│   │   │   ├── linkedin_scraper.py     # Playwright stealth
│   │   │   ├── workday_scraper.py      # Selenium
│   │   │   ├── remoteok_scraper.py     # API-based
│   │   │   ├── wellfound_scraper.py    # BeautifulSoup
│   │   │   ├── remotive_scraper.py     # API-based
│   │   │   └── utils/
│   │   │       ├── stealth_config.py   # Anti-detection
│   │   │       └── rate_limiter.py     # Rate limiting
│   │   └── utils/
│   │       └── file_handler.py         # Upload handling
│   ├── data/
│   │   └── job_scrapper.db             # SQLite database
│   ├── uploads/                         # Temporary resume storage
│   ├── requirements.txt
│   └── .env
│
├── frontend/
│   ├── src/
│   │   ├── App.js                      # Main component
│   │   ├── components/
│   │   │   ├── ResumeUpload.js         # Drag-drop upload
│   │   │   ├── JobList.js              # Results display
│   │   │   ├── JobCard.js              # Individual job
│   │   │   └── MatchScore.js           # Score visualization
│   │   └── services/
│   │       └── api.js                  # API client
│   ├── package.json
│   └── .env
│
└── README.md
```

## Critical Files to Implement

### 1. `/backend/app/main.py` - FastAPI Application
**Purpose:** API entry point, route definitions, CORS setup

**Key Routes:**
- `POST /api/upload-resume` - Upload & analyze resume
- `POST /api/scrape-jobs` - Trigger background scraping
- `GET /api/scraping-status/{job_id}` - Poll scraping progress
- `GET /api/matched-jobs/{session_id}` - Get ranked results

### 2. `/backend/app/services/resume_parser.py` - Resume Parsing
**Purpose:** Extract text from PDF/DOCX files

**Dependencies:** `pdfplumber` (primary), `PyPDF2` (fallback), `python-docx`

**Key Functions:**
- `parse_file(file_path, file_type) -> dict` - Main parsing entry
- `extract_text_from_pdf(file_path) -> str`
- `extract_text_from_docx(file_path) -> str`

### 3. `/backend/app/services/llm_analyzer.py` - LLM Integration
**Purpose:** Extract structured data from resume text using Mistral

**Dependencies:** `mistralai`

**Structured Extraction (MVP - Keep it Simple):**
```python
class ResumeProfile:
    skills: List[str]              # Key technical skills
    experience_years: float        # Total years of experience
    roles: List[str]               # Previous job titles
    job_type_preference: str       # remote/hybrid/onsite (if mentioned)
    location: str                  # Location preference (if mentioned)
```

**LLM Strategy:**
- Use Mistral API (user provides API key)
- Model: `mistral-small` or `mistral-medium` (cost-effective)
- Fallback: Simple regex-based extraction if API fails

**Mistral API Usage:**
```python
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage

client = MistralClient(api_key=os.getenv("MISTRAL_API_KEY"))

def analyze_resume(resume_text: str) -> ResumeProfile:
    prompt = f"""Analyze this resume and extract the following information:
    1. Key technical skills (list)
    2. Total years of professional experience (number)
    3. Job titles/roles held (list)
    4. Job type preference if mentioned (remote/hybrid/onsite)
    5. Location preference if mentioned

    Resume text:
    {resume_text}

    Return ONLY a valid JSON object with keys: skills, experience_years, roles, job_type_preference, location
    """

    messages = [ChatMessage(role="user", content=prompt)]

    response = client.chat(
        model="mistral-small-latest",  # or "mistral-medium-latest"
        messages=messages,
        temperature=0.1,  # Low temperature for consistent extraction
    )

    # Parse JSON response
    result = json.loads(response.choices[0].message.content)
    return ResumeProfile(**result)
```

### 4. `/backend/app/scrapers/base_scraper.py` - Scraper Base Class
**Purpose:** Common interface and utilities for all scrapers

```python
from abc import ABC, abstractmethod

class BaseScraper(ABC):
    @abstractmethod
    def scrape_jobs(self, query: str, location: str, limit: int) -> List[Job]:
        pass

    def normalize_job_data(self, raw_data: dict) -> Job:
        # Standardize job data format
        pass

    def retry_with_backoff(self, func, max_retries=3):
        # Exponential backoff for retries
        pass
```

### 5. `/backend/app/services/job_matcher.py` - Matching Algorithm
**Purpose:** Calculate match scores between resume and jobs

**Weighted Scoring Algorithm:**
```python
def calculate_match_score(resume_profile, job) -> float:
    scores = {
        'skills_match': 40%,      # TF-IDF/cosine similarity
        'experience_match': 25%,   # Years comparison
        'title_match': 20%,        # Fuzzy string matching
        'location_match': 10%,     # Geographic/remote match
        'job_type_match': 5%       # Full-time/contract/etc
    }
    return weighted_total  # 0-100
```

## MVP Scope (Build This First)

**Core Features for MVP:**
1. ✅ Resume upload (PDF only for MVP)
2. ✅ Mistral-based resume analysis → extract skills, experience, roles
3. ✅ Scrape 50-100 jobs from 2-3 easy sources (RemoteOK, Indeed)
4. ✅ Simple matching based on skills overlap
5. ✅ Display results: Company, Role, Location, Date, Apply Link
6. ✅ Basic React UI with upload + results list

**Post-MVP Enhancements:**
- Add more scrapers (LinkedIn, Workday)
- Advanced matching algorithm
- Filters and sorting
- Save search results
- Email notifications

**MVP Timeline:** 7-10 days (vs 15-17 for full version)

## Implementation Steps (Phased)

### Phase 1: Backend Foundation (Days 1-3)

1. **Setup:**
   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate
   pip install fastapi uvicorn sqlalchemy pdfplumber python-docx mistralai
   ```

2. **Create core files:**
   - `app/main.py` - FastAPI app with CORS
   - `app/database.py` - SQLAlchemy setup
   - `app/models.py` - Job, UserSession, JobMatch models
   - `app/config.py` - Environment variables

3. **Implement resume parser:**
   - PDF parsing (pdfplumber + PyPDF2 fallback)
   - DOCX parsing
   - File validation (max 10MB, .pdf/.docx only)

4. **Integrate Mistral API:**
   - Set up API key in `.env` (MISTRAL_API_KEY)
   - Implement structured prompt for resume analysis
   - Parse JSON response
   - Add error handling + regex fallback

### Phase 2: Job Scraping (Days 4-6) - **MVP Focus**

5. **MVP scrapers (build these first):**
   - **RemoteOK:** `https://remoteok.com/api` (has API - very easy!)
     - Simple GET request
     - Returns JSON with all job data
     - Parse and normalize to our schema

   - **Indeed:** `https://www.indeed.com/jobs?q={query}&l={location}`
     - BeautifulSoup parsing
     - User agent rotation
     - Extract: company, role, location, date, link
     - 2-5 sec random delays between requests

6. **Scraper orchestration (parallel scraping):**
   ```python
   async def scrape_all_sources(query, location, limit):
       # MVP: Start with 2 sources
       tasks = [
           remoteok_scraper.scrape_async(query, limit=50),
           indeed_scraper.scrape_async(query, location, limit=50),
       ]
       results = await asyncio.gather(*tasks, return_exceptions=True)
       # Combine and return jobs
       all_jobs = []
       for result in results:
           if not isinstance(result, Exception) and result:
               all_jobs.extend(result)
       return all_jobs
   ```

7. **Post-MVP scrapers (add later):**
   - **LinkedIn:** Playwright with stealth (complex, may get blocked)
   - **Workday:** Selenium (needs user-provided URLs)
   - **Remotive:** API-based (easy to add)
   - **Wellfound:** BeautifulSoup (medium difficulty)

### Phase 3: Matching & API (Days 7-8) - **MVP Simplified**

8. **Job matcher implementation (simple version for MVP):**
   - **Skills matching:** Count how many resume skills appear in job description
   - **Experience matching:** Simple yes/no based on years
   - **Basic scoring:** Skills match percentage (0-100)
   - Sort by: Match score DESC, then Date posted DESC

   ```python
   def calculate_match_score(resume_skills, job_description):
       # Simple keyword matching for MVP
       matches = sum(1 for skill in resume_skills if skill.lower() in job_description.lower())
       score = (matches / len(resume_skills)) * 100 if resume_skills else 0
       return round(score, 2)
   ```

9. **API endpoints:**
    - `POST /api/upload-resume` → Upload, parse, analyze with Mistral, create session
    - `POST /api/scrape-jobs` → Trigger background scraping
    - `GET /api/scraping-status/{job_id}` → Check progress
    - `GET /api/matched-jobs/{session_id}` → Get ranked results (sorted by score, then date)

### Phase 4: Frontend (Days 9-10) - **MVP Minimal UI**

10. **React setup:**
    ```bash
    npx create-react-app frontend
    cd frontend
    npm install axios react-dropzone
    ```

11. **Core components (keep it simple for MVP):**
    - `ResumeUpload.js` - Simple file input (drag-drop optional)
    - `LoadingSpinner.js` - Show while scraping
    - `JobTable.js` - Display results in a table with columns:
      - Company Name
      - Role Name
      - Location
      - Date Posted
      - Apply Link (clickable)
      - Match Score

12. **User flow (MVP - single page app):**
    ```
    1. Upload Resume
    2. Show "Analyzing resume..."
    3. Show "Scraping jobs..." with spinner
    4. Display results table (sortable by date/score)
    ```

    **No complex features for MVP:**
    - ❌ No filters (add post-MVP)
    - ❌ No fancy animations
    - ❌ No user accounts
    - ✅ Just upload → results

### Phase 5: Testing & Polish (Days 11-12) - **MVP Testing**

13. **Basic testing:**
    - Test resume parser with sample PDF
    - Test Mistral API integration
    - Test each scraper (RemoteOK, Indeed)
    - End-to-end flow: upload → scrape → display

14. **Error handling (minimal for MVP):**
    - Show error if resume upload fails
    - Show error if no jobs found
    - If one scraper fails, continue with other
    - Basic logging to console

15. **MVP ready checklist:**
    - ✅ Can upload PDF resume
    - ✅ Mistral extracts skills correctly
    - ✅ RemoteOK scraper works
    - ✅ Indeed scraper works
    - ✅ Jobs display in table
    - ✅ Match scores are calculated
    - ✅ Sortable by date/score
    - ✅ Apply links are clickable

## Key Dependencies

### Backend (`requirements.txt`)
```
# Core Framework
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-multipart==0.0.6

# Database
sqlalchemy==2.0.25

# Resume Parsing
pdfplumber==0.10.3
PyPDF2==3.0.1
python-docx==1.1.0

# LLM Integration
mistralai==0.1.8

# Web Scraping
selenium==4.16.0
playwright==1.40.0
beautifulsoup4==4.12.3
lxml==5.1.0
requests==2.31.0
selenium-stealth==1.0.6
fake-useragent==1.4.0

# Matching Algorithm
scikit-learn==1.4.0

# Utilities
python-dotenv==1.0.0
tenacity==8.2.3
```

### Frontend (`package.json`)
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "axios": "^1.6.5",
    "react-dropzone": "^14.2.3",
    "tailwindcss": "^3.4.1",
    "react-icons": "^5.0.1"
  }
}
```

## Anti-Bot Scraping Strategies

### LinkedIn (Hardest)
- Playwright with stealth mode
- Hide webdriver flag
- Realistic viewport (1920x1080)
- Random delays (3-7 seconds)
- Session persistence (save cookies)
- **Accept failures** - LinkedIn actively blocks bots

### Indeed (Moderate)
- Rotate user agents
- Random delays (2-5 seconds)
- Limit to 10 pages per query
- Use BeautifulSoup (simpler than browser automation)

### Workday (Moderate)
- Selenium with stealth plugin
- Wait for React content to load
- Handle dynamic pagination
- Each company has different setup

### RemoteOK/Remotive (Easy)
- Have unofficial APIs - use those!
- No anti-bot measures needed

## Database Schema (MVP - Simplified)

```python
class Job(Base):
    """Core job fields matching MVP output format"""
    id = Integer (primary key)
    company_name = String(255)      # Company Name
    role_name = String(255)         # Role/Job Title
    location = String(255)          # Location
    date_posted = DateTime          # Date of Posting (for sorting)
    apply_link = String(500)        # Link to Apply
    source = String(50)             # indeed/linkedin/etc
    scraped_at = DateTime           # When we scraped it

class UserSession(Base):
    """Store resume analysis results"""
    id = String(36) (UUID)          # Session ID
    resume_text = Text              # Original resume text
    resume_profile = JSON           # ResumeProfile from Mistral
    created_at = DateTime

class JobMatch(Base):
    """Track which jobs match which session (with scores)"""
    id = Integer
    session_id = String (FK)
    job_id = Integer (FK)
    match_score = Float             # 0-100 matching score
```

## Environment Variables

**Backend (`.env`):**
```
MISTRAL_API_KEY=your_mistral_api_key_here
DATABASE_URL=sqlite:///./data/job_scrapper.db
SECRET_KEY=random_secret_key
CORS_ORIGINS=http://localhost:3000
MAX_UPLOAD_SIZE=10485760
SCRAPING_TIMEOUT=300
```

**Frontend (`.env`):**
```
REACT_APP_API_URL=http://localhost:8000
```

## Running the Application

### Development

**Backend:**
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm start  # Runs on port 3000
```

### Production Deployment Options

1. **Railway** (Recommended for MVP)
   - Deploy backend and frontend separately
   - Built-in PostgreSQL available
   - Free tier with GitHub integration

2. **DigitalOcean App Platform**
   - Full-stack deployment
   - $5-12/month

3. **VPS (DigitalOcean Droplet)**
   - Full control
   - Nginx reverse proxy
   - $6/month

## Verification & Testing

**End-to-end test:**
1. Upload sample resume (PDF)
2. Verify resume analysis extracts skills correctly
3. Trigger job scraping (start with 50 jobs)
4. Verify jobs are scraped from multiple sources
5. Check match scores are calculated correctly
6. Verify job list displays with links
7. Test filter/sort functionality

**Scraper testing:**
```bash
cd backend
python scripts/test_scrapers.py
```

**Unit tests:**
```bash
cd backend
pytest tests/ -v
```

## Critical Success Factors (MVP Focus)

1. **Resume parsing works** - At least for common PDF formats
2. **Mistral extracts skills** - Doesn't need to be perfect, just good enough
3. **2 scrapers work reliably** - RemoteOK (easy) + Indeed (moderate)
4. **Basic matching works** - Simple keyword matching is fine for MVP
5. **Simple, functional UI** - No need to be fancy, just works
6. **Fast iteration** - Get MVP working, then improve based on testing

**Post-MVP Improvements:**
- Better PDF parsing for complex formats
- More sophisticated matching algorithm
- Additional scrapers
- Better UI/UX
- Performance optimizations

## Known Challenges & Solutions

| Challenge | Solution |
|-----------|----------|
| LinkedIn blocks scraping | Use Playwright stealth, limit requests, accept failures |
| Inconsistent resume formats | Multiple parsing libraries (pdfplumber, PyPDF2), Mistral-based extraction |
| Long scraping times (2-5 min) | Background tasks, progress polling, show partial results |
| LLM API reliability | Use Mistral API with retry logic, fallback to regex extraction |
| Workday variations | User provides URLs, generic scraper with config options |

## Future Enhancements (Post-MVP)

- User accounts & saved resumes
- Email alerts for new matching jobs
- Application tracking
- More job sources (Glassdoor, Monster)
- Machine learning-based matching
- Salary range matching
- Company culture fit analysis

---

## MVP vs Full Version Timeline

**MVP (Recommended - Build This First):** 10-12 days
- Days 1-3: Backend setup, resume parser, Mistral integration
- Days 4-6: 2 scrapers (RemoteOK + Indeed)
- Days 7-8: Simple matching, API endpoints
- Days 9-10: Basic React UI
- Days 11-12: Testing & polish

**Full Version (Post-MVP):** +5-7 days
- Add LinkedIn scraper (complex)
- Add Workday scraper
- Advanced matching (TF-IDF, fuzzy matching)
- Filters, sorting, pagination
- Better UI/UX

**First Milestone (Days 1-5):** Resume upload + Mistral analysis + RemoteOK scraper working
