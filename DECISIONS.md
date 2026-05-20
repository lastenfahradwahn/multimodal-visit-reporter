# DECISIONS.md

This document records the key architectural decisions, tradeoffs, and
rationale behind the Multimodal Visit Reporter MVP. It is written for
the interviewing team evaluating the project.

---

## 1. Stack and tooling choices

### Backend: Python 3.13 + FastAPI

FastAPI was chosen for its async support, automatic OpenAPI docs, and
clean separation between API routes and business logic. It is lightweight
enough to run on a Raspberry Pi 5 (the development environment) yet
scales to cloud deployment without changes. Python 3.13 is used for
forward-compatibility with modern type hints and performance improvements.

### Frontend: Streamlit

Streamlit offers the fastest path to a polished, interactive UI for
internal tools. It requires no JavaScript and integrates naturally
with Python service calls. The tradeoff is that Streamlit is not suited
for public multi-user apps without additional auth — acceptable for an
MVP whose users are a small sales team behind a VPN.

### AI integration: LiteLLM library (no proxy)

LiteLLM provides a unified, provider-agnostic API for calling models
across OpenAI, Anthropic, Groq, and OpenRouter. This means:

- Swapping a model is a one-string change (no SDK rewrite).
- Cost tracking, token counting, and future rate-limiting can be added
  through LiteLLM's callback system without touching extraction logic.
- No operational overhead from running a proxy server — the library
  runs in-process.

The project deliberately does **not** use LiteLLM's proxy mode to keep
the architecture simple for an MVP.

### Model selection

| Stage          | Model                                      | Why                                                       |
|----------------|--------------------------------------------|-----------------------------------------------------------|
| Transcription  | `groq/whisper-large-v3` (direct Groq API) | Fastest Whisper inference available; free tier sufficient |
| Image → text   | `openrouter/mistralai/pixtral-12b`         | Strong vision-language model; EU-based (GDPR-friendly)    |
| Text → JSON    | `openrouter/google/gemini-2.0-flash-001`   | Fast, cheap, reliable JSON; large context window          |

**Why Gemini Flash instead of Mistral Small?**
The original plan used Mistral Small (`mistral-small-3.1-24b-instruct`)
because it is EU-hosted and GDPR-friendly. In testing on OpenRouter's
free tier, Mistral Small frequently returned truncated JSON (cut off
mid-response). Switching to Gemini Flash resolved this; it produced
clean, complete JSON on every test run with `temperature=0.0` and
`max_tokens=1024`.

**GDPR note:** Gemini Flash is a Google model (US infrastructure).
In production, the model string would be changed to an Azure AI Foundry
deployment of Mistral Small or another EU-hosted model. The LiteLLM
abstraction makes this a single-line change in `app/services/ai.py`,
with no other code affected.

### Persistence: JSON file (`data/visits.json`)

A flat JSON file was chosen for the MVP because:

- Zero setup — no database server, no schema migrations.
- The target user is a single sales rep; concurrent writes are not a
  concern.
- The `app/services/storage.py` module exposes `load_visits()` and
  `save_visit()` as its only public interface. Swapping to SQLite or
  Postgres requires changing only that module; the rest of the app
  calls the same functions with the same contracts.

The known risk — file corruption on concurrent writes — is documented
here and accepted for the MVP scope.

---

## 2. AI integration and prompt design

### Two-step image extraction

Images go through a two-stage pipeline:

1. **Vision model (Pixtral)** describes the image in natural language,
   capturing visible text, diagrams, and key elements.
2. **Text model (Gemini Flash)** extracts structured JSON from that
   description.

This design was chosen over single-step "image → JSON" because:

- Vision-language models are less reliable at strict JSON formatting;
  they often add conversational text or miss closing braces.
- Separating description from extraction lets each model do what it
  does best — the VLM handles visual noise and OCR-like challenges,
  the LLM handles precise structured output.
- Either model can be upgraded or replaced independently, without
  redesigning the pipeline.

