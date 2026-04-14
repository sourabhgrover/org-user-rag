# Org User RAG — Complete Codebase Guide

## What This Project Is

A **multi-tenant RAG (Retrieval Augmented Generation) REST API** where:
- Organizations can be created, each with isolated data
- Each organization's users can upload PDF documents
- Users can semantically **search** those documents
- Users can **ask natural language questions** and get AI-generated answers grounded in the uploaded documents

---

## Project Structure

```
org-user-rag/
├── app/
│   ├── main.py                    # FastAPI app, middleware, lifespan, routers
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   ├── auth.py        # POST /token — Login & JWT issue
│   │       │   ├── user.py        # CRUD for users (org-scoped)
│   │       │   ├── organization.py# CRUD for organizations
│   │       │   ├── doc.py         # Upload PDFs, list docs
│   │       │   ├── search.py      # Semantic search endpoint
│   │       │   └── qa.py          # Ask a question (full RAG)
│   │       └── models/
│   │           ├── user.py        # UserBase, UserCreate, UserInDB, UserResponse, UserUpdate
│   │           ├── organization.py# OrganizationCreate, OrganizationInDB, etc.
│   │           ├── doc.py         # DocBase, DocOutput
│   │           ├── auth.py        # UserLogin, AuthResponse
│   │           ├── token.py       # Token, TokenData
│   │           ├── qa.py          # QARequest, QAResponse, ContextSource
│   │           ├── search.py      # SearchRequest, SearchResponse, SearchResult
│   │           └── response.py    # StandardResponse[T], DeleteResponse
│   ├── core/
│   │   ├── config.py              # Pydantic settings — loads .env
│   │   ├── security.py            # bcrypt hashing + JWT create/decode
│   │   ├── dependencies.py        # FastAPI auth dependency chain (3 layers)
│   │   ├── vector_store.py        # Pinecone init, index creation, VectorStoreManager
│   │   └── llm.py                 # OpenAI GPT-3.5-turbo init, LLMManager
│   ├── crud/
│   │   ├── user.py                # MongoDB async user operations
│   │   ├── organization.py        # MongoDB async org operations
│   │   └── doc.py                 # File save + MongoDB doc metadata ops
│   ├── db/
│   │   └── mongodb.py             # AsyncMongoClient, connect/close, get_database()
│   └── services/
│       ├── document_service.py    # Orchestrates the full PDF → Pinecone pipeline
│       ├── pdf_service.py         # PyPDF2: extract text from PDF file
│       ├── chunking_service.py    # LangChain: split text into chunks with metadata
│       ├── vector_service.py      # LangChain + Pinecone: store chunks
│       ├── search_service.py      # Pinecone similarity search with org filter
│       ├── qa_service.py          # Search + GPT-3.5-turbo prompt → answer
│       └── rag_service.py         # (Legacy) original monolithic pipeline — superseded
├── uploaded_files/                # PDF files stored on disk after upload
├── requirements.txt
└── .env                           # Secret keys and API credentials (not in git)
```

---

## Architecture: How Everything Connects

