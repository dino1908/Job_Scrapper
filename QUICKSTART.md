# Quick Start Guide

Get the Job Scrapper running in 5 minutes!

## Prerequisites

- Python 3.8+
- Node.js 16+
- Chrome/Chromium browser

## Backend Setup (2 minutes)

1. **Navigate to backend:**
   ```bash
   cd backend
   ```

2. **Run setup script:**
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

3. **Configure API keys:**
   ```bash
   # Edit .env file
   nano .env  # or use your favorite editor
   ```

   **Add your Mistral API key:**
   - `MISTRAL_API_KEY` - Get key at https://console.mistral.ai/api-keys/

   **Example .env:**
   ```
   MISTRAL_API_KEY=your_actual_key_here
   ```

   **Note:** The API key is already configured in the .env file!

4. **Start backend server:**
   ```bash
   source venv/bin/activate  # Activate virtual environment
   uvicorn app.main:app --reload
   ```

   ✅ Backend running at: http://localhost:8000

## Frontend Setup (1 minute)

1. **Open new terminal and navigate to frontend:**
   ```bash
   cd frontend
   ```

2. **Start frontend:**
   ```bash
   npm start
   ```

   ✅ Frontend running at: http://localhost:3000

## Using the Application

### Step 1: Upload Resume
1. Open http://localhost:3000
2. Drag and drop your resume (PDF or DOCX)
3. Wait for AI analysis (~5 seconds)

### Step 2: Job Scraping
- Automatically starts after resume upload
- Scrapes from: Indeed, RemoteOK, Remotive, LinkedIn, Wellfound
- Takes 1-3 minutes
- Shows real-time progress

### Step 3: View Results
- Jobs ranked by match score (0-100%)
- Filter by score, source, or search term
- Click "Apply Now" to visit job posting

## Troubleshooting

### Backend Issues

**"Module not found" errors:**
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

**"Playwright not found":**
```bash
playwright install chromium
```

**"No LLM API keys" warning:**
- The Mistral API key should already be in your `.env` file
- If not, get one at: https://console.mistral.ai/api-keys/
- Add to `.env` file

### Frontend Issues

**"Module not found" errors:**
```bash
cd frontend
npm install
```

**CORS errors:**
- Ensure backend is running on port 8000
- Check `.env` has correct API URL

### Scraping Issues

**LinkedIn fails:**
- Expected - LinkedIn has strong anti-bot measures
- Try other sources (Indeed, RemoteOK, Remotive)

**Few jobs found:**
- Normal - depends on query and availability
- Try broader search terms
- RemoteOK and Remotive always work

## Testing Without Resume

You can test the API directly:

```bash
# Check health
curl http://localhost:8000/health

# View API docs
open http://localhost:8000/docs
```

## What's Next?

- Upload different resumes to see varied results
- Adjust minimum match score filter
- Check different job sources
- Review match breakdowns to understand scoring

## API Key Already Configured!

**Good news:** The Mistral API key is already configured in your `backend/.env` file!

If you need to get a new one:
1. Visit: https://console.mistral.ai/api-keys/
2. Sign up or sign in
3. Click "Create new key"
4. Copy and replace in `.env`

**Mistral Pricing:**
- Pay-as-you-go (very affordable)
- `mistral-small-latest` is cost-effective for resume analysis
- Typically < $0.01 per resume analysis

## Need Help?

- Check `/docs` endpoint for full API documentation
- Review `README.md` for detailed information
- Check backend logs for error messages
- Ensure all prerequisites are installed

## Minimal Working Setup

If you're having issues, here's the absolute minimum:

1. **Backend only:**
   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate
   pip install fastapi uvicorn sqlalchemy pdfplumber python-docx google-generativeai

   # Create .env with Gemini key
   echo "GEMINI_API_KEY=your_key" > .env

   # Run server
   uvicorn app.main:app
   ```

2. **Test with curl:**
   ```bash
   # Health check
   curl http://localhost:8000/health

   # Should show: {"status": "healthy", "gemini_api": "configured"}
   ```

3. **Then add frontend** when backend works

---

**Ready to find your next job? Let's go! 🚀**
