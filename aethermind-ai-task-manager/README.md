# AetherMind — Personal AI Task Manager

A beginner-friendly CSB312 CA3 mini-project demonstrating:
- Streamlit frontend
- FastAPI backend
- Mistral AI structured JSON extraction
- Pydantic validation
- SQLite create/read/update operations
- Error handling and tests
- Deployment configuration

## 1. Requirements
- Python 3.10 or newer
- VS Code
- A Mistral API key (for AI extraction): https://console.mistral.ai/

## 2. Open the project
Extract the ZIP, then open the `aethermind_ai_task_manager` folder in VS Code.

Open Terminal in VS Code and run:

```bash
python -m venv .venv
```

Activate it:

**Windows PowerShell**
```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, use:
```powershell
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
```
Then use `.venv\Scripts\python.exe` instead of `python` in commands.

**macOS/Linux**
```bash
source .venv/bin/activate
```

Install dependencies:
```bash
pip install -r backend/requirements.txt
pip install -r frontend/requirements.txt
```

## 3. Configure the AI key
Copy `backend/.env.example` to `backend/.env`, then add your Mistral API key:
```env
MISTRAL_API_KEY=your_real_key_here
MISTRAL_MODEL=mistral-small-latest
DATABASE_PATH=./aethermind.db
CORS_ORIGINS=http://localhost:8501
```
Never commit or share your `.env` file. The project includes `.gitignore` to help prevent this.

## 4. Run locally (two terminals)
**Terminal 1 — backend**
From the project root:
```bash
uvicorn backend.main:app --reload --port 8000
```
API docs: http://127.0.0.1:8000/docs

**Terminal 2 — frontend**
```bash
streamlit run frontend/app.py
```
Open the local URL Streamlit prints (usually http://localhost:8501).

## 5. Use the app
Enter something like:
> Finish my GenAI assignment by Friday. High priority.

Click **Extract and save task**. Review the extracted fields and confirm before saving. The saved task appears in **Your tasks**. The AI may not infer an exact date if "Friday" is ambiguous; review and edit the date before saving.

You can also add a task without an AI key using the manual form. The AI extraction button requires a valid key and internet access.

## 6. Tests
With the virtual environment active:
```bash
pytest -q
```
The tests use a temporary SQLite database and do not call the live AI service.

## 7. Deployment (required by the assignment)
The frontend and backend are separate services. Deploy both, then configure the frontend with the backend URL.

### Backend on Render
1. Push the project to a GitHub repository.
2. Create a new **Web Service** on Render and connect the repo.
3. Build command:
   `pip install -r backend/requirements.txt`
4. Start command:
   `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
5. Set environment variables:
   - `MISTRAL_API_KEY` = your secret key
   - `MISTRAL_MODEL` = `mistral-small-latest`
   - `DATABASE_PATH` = `./aethermind.db`
   - `CORS_ORIGINS` = your Streamlit app URL (add after deploying frontend)
6. Deploy and test `https://YOUR-BACKEND.onrender.com/health`.

**Important database note:** a local SQLite file on a free cloud instance may be ephemeral and may not persist across redeploys/restarts. For a durable deployed demo, use a persistent disk if supported by your hosting plan, or replace SQLite with a hosted database. SQLite is suitable for local evaluation and the basic project demonstration.

### Frontend on Streamlit Community Cloud
1. Ensure `frontend/` and the root `requirements.txt` are committed to GitHub.
2. In Streamlit Community Cloud, choose your repo and set the app file path to `frontend/app.py`.
3. Add a secret in app settings:
   ```toml
   BACKEND_URL = "https://YOUR-BACKEND.onrender.com"
   ```
4. Redeploy the app.
5. Update the backend `CORS_ORIGINS` with your deployed Streamlit URL, then redeploy backend.

The frontend must connect to the deployed backend. Submit the **deployed frontend URL** as the assignment requires.

## 8. Viva explanation (simple)
- **Frontend:** Streamlit collects the user's text and shows results.
- **Backend:** FastAPI exposes endpoints, calls the AI, validates output, and writes to SQLite.
- **Schema-guided prompting:** the prompt requests fixed JSON fields with specific types.
- **Pydantic:** checks that AI output follows the required schema and field constraints.
- **Database:** SQLite stores tasks; POST creates a task, GET lists tasks, PATCH marks one complete.
- **Error handling:** missing text, invalid AI JSON, failed AI request, and failed backend requests are handled.
- **Human confirmation:** the frontend previews extracted fields before saving.
