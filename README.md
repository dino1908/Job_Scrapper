# Job Scrapper

Job Scrapper is a React + FastAPI application for searching LinkedIn public job listings by role and location, tracking scraping progress live, and exporting the resulting jobs to Excel.

The current app is centered on a single flow:

1. Enter one or more role titles.
2. Optionally enter one or more locations.
3. Start a background scrape.
4. Poll progress and show live results in the UI.
5. Export the final job list as `.xlsx`.

## What The Code Currently Does

- Scrapes LinkedIn public guest job listings only.
- Accepts comma-separated role titles and comma-separated locations.
- Expands the search across every role/location combination.
- Starts from the most recent 1 day of postings and backfills 1 day at a time until the target count is reached or 180 days is exhausted.
- Stores scraped jobs in SQLite.
- Replaces the previous stored job set whenever a new scrape starts.
- Uses deterministic relevance filters by default.
- Uses Mistral, when configured, to further screen jobs for strict role/location relevance.
- Shows live progress in the frontend while scraping runs in a FastAPI background task.
- Lets the user download the visible jobs as an Excel file.

## What Is Not Currently Wired Into The App

Some files in the repository are from earlier or broader plans, but they are not part of the current API/UI flow:

- Resume upload is not exposed by the active FastAPI router.
- Resume analysis is not exposed by the active FastAPI router.
- Match scoring is not exposed by the active FastAPI router.
- Multi-source scraping is not active in the orchestrator; only LinkedIn is enabled.

## Stack

### Backend

- FastAPI
- SQLAlchemy
- SQLite
- Requests + BeautifulSoup for the active LinkedIn scraper
- Optional Mistral API integration for relevance screening

### Frontend

- React
- Axios
- Tailwind CSS
- `xlsx` for Excel export

## Repository Layout

```text
Job_Scrapper/
├── backend/
│   ├── app/
│   │   ├── api/routes.py                    # Active API endpoints
│   │   ├── main.py                          # FastAPI app entrypoint
│   │   ├── models.py                        # SQLite models
│   │   ├── schemas.py                       # Request/response schemas
│   │   ├── services/
│   │   │   ├── job_relevance_screener.py    # Deterministic + optional Mistral screening
│   │   │   └── scraper_orchestrator.py      # LinkedIn-only orchestration
│   │   └── scrapers/
│   │       └── linkedin_scraper.py          # Active scraper
│   ├── requirements.txt
│   └── setup.sh
├── frontend/
│   ├── src/App.js                           # Search, polling, results, Excel download
│   ├── src/components/
│   └── src/services/api.js                  # Frontend API client
├── render.yaml                              # Render deployment config
└── start.sh                                 # Starts backend + frontend locally
```

## Local Setup

### Prerequisites

- Python 3
- Node.js and npm

### Backend

```bash
cd backend
chmod +x setup.sh
./setup.sh
```

`backend/setup.sh` does the following:

- creates `backend/venv`
- installs Python dependencies from `backend/requirements.txt`
- installs Playwright Chromium
- creates `backend/.env` from `backend/.env.example` if missing
- creates `backend/.env.secrets` from `backend/.env.secrets.example` if missing
- creates `backend/data`

Run the API:

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