```
HTTP Request
     │
     ▼
┌─────────────────────────────────┐
│  FastAPI  (app/main.py)         │
│  - CORS Middleware               │
│  - Global Exception Handlers     │
│    (PyMongoError → 500,          │
│     Exception → 500)             │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  API Endpoints (/api/v1/...)    │
│  auth.py → /token               │
│  user.py → /user                │
│  org.py  → /organization        │
│  doc.py  → /doc                 │
│  search.py → /search            │
│  qa.py   → /qa/ask              │
└──────┬──────────────┬───────────┘
       │              │
       ▼              ▼
┌────────────┐  ┌──────────────────┐
│ Auth Layer │  │  CRUD Layer       │
│            │  │  (MongoDB ops)    │
│ HTTPBearer │  │  crud/user.py     │
│     ↓      │  │  crud/org.py      │
│ JWT decode │  │  crud/doc.py      │
│     ↓      │  └──────────┬───────┘
│ TokenData  │             │
│     ↓      │             ▼
│get_active_ │  ┌──────────────────┐
│   user     │  │  MongoDB Atlas   │
│ (DB hit)   │  │  - users         │
│     ↓      │  │  - organizations │
│get_admin_  │  │  - documents     │
│   user     │  └──────────────────┘
│ (no DB)    │
└────────────┘
       │
       ▼
┌──────────────────────────────────────────┐
│  Services Layer (Business Logic)          │
│                                           │
│  document_service.process_documents()     │
│    → pdf_service (PyPDF2)                 │
│    → chunking_service (LangChain splitter)│
│    → vector_service (Pinecone upsert)     │
│                                           │
│  search_service.search_documents()        │
│    → Pinecone similarity_search           │
│      filtered by organization_id          │
│                                           │
│  qa_service.answer_question()             │
│    → search_service (get context)         │
│    → llm_manager.get_llm().invoke(prompt) │
└──────────┬──────────────────┬────────────┘
           │                  │
           ▼                  ▼
    ┌──────────────┐   ┌─────────────┐
    │   Pinecone   │   │  OpenAI API │
    │  Vector DB   │   │  Embeddings │
    │  (1536-dim,  │   │  + GPT-3.5  │
    │   cosine)    │   │   -turbo    │
    └──────────────┘   └─────────────┘
```

---

## Step-by-Step Data Flows

### Flow 1: Application Startup

```
uvicorn app.main:app
  │
  ├── lifespan() starts
  │     ├── connect_to_mongo() — creates AsyncMongoClient
  │     └── (implicit) VectorStoreManager() module loads
  │           ├── OpenAIEmbeddings("text-embedding-ada-002")
  │           ├── Pinecone(api_key=...)
  │           ├── _ensure_index_exists()
  │           │     └── create_index(dim=1536, metric=cosine) if not exists
  │           └── PineconeVectorStore(index, embeddings)
  │
  └── LLMManager() module loads
        └── ChatOpenAI(model="gpt-3.5-turbo", temperature=0.1)
```

### Flow 2: Create Organization

```
POST /api/v1/organization/
  │
  ├── crud/organization.create_organization()
  │     ├── Check name uniqueness in MongoDB
  │     ├── insert_one → organizations collection
  │     └── create_default_admin_user()
  │           └── Creates an admin user automatically for this org
  │
  └── Returns StandardResponse[OrganizationResponse]
```

### Flow 3: Login

```
POST /api/v1/token   { username, password }
  │
  ├── crud/user.get_user_by_username(db, username)  → MongoDB query
  ├── security.verify_password(plain, hashed)       → bcrypt compare
  ├── security.create_access_token({
  │     "sub": username,
  │     "user_id": str(user._id),
  │     "is_admin": user.is_admin
  │   }, expires=30min)
  │
  └── Returns StandardResponse[AuthResponse]  { user, token }
```

### Flow 4: Upload PDF (triggers RAG indexing)

```
POST /api/v1/doc/   multipart files
  │
  ├── [Auth] get_current_active_user → JWT validate + MongoDB fetch
  │
  ├── For each file:
  │     ├── Validate content_type == "application/pdf"
  │     ├── Save to disk: uploaded_files/{orgId}_{timestamp}_{filename}
  │     └── Insert metadata into MongoDB documents collection
  │
  ├── db.documents.insert_many([...])
  │
  └── For each saved file → document_service.process_documents(path, doc_id, org_id)
        │
        ├── pdf_service.extract_text_from_pdf(path)
        │     └── PyPDF2.PdfReader → iterates pages
        │           → "--- Page N ---\n" + page.extract_text()
        │
        ├── chunking_service.extract_text_into_chunks(text, doc_id, org_id)
        │     └── RecursiveCharacterTextSplitter(
        │               chunk_size=1000,
        │               chunk_overlap=200,
        │               separators=["\n\n", "\n", ". ", " ", ""]
        │           )
        │     └── Each chunk → {
        │               id: "{doc_id}_chunk_{i}",
        │               text: "...",
        │               metadata: {
        │                   organization_id, document_id,
        │                   chunk_index, chunk_length
        │               }
        │           }
        │
        └── vector_service.store_chunks_in_pinecone(chunks)
              └── vector_store.add_texts(texts, metadatas)
                    ├── LangChain calls OpenAI Embeddings API
                    │     → 1536-dim vector per chunk
                    └── Upserts vectors into Pinecone index
```

