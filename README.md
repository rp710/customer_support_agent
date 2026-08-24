# Insurance Claims Copilot

An internal claims-adjuster workbench for registering auto claims/FNOLs, retrieving relevant policy guidance, and generating editable AI coverage recommendations. A licensed adjuster remains responsible for the final decision.

## What it does

- Registers customers and claims through a Streamlit dashboard.
- Stores customers, tickets, and recommendation drafts in SQLite.
- Retrieves policy and claims guidance from the Markdown files in `knowledge_base/` using ChromaDB.
- Searches customer and company claim history using the memory integration.
- Uses a Groq-hosted LangChain agent with operational tools for customer plan and open-ticket checks.
- Lets an adjuster edit, approve, or request more information for a recommendation.
- Saves approved resolutions back to memory for future recommendations.

## Architecture

```text
Streamlit dashboard (app.py)
            |
            v
FastAPI API (main.py)
  |         |          |
  v         v          v
SQLite    ChromaDB   SupportCopilot
                    |       |       |
                    v       v       v
                 Memory    RAG    Groq agent/tools
```

The main application code is in `customer_support_agent/`. The package under `src/insurance_agent_project/` is the original project scaffold and is not used by the dashboard/API startup commands.

## Requirements

- Python 3.14 or newer (as specified in `pyproject.toml`)
- A Groq API key for recommendation generation
- `uv` or `pip`

## Installation

Using `uv`:

```bash
uv sync
```

Using `pip`:

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
# source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```dotenv
GROQ_API_KEY=your-groq-api-key
GROQ_MODEL=openai/gpt-oss-120b
LLM_TEMPERATURE=0.2
API_HOST=127.0.0.1
API_PORT=8000
DASHBOARD_API_URL=http://localhost:8000
```

`GOOGLE_API_KEY` is optional. It is used by the memory integration when available; memory still falls back to an in-process store when semantic embeddings cannot be initialized.

## Run locally

Start the API in one terminal:

```bash
python main.py
```

Start the dashboard in a second terminal:

```bash
streamlit run app.py
```

Open:

- Dashboard: <http://localhost:8501>
- FastAPI Swagger UI: <http://localhost:8000/docs>
- Health check: <http://localhost:8000/health>

The API creates the required local directories and initializes the SQLite schema on startup. The dashboard uses `API_BASE_URL` if set; otherwise it calls `http://localhost:8000`.

## Typical workflow

1. Open the Streamlit dashboard.
2. Optionally click **Ingest Policy & Regulation KB** in the sidebar.
3. Register a claim with claimant, policy, incident, loss, and FNOL details.
4. Generate a coverage recommendation automatically or manually.
5. Review the recommendation and inspect the memory, policy, and tool context.
6. Edit and approve the recommendation, or mark it as a request for more information.
7. Approved recommendations resolve the ticket and are added to customer/company memory.

## API endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Health probe |
| `POST` | `/api/tickets` | Create a customer/claim; optionally generate a draft in the background |
| `GET` | `/api/tickets` | List claims |
| `GET` | `/api/tickets/{ticket_id}` | Get one claim |
| `POST` | `/api/tickets/{ticket_id}/generate-draft` | Generate a recommendation manually |
| `GET` | `/api/drafts/{ticket_id}` | Get the latest draft for a claim |
| `PATCH` | `/api/drafts/{ticket_id}` | Update draft content/status (`pending`, `accepted`, or `discarded`) |
| `POST` | `/api/knowledge/ingest` | Index Markdown/text knowledge-base files into ChromaDB |
| `GET` | `/api/customers/{customer_id}/memories` | List customer/company memories |
| `GET` | `/api/customers/{customer_id}/memory-search` | Search customer/company memories |

Interactive request/response schemas are available at `/docs` when the API is running.

## Knowledge base

The current knowledge base contains insurance claims guidance plus sample banking FAQs. Ingestion reads `.md` and `.txt` files from `knowledge_base/`, splits them into overlapping chunks, and stores them in the persistent Chroma collection `support_kb`.

From the dashboard, use **Ingest Policy & Regulation KB**, or call the API:

```bash
curl -X POST http://localhost:8000/api/knowledge/ingest \
  -H "Content-Type: application/json" \
  -d '{"clear_existing": false}'
```

Use `{"clear_existing": true}` when rebuilding the collection from scratch.

## Configuration

Important settings can be supplied through environment variables or `.env`:

| Variable | Default | Description |
| --- | --- | --- |
| `GROQ_API_KEY` | empty | Required for the AI copilot |
| `GROQ_MODEL` | `openai/gpt-oss-120b` | Groq model used by the agent |
| `LLM_TEMPERATURE` | `0.2` | Model temperature |
| `GOOGLE_API_KEY` | empty | Optional memory embedding key |
| `DB_PATH` | `data/support.db` | SQLite database path |
| `CHROMA_RAG_DIR` | `data/chroma_rag` | Persistent RAG data directory |
| `KNOWLEDGE_BASE_DIR` | `knowledge_base` | Source documents directory |
| `RAG_TOP_K` | `4` | Number of policy chunks retrieved |
| `MEM0_TOP_K` | `5` | Number of memory hits retrieved per scope |
| `API_HOST` | `127.0.0.1` | API bind address |
| `API_PORT` | `8000` | API port |
| `DASHBOARD_API_URL` | `http://localhost:8000` | Configured dashboard API URL |

## Project layout

```text
app.py                              Streamlit adjuster dashboard
main.py                             FastAPI/Uvicorn entry point
customer_support_agent/
  api/                              FastAPI app factory, dependencies, routers
  core/                             Pydantic settings and directory setup
  integrations/
    memory/                         LangMem/LangGraph memory adapter
    rag/                            ChromaDB knowledge-base adapter
    tools/                          Agent tools
  repositories/sqlite/              SQLite persistence layer
  schemas/                          Pydantic API models
  services/                         Copilot, draft, and knowledge services
knowledge_base/                     Policy and FAQ source documents
data/support.db                    Local SQLite database
data/chroma_rag/                   Persistent ChromaDB files
docs/                               Architecture, project, and deployment notes
experiment.ipynb                    Exploratory agent/memory notebook
```

## Data and safety notes

- `data/support.db` and `data/chroma_rag/` are local persistent application data.
- The current memory store is `LangGraph InMemoryStore`, so memories are lost when the process/container restarts.
- There is no authentication or authorization layer in the API; deploy behind appropriate access controls.
- AI output is a recommendation only. The UI explicitly requires adjuster review before resolution.
- The copilot is instructed to avoid autonomous denial language and to recommend pending documents when facts are incomplete.

## Further documentation

- [Project master documentation](docs/Project_Master_Documentation.md)
- [EC2 deployment flow](docs/EC2_deployment_flow.md)
- [Project report](docs/Customer_Support_Agent_Project_Report.md)
- [Assignments and quizzes](docs/Assignments_and_Quizzes_Customer_Support_Agent.md)
