# Resume-to-Job Matching Web Application

An intelligent web application that analyzes your resume using AI, scrapes jobs from multiple sources, and ranks them by compatibility.

## Features

- **AI-Powered Resume Analysis**: Uses Google Gemini/OpenAI to extract skills, experience, and preferences
- **Multi-Source Job Scraping**: Aggregates jobs from Indeed, RemoteOK, Remotive, LinkedIn, Wellfound, and Workday
- **Intelligent Matching**: Ranks jobs using a weighted algorithm (skills, experience, title, location, job type)
- **Real-time Progress**: Background scraping with progress tracking
- **RESTful API**: Clean FastAPI backend with comprehensive endpoints

## Tech Stack

### Backend
- **Framework**: FastAPI
- **Database**: SQLite (SQLAlchemy ORM)
- **Resume Parsing**: pdfplumber, PyPDF2, python-docx
- **LLM Integration**: Google Gemini API, OpenAI API
- **Web Scraping**: BeautifulSoup, Selenium, Playwright
- **Matching**: scikit-learn (TF-IDF), RapidFuzz

### Frontend
- **Framework**: React 18
- **HTTP Client**: Axios
- **File Upload**: react-dropzone
- **Styling**: Tailwind CSS

## Project Structure

```
Job_Scrapper/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI app
│   │   ├── config.py               # Configuration
│   │   ├── database.py             # Database setup
│   │   ├── models.py               # SQLAlchemy models
│   │   ├── schemas.py              # Pydantic schemas
│   │   ├── api/
│   │   │   └── routes.py           # API endpoints
│   │   ├── services/
│   │   │   ├── resume_parser.py    # PDF/DOCX parsing
│   │   │   ├── llm_analyzer.py     # AI analysis
│   │   │   ├── job_matcher.py      # Matching algorithm
│   │   │   └── scraper_orchestrator.py
│   │   ├── scrapers/
│   │   │   ├── base_scraper.py
│   │   │   ├── indeed_scraper.py
│   │   │   ├── linkedin_scraper.py
│   │   │   ├── remoteok_scraper.py
│   │   │   ├── remotive_scraper.py
│   │   │   ├── wellfound_scraper.py
│   │   │   ├── workday_scraper.py
│   │   │   └── utils/
│   │   └── utils/
│   ├── data/                       # SQLite database
│   ├── uploads/                    # Temporary resume storage
│   ├── requirements.txt
│   ├── setup.sh                    # Setup script
│   └── .env                        # Environment variables
│
├── frontend/                       # React app (to be implemented)
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.8+
- Node.js 16+ (for frontend)
- Chrome/Chromium (for Playwright/Selenium)

### Backend Setup

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Run setup script:**
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

   Or manually:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   playwright install chromium
   ```

3. **Configure environment variables:**
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and add your API keys:
   ```
   GEMINI_API_KEY=your_gemini_api_key_here
   OPENAI_API_KEY=your_openai_api_key_here
   ```

4. **Run the server:**
   ```bash
   uvicorn app.main:app --reload
   ```

   Server will start at: `http://localhost:8000`

### API Documentation

Once the server is running, visit:
- **Interactive API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Resume Upload & Analysis

**POST** `/api/upload-resume`
- Upload resume (PDF/DOCX)
- Returns session ID and extracted profile

**Example:**
```bash
curl -X POST "http://localhost:8000/api/upload-resume" \
  -F "file=@resume.pdf"
```

### Job Scraping

**POST** `/api/scrape-jobs`
- Start background scraping task
- Returns task ID for status polling

**Request Body:**
```json
{
  "session_id": "uuid",
  "query": "software engineer",
  "location": "Remote",
  "max_jobs_per_source": 50,
  "sources": ["indeed", "remoteok", "remotive"]
}
```

**GET** `/api/scraping-status/{task_id}`
- Check scraping progress

### Job Matching

**POST** `/api/matched-jobs`
- Get ranked job matches for resume

**Request Body:**
```json
{
  "session_id": "uuid",
  "min_score": 30,
  "limit": 50
}
```

**Response:**
```json
{
  "session_id": "uuid",
  "total_matches": 120,
  "matches": [
    {
      "job": {
        "title": "Senior Python Developer",
        "company": "Tech Corp",
        "location": "Remote",
        "apply_url": "https://..."
      },
      "match_score": 87.5,
      "match_breakdown": {
        "skills_score": 35.2,
        "experience_score": 22.0,
        "title_score": 18.5,
        "location_score": 10.0,
        "job_type_score": 5.0
      }
    }
  ]
}
```