### Flow 5: Semantic Search

```
POST /api/v1/search/   { query, document_id?, top_k }
  │
  ├── [Auth] get_current_active_user
  │
  └── search_service.search_documents(query, org_id, doc_id, top_k)
        ├── Build filter: {"organization_id": org_id}
        │                 + {"document_id": doc_id}  if provided
        │
        ├── vector_store.similarity_search_with_score(
        │     query=query, k=top_k, filter=filter_dict
        │   )
        │   └── LangChain embeds query via OpenAI → vector
        │       → Pinecone cosine similarity search → top-k results
        │
        └── For each (doc, score):
              relevance = "High" if score < 0.3
                          "Medium" if score < 0.6
                          "Low" otherwise
              → { text, score, relevance, metadata }
```

### Flow 6: Ask a Question (Full RAG)

```
POST /api/v1/qa/ask   { question, document_id?, max_context_chunks }
  │
  ├── [Auth] get_current_active_user
  │
  └── qa_service.answer_question(question, org_id, doc_id, max_chunks)
        │
        ├── [RETRIEVE] search_service.search_documents(question, ...)
        │     └── Returns top-k relevant chunks from Pinecone
        │
        ├── [AUGMENT] Build prompt:
        │     """
        │     You are a helpful AI assistant...
        │     Context Information:
        │       Context 1: <chunk text>
        │       Context 2: <chunk text>
        │       ...
        │     Question: <user question>
        │     Instructions: Answer based ONLY on provided context...
        │     Answer:
        │     """
        │
        ├── [GENERATE] llm_manager.get_llm().invoke(prompt)
        │     └── GPT-3.5-turbo API call → response.content
        │
        ├── Confidence:
        │     avg_score = average of cosine scores
        │     "High"   if avg_score < 0.3
        │     "Medium" if avg_score < 0.6
        │     "Low"    otherwise
        │
        └── Returns StandardResponse[QAResponse] {
                answer, confidence, context_sources,
                total_sources, response_time_ms
              }
```

---

## File-by-File Explanation

### `app/main.py`
The entry point. Creates the FastAPI app and wires everything together.

```python
# Lifespan: replaces deprecated @app.on_event
@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()   # startup
    yield
    await close_mongo_connection()  # shutdown
```

- Registers **CORS** for `localhost:5173` (React dev) and a Netlify frontend
- Two global exception handlers intercept unhandled `PyMongoError` and `Exception` and return clean HTTP 500 responses instead of stack traces

---

### `app/core/config.py`
Uses `pydantic-settings` to load and validate all environment variables from `.env`.

```python
class Settings(BaseSettings):
    MONGO_URI: str          # required — no default
    OPENAI_API_KEY: str     # required
    PINECONE_API_KEY: str   # required
    SECRET_KEY: str = "..."  # has default (change in prod!)
    ...
    model_config = SettingsConfigDict(env_file=".env", extra='ignore')

settings = Settings()  # fails fast if required vars missing
```

---

### `app/db/mongodb.py`
Simple connection manager using PyMongo's native async client.

```python
client: Optional[AsyncMongoClient] = None
database: Optional[AsyncDatabase] = None

async def get_database() -> AsyncDatabase:  # FastAPI Depends()
    if database is None:
        raise ConnectionError(...)
    return database
```

`get_database` is a **FastAPI dependency** — injected via `Depends(get_database)` in any endpoint that needs MongoDB.

---

### `app/core/security.py`
Two responsibilities: password hashing and JWT tokens.

