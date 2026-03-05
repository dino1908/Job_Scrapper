# Mistral AI Configuration

## API Key Setup

Store your Mistral API key in `backend/.env.secrets`:

```
MISTRAL_API_KEY=your_mistral_api_key_here
```

`backend/.env.secrets` is gitignored and should never be committed.

## How It Works

The application uses **Mistral AI** (`mistral-large-latest` model) to analyze resumes and extract:
- Skills (technical & soft skills)
- Years of experience
- Job titles/roles
- Education level
- Job type preference (remote/hybrid/onsite)
- Location preferences

## What Changed

The application was updated from Gemini/OpenAI to Mistral AI:

### Updated Files:
- ✅ `backend/.env.secrets` - API key configured
- ✅ `backend/app/config.py` - Uses `MISTRAL_API_KEY`
- ✅ `backend/app/main.py` - Health check updated
- ✅ `backend/app/services/llm_analyzer.py` - Completely rewritten for Mistral
- ✅ `backend/requirements.txt` - Added `mistralai` package
- ✅ `plan.md` - API key removed for security

### Installation

The Mistral package will be installed when you run:

```bash
cd backend
./setup.sh
```

Or manually:

```bash
cd backend
source venv/bin/activate
pip install mistralai==1.0.1
```

## Testing the Integration

Once the backend is running, check the health endpoint:

```bash
curl http://localhost:8000/health
```

You should see:

```json
{
  "status": "healthy",
  "database": "connected",
  "mistral_api": "configured"
}
```

## API Usage & Costs

**Model:** `mistral-large-latest`

**Pricing (as of 2024):**
- Input: $2 per 1M tokens
- Output: $6 per 1M tokens

**Typical Resume Analysis:**
- Input tokens: ~1,000 tokens (resume text + prompt)
- Output tokens: ~300 tokens (JSON response)
- **Cost per resume: ~$0.004 (less than half a cent)**

**For 100 resumes:** ~$0.40

**Why Mistral Large:**
- More accurate extraction
- Better understanding of context
- Handles complex resumes better

**Very affordable for a job matching application!**

## Fallback Behavior

If the Mistral API fails for any reason, the system automatically falls back to regex-based extraction:
- Still extracts skills, experience, and roles
- Less accurate but functional
- No API costs

## Troubleshooting

### "Mistral API not configured" warning

If you see this warning on startup:
1. Check `backend/.env.secrets` file exists
2. Verify `MISTRAL_API_KEY` is set
3. Restart the backend server

### Mistral API errors

If resume analysis fails:
1. Check your internet connection
2. Verify the API key is valid at https://console.mistral.ai/
3. Check the console logs for detailed error messages

The system will automatically fall back to basic extraction if Mistral fails.

## Getting a New API Key (if needed)

If you need to regenerate your API key:

1. Visit: https://console.mistral.ai/api-keys/
2. Sign in with your account
3. Click "Create new key"
4. Copy the key
5. Replace in `backend/.env.secrets`:
   ```
   MISTRAL_API_KEY=your_new_key_here
   ```
6. Restart the backend server

## API Key Security

**Important:**
- ✅ The API key has been removed from `plan.md`
- ✅ It's now only in `backend/.env.secrets` (which is in `.gitignore`)
- ✅ Never commit `.env` or `.env.secrets` files to version control
- ✅ Use `.env.example` and `.env.secrets.example` for sharing configuration templates

---

**You're all set! The Mistral API is configured and ready to use.** 🚀