Backend default URL: [http://localhost:8000](http://localhost:8000)

### Frontend

```bash
cd frontend
npm install
npm start
```

Frontend default URL: [http://localhost:3000](http://localhost:3000)

### Start Both Together

From the repository root:

```bash
chmod +x start.sh
./start.sh
```

## Configuration

The backend loads:

- `backend/.env`
- `backend/.env.secrets` with override priority for secret values

### `backend/.env`

Template values are defined in `backend/.env.example`.

Common settings:

```env
DATABASE_URL=sqlite:///./data/job_scrapper.db
SECRET_KEY=your_random_secret_key_here
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
MAX_UPLOAD_SIZE=10485760
SCRAPING_TIMEOUT=300
MAX_JOBS_PER_SOURCE=50
```

### `backend/.env.secrets`

Template values are defined in `backend/.env.secrets.example`.

Optional secret:

```env
MISTRAL_API_KEY=your_mistral_api_key_here
```

If `MISTRAL_API_KEY` is not set, the app still runs and falls back to deterministic filtering.

### Frontend Environment

The frontend reads:

```env
REACT_APP_API_URL=http://localhost:8000
```

The frontend strips a trailing `/api` automatically if you include it by mistake.

## API

The FastAPI router is mounted under `/api`.

### `GET /`

Basic health/info response:

```json
{
  "name": "Job Scrapper API",
  "version": "1.0.0",
  "status": "running"
}
```

### `GET /health`

Returns service health plus whether Mistral is configured.

### `POST /api/scrape-jobs`

Starts a background scrape.

Request body:

```json
{
  "role_titles": "Software Engineer, Backend Engineer",
  "locations": "Remote, New York",
  "target_jobs": 25,
  "recent_days": 1
}
```

Notes:

- `role_titles` is required.
- `locations` may be blank; blank means any location.
- `target_jobs` must be between `1` and `200`.
- `recent_days` must be between `1` and `30`, but the current frontend always sends `1`.
- The backend creates every role/location combination and scrapes each combination.

Example response:

```json
{
  "task_id": "9d3f4b43-5d9d-4b2c-9e52-4b35d3bcb4d8",
  "status": "pending",
  "message": "Scraping task started successfully",
  "parsed_roles": ["Software Engineer", "Backend Engineer"],
  "parsed_locations": ["Remote", "New York"],
  "target_jobs": 25
}
```

### `GET /api/scraping-status/{task_id}`

Returns task state:

- `pending`
- `running`
- `completed`
- `failed`

Example response:

```json
{
  "task_id": "9d3f4b43-5d9d-4b2c-9e52-4b35d3bcb4d8",
  "status": "running",
  "progress": 42,
  "total_jobs_scraped": 11,
  "sources_completed": ["linkedin:last_3_days"],
  "error_message": null,
  "started_at": "2026-03-08T10:30:00.000000",
  "completed_at": null
}
```

### `POST /api/jobs`

Returns scraped jobs sorted by `posted_date` descending.

Request body:

```json
{
  "limit": 25,
  "task_id": "optional-task-id"
}
```

Notes:

- `limit` must be between `1` and `200`.
- `task_id` is returned in the response for client context, but the current backend does not filter jobs by task.
- The endpoint currently returns only jobs whose source is `linkedin`.

Example response shape:

```json
{
  "task_id": "optional-task-id",
  "total_jobs": 25,
  "jobs": [
    {
      "id": 1,
      "title": "Backend Engineer",
      "company": "Example Inc",
      "location": "Remote",
      "job_type": "remote",
      "employment_type": "full-time",
      "description": "",
      "required_skills": [],
      "required_experience": null,
      "salary_range": "",
      "apply_url": "https://www.linkedin.com/jobs/view/1234567890/",
      "source": "linkedin",
      "posted_date": "2026-03-08T09:00:00",
      "scraped_at": "2026-03-08T10:30:05"
    }
  ]
}
```

## Scraping Behavior

The current scrape pipeline in `backend/app/api/routes.py` and `backend/app/services/scraper_orchestrator.py` works like this:

1. Parse comma-separated roles and locations.
2. Create a `ScrapingTask`.
3. Delete previously stored jobs.
4. For each role/location combination, scrape LinkedIn guest job listings.
5. Start with a 1-day posting window.
6. If the target count is not met, increase the window by 1 day and try again.
7. Stop when the target count is reached or the search reaches 180 days of backfill.
8. Persist accepted jobs to SQLite.

## Frontend Behavior

The React app currently provides:

- a search form for role titles, locations, and target count
- task polling every 2.5 seconds
- live result updates while the scrape is still running
- a table with company, role, location, posted date, and apply link
- Excel download of the currently loaded jobs

## Data Storage

SQLite models currently used by the active flow:

- `jobs`
- `user_sessions`
- `scraping_tasks`

Default local database path:

```text
backend/data/job_scrapper.db
```

One important implementation detail: starting a new scrape clears the existing contents of `jobs` before inserting the new run's results.

## Deployment

`render.yaml` defines two Render services:

- `job-scrapper-api`
- `job-scrapper-web`

The backend runs with:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

The frontend is built as a static site with:

```bash
npm ci && npm run build
```

## Quick Manual Test

1. Start the backend.
2. Start the frontend.
3. Open [http://localhost:3000](http://localhost:3000).
4. Enter a role such as `Software Engineer`.
5. Optionally enter a location such as `Remote`.
6. Start scraping.
7. Confirm live progress updates appear.
8. Confirm results appear and can be exported to Excel.