```python
# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"])
get_password_hash(password)     # bcrypt hash
verify_password(plain, hashed)  # constant-time compare

# JWT
create_access_token(data, expires_delta)  # HS256 signed
decode_access_token(token)                # returns payload or None
```

---

### `app/core/dependencies.py`
Three-level dependency chain for authentication and authorization:

| Function | What it does | DB hit? |
|---|---|---|
| `get_current_user_from_token` | Validates JWT via `HTTPBearer`, returns `TokenData` | No |
| `get_current_active_user` | Fetches full `UserInDB` from MongoDB by `user_id` | Yes |
| `get_current_admin_user` | Checks `is_admin` flag from JWT | No |

Usage in endpoints:
```python
# Just needs valid token (fast):
router = APIRouter(dependencies=[Depends(get_current_active_user)])

# Needs admin, no DB:
@router.post("/", dependencies=[Depends(get_current_admin_user)])

# Needs full user object:
current_user: UserInDB = Depends(get_current_active_user)
```

---

### `app/core/vector_store.py`
Singleton that manages the Pinecone connection. Initialized once at module import.

```python
class VectorStoreManager:
    def _initialize(self):
        self.embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")
        self.pinecone_client = Pinecone(api_key=...)
        self._ensure_index_exists()  # creates index if missing
        pinecone_index = self.pinecone_client.Index(INDEX_NAME)
        self.vector_store = PineconeVectorStore(index=pinecone_index, embedding=self.embeddings)

vector_store_manager = VectorStoreManager()  # module-level singleton
```

Index config: `dimension=1536, metric="cosine", ServerlessSpec(cloud="aws", region="us-east-1")`

---

### `app/core/llm.py`
Singleton for GPT-3.5-turbo.

```python
class LLMManager:
    def _initialize(self):
        self.llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.1)
        #  temperature=0.1 → deterministic, factual answers

llm_manager = LLMManager()
```

---

### Pydantic Models (`app/api/v1/models/`)

**User model hierarchy:**
```
UserBase
  ├── first_name, last_name, email, username
  ├── gender: GenderEnum (Male/Female/Other)
  ├── dob: date
  └── is_admin: bool = False

UserCreate(UserBase)
  └── +password (min 8, max 128 chars)

UserInDB(UserBase)
  ├── id: PyObjectId (alias="_id")
  ├── organization_id: PyObjectId
  ├── hashed_password: str (exclude=True → never in responses)
  └── created_at, updated_at: Optional[datetime]

UserResponse(UserInDB)  → identical to UserInDB, hashed_password excluded by inherit

UserUpdate(BaseModel)   → all UserBase fields but Optional
```

**`PyObjectId`:** `Annotated[str, BeforeValidator(str)]` — converts MongoDB `ObjectId` to string automatically when Pydantic validates it.

**`StandardResponse[T]`:** Generic envelope used by every endpoint:
```python
class StandardResponse(BaseModel, Generic[T]):
    status: str
    message: str
    data: Optional[T] = None
```

---

### `app/crud/user.py`
All async MongoDB operations for users:
- `create_user`: checks duplicate email/username, validates org exists, hashes password, stores `dob` as datetime (MongoDB requirement), sets timestamps
- `get_user_by_username` / `get_user_by_id`: simple find_one queries
- `get_all_user`: supports pagination (`skip`/`limit`) and `search_name` via `$regex`
- `update_user_by_id`: partial update via `$set` with only provided fields
- `delete_user_by_id`: scoped by `organization_id` for safety

---

### `app/crud/organization.py`
- `create_organization`: checks name uniqueness, inserts, calls `create_default_admin_user()` to bootstrap an admin for the new org
- `get_organizations`: supports pagination + case-insensitive `$regex` name search
- `update_organization`: checks new name uniqueness before updating

---