Audio follows an analogous two-step path: Whisper transcribes to text,
then the text model extracts JSON.

### Prompt engineering

The system prompt (`app/prompts.py`) instructs the model to:

- Output **only** a JSON object.
- Not include markdown fences, code blocks, or extra commentary.
- Follow the exact schema with field descriptions and defaults.

The completion call uses `temperature=0.0` (maximum determinism) and
`max_tokens=1024` (prevents truncation while allowing a full report).

### Graceful JSON parsing

Even with a strict prompt, models occasionally wrap JSON in backticks
or add a short sentence. The `_extract_json()` function handles this:

1. Attempt `json.loads()` on the entire response.
2. If that fails, scan for the first balanced `{...}` pair using brace
   counting and parse the substring.
3. If both fail, raise a `ValueError` with a descriptive message.

The caller (the API route) catches this and returns an HTTP 422 so the
UI can display a clear error to the user — no crash, no blank screen.

### Provider failure handling

All AI calls are wrapped in `try/except`. Exceptions are logged via
Python's standard `logging` module and re-raised. The API layer catches
them and maps them to appropriate HTTP status codes (422 for extraction
failures, 502/503 for provider outages). The user always sees an error
state, never a silent failure.

---

## 3. Tradeoffs given the time constraint

### Model switch (Mistral Small → Gemini Flash)

The biggest tradeoff. Mistral Small aligned with the preference for
EU-hosted models but was unreliable on the free tier (truncated JSON).
Gemini Flash worked immediately and reliably. The LiteLLM abstraction
makes this reversible with one line of code — in production, switching
to a GDPR-compliant deployment (e.g., Azure AI Foundry + Mistral) is
straightforward.

### No streaming responses

The app waits for the full AI response before showing results. Streaming
would improve perceived speed, but adds complexity in error handling and
partial-JSON parsing. Deferred to "next day" work.

### No browser audio recording

Users must upload an audio file rather than recording directly in the
browser. This avoids WebRTC/microphone permission complexity. Streamlit's
`audio_input` component could be added later with minimal changes.

### JSON file storage

Chosen for zero-setup. The known concurrency problem (simultaneous writes
can corrupt the file) is mitigated by atomic read-append-write and is
acceptable for single-user MVP use. The storage module is designed so a
database can replace it without touching any other code.

### No authentication

The MVP assumes a single trusted user (the sales rep running it locally
or behind a VPN). Adding auth would require session management, user
models, and a proper database — all out of scope for a 4–6 hour timebox.

---

## 4. What I would tackle next with another day of work

### 1. SQLite persistence (with async support)

Replace `data/visits.json` with SQLite via `aiosqlite`. The storage
module already has a clean interface, so this is a drop-in replacement.
Benefits: no corruption on concurrent writes, queryable history, and
a migration path to Postgres if needed later.

### 2. Proper test suite

Write `pytest` tests for:
- The `_extract_json` fallback parser with edge cases (extra text,
  multiple braces, empty response).
- The storage module (round-trip, corrupt file, empty file).
- AI pipeline with mocked LiteLLM responses (fast, deterministic,
  runnable in CI without API keys).

### 3. Streaming AI extraction

Use Server-Sent Events (SSE) or Streamlit's streaming to show the
AI response as it arrives. This improves UX for longer extractions
and demonstrates an understanding of real-time patterns. LiteLLM
supports streaming with minimal changes to the completion call.

### 4. Prompt versioning and A/B testing

Extract prompts into versioned files (e.g., `prompts/v1_system.txt`)
and log which prompt version produced each extraction. This enables
data-driven prompt iteration — critical for production AI products.

### 5. Docker containerisation

Write a `Dockerfile` and `docker-compose.yml`. This standardises the
runtime, simplifies onboarding (replaces the Python venv setup), and
prepares for cloud deployment on RunPod, Fly.io, or a VPS.

---

*This document will be updated as the project evolves. The latest version
accompanies the GitHub repository at `git@github.com:lastenfahradwahn/multimodal-visit-reporter.git`.*
