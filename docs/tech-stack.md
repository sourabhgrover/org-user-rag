# Tech Stack — Org User RAG

## Overview

This project uses **Python + FastAPI** as the backend API framework, **MongoDB** as the primary database, **Pinecone** as the vector database, and **OpenAI** for embeddings and language model inference. **LangChain** is used as an orchestration library for document processing and vector store interaction.

---

## Core Technologies

### FastAPI
- **What**: Modern async Python web framework
- **Version used**: Latest stable at time of build
- **Why chosen**:
  - Native `async/await` support — essential for concurrent MongoDB + OpenAI API calls without blocking
  - Automatic **Swagger/OpenAPI docs** generated from code (`/docs` endpoint)
  - First-class **Pydantic integration** for request/response validation
  - Built-in **Dependency Injection** via `Depends()` — used for auth, DB sessions, current user
  - Type hints drive both validation and documentation
- **Alternatives considered**: Flask (no native async), Django (too heavy, ORM-centric)

---

### MongoDB (via PyMongo Async)
- **What**: NoSQL document database
- **Driver**: `pymongo>=4.5.0` — uses `AsyncMongoClient` for non-blocking I/O
- **Collections used**:
  | Collection | Purpose |
  |---|---|
  | `users` | User profiles, hashed passwords, org membership |
  | `organizations` | Organization records |
  | `documents` | PDF metadata (path, name, upload time) |
- **Why chosen**:
  - Flexible document model suits metadata storage
  - Native Python async client available
  - Pydantic serialization maps cleanly to/from BSON documents
  - Well-suited for the hierarchical org → users → documents data model
- **Key pattern**: `ObjectId` fields converted to strings using `PyObjectId = Annotated[str, BeforeValidator(str)]`

---

### Pinecone
- **What**: Managed vector database (serverless)
- **Library**: `pinecone-client` + `langchain-pinecone`
- **Index configuration**: `dimension=1536, metric=cosine, ServerlessSpec(cloud="aws", region="us-east-1")`
- **Why chosen**:
  - Purpose-built for ANN (Approximate Nearest Neighbor) similarity search
  - Supports **metadata filtering** — essential for multi-tenant org isolation
  - Serverless tier: scales to zero, no infrastructure management
  - Direct LangChain integration via `PineconeVectorStore`
- **How used**: Each PDF chunk is stored as a vector with metadata `{organization_id, document_id, chunk_index}`. All searches are filtered by `organization_id`
- **Alternatives**: MongoDB Atlas Vector Search, pgvector (PostgreSQL), ChromaDB (local)

---

### OpenAI
- **What**: AI API for embeddings and chat completions
- **Library**: `langchain-openai`
- **Models used**:
  | Model | Purpose | Dimension/Config |
  |---|---|---|
  | `text-embedding-ada-002` | Text → vector embeddings | 1536 dimensions |
  | `gpt-3.5-turbo` | Answer generation from context | temperature=0.1 |
- **Why `text-embedding-ada-002`**: Standard embedding model with high quality semantic representations, 8191 token context, cost-effective
- **Why `gpt-3.5-turbo`**: Sufficient for reading + synthesizing provided context. Lower cost than GPT-4. `temperature=0.1` keeps answers deterministic and factual
- **Why `temperature=0.1`**: Closer to 0 = more deterministic output. For RAG, you want the model to closely follow the provided context rather than being creative

---

### LangChain
- **What**: Python orchestration library for LLM applications
- **Libraries**: `langchain`, `langchain-openai`, `langchain-pinecone`
- **What it's used for in this project**:
  | Feature | LangChain Component |
  |---|---|
  | PDF text splitting | `RecursiveCharacterTextSplitter` |
  | Vector store abstraction | `PineconeVectorStore` |
  | Embedding generation | `OpenAIEmbeddings` |
  | LLM chat interface | `ChatOpenAI` |
- **Key benefit**: `PineconeVectorStore.add_texts()` handles embed → upsert in one call. `similarity_search_with_score()` handles embed → search in one call
- **Note**: LangChain is only used for its utilities — no chains, agents, or memory abstractions are used

---

### PyPDF2
- **What**: Python PDF reading library
- **Why**: Simple, dependency-light library to extract text from PDFs page by page
- **How used**: `PdfReader(file)` → iterate `pdf_reader.pages` → `page.extract_text()`
- **Limitation**: Doesn't handle scanned PDFs (images) — those require OCR. Only works on PDF files with embedded text

---

