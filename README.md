# Job Scrapper

Find fresh job openings fast, locally, and for free.

Job Scrapper helps you search recent jobs by role and location, keep widening the search window until it hits your target count, and export the results to Excel. It is designed to give you a speed advantage when applying early, while keeping everything simple and local.

## Why This Project

- Runs locally on your machine
- Free to use for the core workflow
- Search by one or more role titles
- Search by one or more locations
- Set the number of jobs you want to collect
- Starts from the latest postings and searches backward by date until it finds enough jobs
- Download results as an Excel file
- Optional AI filtering layer to reduce irrelevant or garbage roles
- No paid backend or hosted service required

## How It Works

1. Enter one or more role titles
2. Enter one or more locations, or leave location blank
3. Choose how many jobs you want
4. Start the search
5. The app keeps expanding the time window backward until it reaches your target or runs out of matching results
6. Download the final list as an Excel file

## Tech Stack

- Frontend: React
- Backend: FastAPI
- Database: SQLite
- Export: Excel `.xlsx`
- Optional AI filtering: Mistral

## Quick Setup

### Prerequisites

Install these first:

- Git
- Python 3.9+
- Node.js 18+ and npm

## 1. Clone the Repo

```bash
git clone https://github.com/dino1908/Job_Scrapper.git
cd Job_Scrapper
```

## 2. Backend Setup

### macOS / Linux

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Windows PowerShell

```powershell
cd backend
py -3 -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 3. Configure Environment

Create the backend config files if they do not already exist.

### `backend/.env`

Copy the example file:

```bash
cp .env.example .env
```

This project works with the default local database setup, so in most cases you do not need to change anything here.

### `backend/.env.secrets`

Copy the example file:

```bash
cp .env.secrets.example .env.secrets
```

Then add your Mistral key if you want AI filtering:

```env
MISTRAL_API_KEY=your_mistral_api_key_here
```

Notes:

- Mistral is optional
- The app still works without it
- Without Mistral, the app uses built-in filtering only
- The core workflow is still local and free
- If you enable Mistral, your usage depends on your own API account

## 4. Start the Backend

### macOS / Linux

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

### Windows PowerShell

```powershell
cd backend
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

Backend will run at:

```text
http://localhost:8000
```

API docs:

```text
http://localhost:8000/docs
```

## 5. Start the Frontend

Open a new terminal.

```bash
cd frontend
npm install
npm start
```

Frontend will run at:

```text
http://localhost:3000
```

## Using the App

1. Open `http://localhost:3000`
2. Enter role titles
   Example: `Software Engineer, Backend Engineer, Data Analyst`
3. Enter locations
   Example: `Remote, New York, Bangalore`
4. Set your target number of jobs
5. Start the search
6. Watch live progress
7. Download the results as Excel

## Optional AI Filtering

If you add a Mistral API key, the app can apply an extra AI layer to help remove low-quality or irrelevant roles.

This is useful when:

- job titles are noisy
- search results include unrelated roles
- you want cleaner output before exporting

If no key is added, the app still runs normally.

## Notes for macOS vs Windows

The main difference is virtual environment activation:

- macOS / Linux:
  ```bash
  source venv/bin/activate
  ```

- Windows PowerShell:
  ```powershell
  .\venv\Scripts\Activate.ps1
  ```

Everything else is mostly the same.

## Troubleshooting

### Backend does not start

Make sure Python is installed and your virtual environment is activated.

### Frontend does not start

Make sure Node.js and npm are installed.

### AI filtering does not work

Check that `MISTRAL_API_KEY` is set correctly in `backend/.env.secrets`.

### Port already in use

If port `3000` or `8000` is busy, stop the existing process or run on a different port.

## Summary

Job Scrapper is built for fast, local job discovery:

- quick setup
- local-first workflow
- multiple roles and locations
- target-based search
- backward date expansion
- Excel export
- optional AI cleanup layer