## Job Sources

### Implemented Scrapers

| Source | Method | Success Rate | Notes |
|--------|--------|--------------|-------|
| **RemoteOK** | API | ✅ High | Public API, reliable |
| **Remotive** | API | ✅ High | Public API, reliable |
| **Indeed** | BeautifulSoup | ⚠️ Medium | May encounter anti-bot measures |
| **LinkedIn** | Playwright | ⚠️ Low | Strong anti-bot, may require auth |
| **Wellfound** | BeautifulSoup | ⚠️ Medium | May require auth |
| **Workday** | Selenium | ⚠️ Medium | Requires company-specific URLs |

### Anti-Bot Strategies

- **User agent rotation**
- **Random delays (2-8 seconds)**
- **Stealth browser configurations**
- **Rate limiting per source**
- **Graceful failure handling**

## Matching Algorithm

Jobs are scored using a weighted algorithm:

| Component | Weight | Method |
|-----------|--------|--------|
| **Skills Match** | 40% | TF-IDF + keyword overlap |
| **Experience Match** | 25% | Years comparison |
| **Title Match** | 20% | Fuzzy string matching |
| **Location Match** | 10% | Geographic matching |
| **Job Type Match** | 5% | Remote/hybrid/onsite |

**Total Score**: 0-100

## LLM Integration

### Resume Analysis Flow

1. **Parse** resume (PDF/DOCX → text)
2. **Analyze** with Gemini/OpenAI
3. **Extract** structured data:
   - Skills
   - Experience years
   - Job titles/roles
   - Education
   - Location preference
   - Job type preference

### Fallback Strategy

1. **Try Gemini** (primary, free tier)
2. **Try OpenAI** (fallback)
3. **Use regex** (emergency fallback)

## Environment Variables

```bash
# LLM API Keys
GEMINI_API_KEY=your_key
OPENAI_API_KEY=your_key

# Database
DATABASE_URL=sqlite:///./data/job_scrapper.db

# Security
SECRET_KEY=random_secret_key

# CORS
CORS_ORIGINS=http://localhost:3000

# Limits
MAX_UPLOAD_SIZE=10485760  # 10MB
SCRAPING_TIMEOUT=300       # 5 minutes
MAX_JOBS_PER_SOURCE=50
```

## Development

### Running Tests
```bash
cd backend
pytest tests/ -v
```

### Database Management

**Initialize database:**
```python
from app.database import init_db
init_db()
```

**Drop all tables:**
```python
from app.database import drop_db
drop_db()  # USE WITH CAUTION
```

## Troubleshooting

### Common Issues

1. **Playwright browser not found**
   ```bash
   playwright install chromium
   ```

2. **Selenium ChromeDriver issues**
   ```bash
   # Install Chrome/Chromium
   # ChromeDriver auto-managed by Selenium 4.6+
   ```

3. **LinkedIn scraping fails**
   - Expected - LinkedIn has strong anti-bot measures
   - Consider implementing cookie-based authentication

4. **LLM API errors**
   - Check API keys in `.env`
   - Verify API quota/limits
   - Check network connectivity

## Performance

- **Resume parsing**: < 2 seconds
- **LLM analysis**: 3-8 seconds
- **Job scraping**: 1-3 minutes (parallel)
- **Matching**: < 1 second for 200 jobs

## Limitations

1. **LinkedIn**: Strong anti-bot measures, may require authentication
2. **Rate Limits**: Respect source rate limits to avoid IP bans
3. **Job Freshness**: Cache jobs for 24 hours to reduce scraping load
4. **LLM Costs**: Use free tiers (Gemini preferred)

## Future Enhancements

- [ ] User authentication & saved profiles
- [ ] Email notifications for new matches
- [ ] Application tracking
- [ ] More job sources (Glassdoor, Monster)
- [ ] Machine learning-based matching
- [ ] Salary range analysis
- [ ] Company culture fit analysis

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:
- Create an issue on GitHub
- Check API documentation at `/docs`
- Review code comments and docstrings

## Acknowledgments

- Google Gemini for free LLM access
- RemoteOK & Remotive for public APIs
- FastAPI for excellent web framework
- All open-source contributors

---

**Built with ❤️ using FastAPI, React, and AI**
