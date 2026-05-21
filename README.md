# Multimodal Visit Reporter

Extract structured visit reports from audio recordings, whiteboard photos, or
typed notes — using AI. Built for sales reps who want to document customer
visits in seconds, not minutes.

## Quick Start (under 5 minutes)

### Prerequisites

- Python 3.12+
- Git
- An [OpenRouter](https://openrouter.ai) account with credits
- A [Groq](https://console.groq.com) account (free tier works)

### Setup

```bash
git clone git@github.com:lastenfahradwahn/multimodal-visit-reporter.git
cd multimodal-visit-reporter
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create your environment file from the template 

```bash
cp .env.example .env
```

Now edit .env and replace the placeholders with your real API keys

```bash
nano .env
```

### Run

Start the *backend* in one terminal:

```bash
source venv/bin/activate
python -m app.main
```

Start the *frontend* in another terminal:

Open [http://localhost:8501](http://localhost:8501) and upload a text note, audio file, or whiteboard photo. The AI extraxts a structured report you can edit and save.

##Project Structure

```text
app/
  main.py              # FastAPI entry point
  models.py            # Pydantic Visit data model
  prompts.py           # AI prompt templates
  routers/
    visits.py          # /api/visits REST endpoints
  services/
    ai.py              # AI orchestration (LiteLLM → Groq / OpenRouter)
    storage.py         # JSON file persistence
ui/
  app.py               # Streamlit frontend
tests/
  test_ai.py           # Manual extraction smoke test
data/
  .gitkeep
.env.example           # Environment variable template
```

## Architecture Highlights
Let's switch to `main`, add the `.env.example`, and write the full `README.md`. This keeps the documentation commits on the clean main branch.

---

## Step‑by‑step

### 1. Switch to main
```bash
git checkout main
```

### 2. Create `.env.example` (the template with no real keys)
```bash
cat > .env.example << 'EOF'
# Copy this file to .env and fill in your real keys
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
EOF
```

### 3. Write the README
Open nano:
```bash
nano README.md
```
Paste the content below (I’ve rewritten it with the `.env.example` flow and a cleaner setup):

```markdown
# Multimodal Visit Reporter

Extract structured visit reports from audio recordings, whiteboard photos, or
typed notes — using AI. Built for sales reps who want to document customer
visits in seconds, not minutes.

## Quick Start (under 5 minutes)

### Prerequisites

- Python 3.12+
- Git
- An [OpenRouter](https://openrouter.ai) account with credits
- A [Groq](https://console.groq.com) account (free tier works)

### Setup

```bash
git clone git@github.com:lastenfahradwahn/multimodal-visit-reporter.git
cd multimodal-visit-reporter
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create your environment file from the template
cp .env.example .env
# Now edit .env and replace the placeholders with your real API keys
nano .env
```

### Run

Start the **backend** in one terminal:

```bash
source venv/bin/activate
python -m app.main
```

Start the **frontend** in another terminal:

```bash
source venv/bin/activate
streamlit run ui/app.py --server.port 8501 --server.address 0.0.0.0
```

Open **http://localhost:8501** and upload a text note, audio file, or whiteboard
photo. The AI extracts a structured report you can edit and save.

## Project Structure

```
app/
  main.py              # FastAPI entry point
  models.py            # Pydantic Visit data model
  prompts.py           # AI prompt templates
  routers/
    visits.py          # /api/visits REST endpoints
  services/
    ai.py              # AI orchestration (LiteLLM → Groq / OpenRouter)
    storage.py         # JSON file persistence
ui/
  app.py               # Streamlit frontend
tests/
  test_ai.py           # Manual extraction smoke test
data/
  .gitkeep
.env.example           # Environment variable template
```

## Architecture Highlights

- **Backend:** FastAPI (async, auto-generated OpenAPI docs at
  http://localhost:8000/docs)
- **Frontend:** Streamlit — pure Python, internal‑tool UX
- **AI Integration:** LiteLLM library orchestrates three models via OpenRouter
  and Groq:
  - Audio transcription → Groq Whisper (`groq/whisper-large-v3`)
  - Image description → Mistral Pixtral Large
    (`openrouter/mistralai/pixtral-large-2411`)
  - Text → structured JSON → Google Gemini Flash
    (`openrouter/google/gemini-2.0-flash-001`)
- **Storage:** JSON file (`data/visits.json`) behind a repository interface
  that can be swapped for a database with zero changes to the rest of the
  codebase.

Full decision documentation: [`DECISIONS.md`](DECISIONS.md)  
Production infrastructure design: [`INFRASTRUCTURE.md`](INFRASTRUCTURE.md)

## License

MIT? (SBOM Pending).