### `app/crud/doc.py`
File upload + Mongo metadata:
1. Validates each file is `application/pdf`
2. Saves to `uploaded_files/{orgId}_{timestamp}_{filename}` (prevents name collisions)
3. `insert_many()` for all doc metadata in one DB call
4. Calls `document_service.process_documents()` per file to trigger RAG indexing

---

### Services Layer (`app/services/`)

**`pdf_service.py`** — pure function, no dependencies:
```python
def extract_text_from_pdf(file_path) -> str:
    # PyPDF2.PdfReader → iterates pages
    # adds "--- Page N ---" markers between pages
```

**`chunking_service.py`** — pure function:
```python
def extract_text_into_chunks(text, doc_id, org_id):
    # RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    # returns list of {id, text, metadata} dicts
```

**`vector_service.py`** — calls Pinecone:
```python
def store_chunks_in_pinecone(chunks):
    vector_store.add_texts(texts, metadatas)
    # LangChain handles: texts → OpenAI embeddings → Pinecone upsert
```

**`search_service.py`** — queries Pinecone:
```python
def search_documents(query, org_id, doc_id=None, top_k=5):
    filter_dict = {"organization_id": org_id}
    if doc_id: filter_dict["document_id"] = doc_id
    results = vector_store.similarity_search_with_score(query, k=top_k, filter=filter_dict)
```

**`qa_service.py`** — orchestrates RAG:
```python
def answer_question(question, org_id, doc_id, max_chunks):
    context_results = search_documents(question, org_id, doc_id, max_chunks)
    prompt = template.format(context=context_string, question=question)
    response = llm.invoke(prompt)
    return { answer, confidence, context_sources }
```

**`document_service.py`** — pipeline orchestrator:
```python
def process_documents(file_path, document_id, organization_id):
    text = extract_text_from_pdf(file_path)
    chunks = extract_text_into_chunks(text, document_id, organization_id)
    success = store_chunks_in_pinecone(chunks)
```

---

## Multi-Tenancy: How Data Isolation Works

Every piece of data carries `organization_id`:

| Layer | How org isolation is enforced |
|---|---|
| MongoDB `users` | `organization_id` field, all queries filter by it |
| MongoDB `documents` | `organizationId` field, list endpoint filters by it |
| Pinecone vectors | `organization_id` in metadata of every chunk |
| Search/QA | `filter={"organization_id": current_user.organization_id}` |
| Token | `organization_id` stored in DB; every request uses it from validated `UserInDB` |

A user's `organization_id` comes from the database record fetched via JWT — users cannot inject a different org ID.

---

## Key Design Decisions

| Decision | Why |
|---|---|
| `HTTPBearer` not `OAuth2PasswordBearer` | Login accepts JSON body, not OAuth2 form data |
| Admin check from JWT, no DB | Performance — avoid DB round-trip for every admin endpoint |
| `is_admin` + `user_id` in JWT payload | Reduces DB calls; 30-min expiry limits risk of stale data |
| `RecursiveCharacterTextSplitter` | Respects semantic boundaries (\n\n, \n, .) before hard splits |
| `chunk_overlap=200` | Prevents answers being split across chunk boundaries |
| `temperature=0.1` for LLM | Deterministic, factual responses — reduces hallucination |
| Singleton pattern for VectorStore/LLM | Avoid reconnecting on every request |
| Generic `StandardResponse[T]` | Consistent API envelope; Swagger generates correct schemas |

---

## Known Issues / What Could Be Improved

1. **Document processing is synchronous** — uploading 100-page PDFs blocks the HTTP response. Should use FastAPI `BackgroundTasks` or a proper queue (Celery, Redis Queue)
2. **`rag_service.py` is dead code** — superseded by the service modules but never deleted. It also re-initializes Pinecone at module load time
3. **No document deletion** — documents in MongoDB and their Pinecone vectors have no delete endpoint
4. **Password update not implemented** in `UserUpdate`
5. **`setup_indexes.py` is empty** — looks like it was intended to pre-create MongoDB indexes for performance but never completed; for production, indexes on `users.email`, `users.username`, `documents.organizationId` would improve query speed
