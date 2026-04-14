# Org User RAG

A **multi-tenant RAG (Retrieval Augmented Generation) REST API** built with FastAPI, MongoDB, Pinecone, and OpenAI. Organizations can upload PDF documents and their users can semantically search them or ask natural language questions — receiving AI-generated answers grounded in the organization's own documents.

---

## Features

- **Multi-tenant isolation** — Every user, document, and vector is scoped to an organization. Users from one org can never access another org's data
- **JWT Authentication** — Secure login with bcrypt-hashed passwords and signed JWT tokens (30-min expiry)
- **Role-based access** — Admin-only endpoints for user management; admin status embedded in JWT for fast checks
- **PDF Upload & Indexing** — Upload multiple PDFs; text is extracted, chunked, embedded (OpenAI), and stored in Pinecone automatically
- **Semantic Search** — Search documents by meaning, not just keywords, filtered by organization (and optionally by document)
- **AI Q&A (RAG)** — Ask a natural language question; the API retrieves relevant context from Pinecone and generates an answer via GPT-3.5-turbo
- **Consistent API responses** — All endpoints return a `StandardResponse[T]` envelope: `{status, message, data}`

---

## Tech Stack

| Layer | Technology |
|---|---|
| API Framework | FastAPI + Uvicorn |
| Primary Database | MongoDB (async via PyMongo 4.5+) |
| Vector Database | Pinecone (serverless, cosine similarity) |
| Embeddings | OpenAI `text-embedding-ada-002` (1536 dim) |
| LLM | OpenAI `gpt-3.5-turbo` |
| RAG Orchestration | LangChain |
| PDF Parsing | PyPDF2 |
| Authentication | JWT (python-jose, HS256) + bcrypt (passlib) |
| Data Validation | Pydantic v2 + pydantic-settings |

---

## Project Structure

```
app/
├── main.py                    # FastAPI app, CORS, lifespan, global error handlers
├── api/v1/
│   ├── endpoints/             # Route handlers (auth, user, org, doc, search, qa)
│   └── models/                # Pydantic request/response models
├── core/
│   ├── config.py              # Settings loaded from .env via pydantic-settings
│   ├── security.py            # bcrypt hashing + JWT sign/verify
│   ├── dependencies.py        # FastAPI auth dependency chain (3 layers)
│   ├── vector_store.py        # Pinecone init & VectorStoreManager singleton
│   └── llm.py                 # LLMManager singleton (GPT-3.5-turbo)
├── crud/                      # Async MongoDB operations
├── db/mongodb.py              # AsyncMongoClient connection manager
└── services/                  # Business logic
    ├── document_service.py    # Pipeline orchestrator
    ├── pdf_service.py         # PDF text extraction (PyPDF2)
    ├── chunking_service.py    # Text splitting (LangChain)
    ├── vector_service.py      # Pinecone upsert via LangChain
    ├── search_service.py      # Similarity search with org filter
    └── qa_service.py          # Retrieve context + GPT answer generation
uploaded_files/                # Uploaded PDFs stored on disk
docs/
├── codebase-guide.md          # Full architecture, data flows, file-by-file guide
├── interview-qa.md            # 35+ interview Q&As covering the full stack
└── tech-stack.md              # Tech stack details and dependency reference
```

---

## Setup

### Prerequisites
- Python 3.10+
- MongoDB Atlas cluster (or local MongoDB)
- Pinecone account (free tier works)
- OpenAI API key

### 1. Clone & install dependencies

```bash
git clone https://github.com/your-username/org-user-rag.git
cd org-user-rag
pip install -r requirements.txt
```

### 2. Create `.env` file

```env
MONGO_URI=mongodb+srv://<user>:<password>@cluster.mongodb.net
MONGO_DB_NAME=org_rag
SECRET_KEY=<random-32-byte-hex-string>
OPENAI_API_KEY=sk-...
PINECONE_API_KEY=<your-pinecone-key>
PINECONE_ENVIRONMENT=us-east-1
PINECONE_INDEX_NAME=org-rag-index
```

Generate a secure `SECRET_KEY`:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 3. Run the server

```bash
uvicorn app.main:app --reload
```

### 4. Open API docs

```
http://localhost:8000/docs
```

---

## API Endpoints

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/api/v1/token` | None | Login — returns JWT token |
| `POST` | `/api/v1/organization/` | None | Create a new organization (auto-creates admin user) |
| `GET` | `/api/v1/organization/` | None | List all organizations |
| `GET` | `/api/v1/organization/{id}` | None | Get organization by ID |
| `POST` | `/api/v1/user/` | Admin | Create a user in the current org |
| `GET` | `/api/v1/user/` | User | List users in the current org |
| `GET` | `/api/v1/user/{id}` | User | Get user by ID |
| `PUT` | `/api/v1/user/{id}` | Admin | Update user |
| `DELETE` | `/api/v1/user/{id}` | Admin | Delete user |
| `POST` | `/api/v1/doc/` | User | Upload one or more PDFs (auto-indexes in Pinecone) |
| `GET` | `/api/v1/doc/` | User | List all documents for current org |
| `POST` | `/api/v1/search/` | User | Semantic search across documents |
| `POST` | `/api/v1/qa/ask` | User | Ask a natural language question |

---

## How RAG Works

```
PDF Upload
    │
    ├── Extract text (PyPDF2, page by page)
    ├── Split into chunks (1000 chars, 200 overlap, RecursiveCharacterTextSplitter)
    ├── Embed each chunk (OpenAI text-embedding-ada-002 → 1536-dim vector)
    └── Store vectors in Pinecone with metadata {organization_id, document_id, chunk_index}

Ask a Question
    │
    ├── Embed the question → vector
    ├── Cosine similarity search in Pinecone (filtered by organization_id)
    ├── Retrieve top-k most relevant chunks
    ├── Build prompt: context chunks + question + instructions
    └── GPT-3.5-turbo generates answer → returned with confidence + source contexts
```

---

## Authentication Flow

1. Create an organization → a default admin user is created automatically
2. Login with `POST /api/v1/token` → receive a JWT token
3. Include token in all subsequent requests: `Authorization: Bearer <token>`
4. Token contains `user_id`, `is_admin`, and `exp` — no session storage needed

---

## Documentation

See the `docs/` folder for detailed reference material:

- [docs/codebase-guide.md](docs/codebase-guide.md) — Complete architecture, data flow diagrams, and file-by-file explanation
- [docs/interview-qa.md](docs/interview-qa.md) — 35+ interview questions and answers covering RAG, FastAPI, auth, and databases
- [docs/tech-stack.md](docs/tech-stack.md) — Tech stack rationale and dependency reference