### Python-Jose (JWT)
- **What**: Python library for JSON Web Tokens
- **Algorithm**: `HS256` (HMAC-SHA256 symmetric signing)
- **Token payload**: `{sub, user_id, is_admin, exp}`
- **Expiry**: 30 minutes
- **Why this approach**: Stateless auth — server doesn't need to store sessions. The JWT is self-contained and cryptographically verified on every request

---

### Passlib + bcrypt
- **What**: Password hashing library with bcrypt backend
- **Configuration**: `CryptContext(schemes=["bcrypt"], deprecated="auto")`
- **Why bcrypt**: Intentionally slow (tunable work factor), salted, industry standard for password storage. Resistant to rainbow tables and GPU brute-force attacks
- **Usage**: `get_password_hash(plain)` at creation, `verify(plain, hashed)` at login

---

### Pydantic v2
- **What**: Data validation library for Python
- **Library**: `pydantic[email]`, `pydantic-settings`
- **Key usages**:
  | Feature | How used |
  |---|---|
  | Request validation | All API request bodies are Pydantic models |
  | Response serialization | `response_model=` strips unwanted fields (e.g., `hashed_password`) |
  | Config management | `BaseSettings` loads `.env` into typed `Settings` class |
  | Generic responses | `StandardResponse[T]` — generic envelope preserving type info |
  | Custom types | `PyObjectId` converts MongoDB `ObjectId` to string automatically |
  | Field exclusion | `Field(exclude=True)` on `hashed_password` — never in API output |

---

### Python-Multipart
- **What**: Enables FastAPI to parse `multipart/form-data` (file uploads)
- **Why needed**: FastAPI's `UploadFile` and `File(...)` require this package to handle binary file data in HTTP requests

---

## Full Dependency List (`requirements.txt`)

```
fastapi              # Web framework
uvicorn              # ASGI server to run FastAPI
pymongo>=4.5.0       # MongoDB async driver
pydantic-settings    # .env → typed Settings class
pydantic[email]      # Pydantic with email validation (EmailStr)
passlib[bcrypt]      # Password hashing
python-multipart     # Multipart form data / file uploads
python-jose[cryptography]  # JWT creation and verification

PyPDF2               # PDF text extraction
langchain            # Text splitting, abstractions
langchain-openai     # OpenAI embeddings + ChatOpenAI
langchain-pinecone   # LangChain ↔ Pinecone integration
pinecone-client      # Pinecone vector DB SDK
```

---

## Infrastructure Diagram

```
Client (React / Postman)
         │  HTTPS
         ▼
  ┌─────────────────┐
  │   FastAPI App   │  uvicorn (ASGI server)
  │   main.py       │
  └──────┬──────────┘
         │
    ┌────┴──────────────────────────┐
    │                               │
    ▼                               ▼
┌─────────────┐             ┌───────────────────┐
│  MongoDB    │             │   External APIs    │
│  Atlas      │             │                   │
│             │             │  ┌─────────────┐  │
│ - users     │             │  │   OpenAI    │  │
│ - orgs      │             │  │  Embeddings │  │
│ - documents │             │  │  + GPT-3.5  │  │
└─────────────┘             │  └─────────────┘  │
                            │                   │
                            │  ┌─────────────┐  │
                            │  │  Pinecone   │  │
                            │  │  Serverless │  │
                            │  │  Vector DB  │  │
                            │  └─────────────┘  │
                            └───────────────────┘
```

---

## Environment Variables Required

| Variable | Description | Example |
|---|---|---|
| `MONGO_URI` | MongoDB connection string | `mongodb+srv://user:pass@cluster.mongodb.net` |
| `MONGO_DB_NAME` | Name of the MongoDB database | `org_rag` |
| `SECRET_KEY` | Secret for signing JWTs | Random 32-byte hex string |
| `OPENAI_API_KEY` | OpenAI API key | `sk-...` |
| `PINECONE_API_KEY` | Pinecone API key | From Pinecone console |
| `PINECONE_ENVIRONMENT` | Pinecone environment | `us-east-1` |
| `PINECONE_INDEX_NAME` | Name of the Pinecone index to use/create | `org-rag-index` |

---

## Key Version Considerations

| Concern | Detail |
|---|---|
| PyMongo async | Requires `pymongo>=4.5.0` — earlier versions lack `AsyncMongoClient` |
| Pydantic v2 | Uses `model_dump()` not `.dict()`, `model_config` not inner `Config` class |
| LangChain packages | Split across `langchain`, `langchain-openai`, `langchain-pinecone` — these are separate packages in modern LangChain |
| Pinecone SDK | Uses new-style `Pinecone(api_key=...)` constructor, not legacy `pinecone.init()` |
