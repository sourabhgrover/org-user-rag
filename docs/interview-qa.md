# Interview Q&A — Org User RAG Project

---

## SECTION 1: Project Overview

**Q: In one sentence, what does this project do?**

> It is a multi-tenant REST API where organizations upload PDF documents and their users can semantically search or ask natural language questions, getting AI-generated answers grounded only in that organization's documents.

---

**Q: What problem does RAG solve that plain GPT doesn't?**

> GPT is trained on public internet data with a knowledge cutoff. If you ask it about your company's internal documents, it either doesn't know or will hallucinate. RAG solves this by first **retrieving** relevant chunks from your own documents and injecting them into the prompt as context — the LLM then synthesizes an answer from that specific, factual context rather than from training data.

---

**Q: Walk me through the high-level flow when a user asks a question.**

> 1. The user sends a POST to `/qa/ask` with their question and a JWT token
> 2. The token is validated and used to identify their organization
> 3. The question is **embedded** into a 1536-dim vector using OpenAI `text-embedding-ada-002`
> 4. Pinecone performs a **cosine similarity search** filtered to that organization's vectors and returns the top-k most relevant text chunks
> 5. Those chunks are injected into a **prompt template** along with the original question
> 6. GPT-3.5-turbo is called via LangChain and generates a grounded answer
> 7. A confidence score is derived from the average cosine distance and returned with the answer and source contexts

---

## SECTION 2: RAG & AI Concepts

**Q: What is RAG? Explain the three stages.**

> RAG stands for Retrieval Augmented Generation. Three stages:
> - **Indexing (offline):** Documents are split into chunks, each chunk is converted to an embedding (vector), and stored in a vector database with metadata
> - **Retrieval (online):** The user's query is embedded and a similarity search finds the most relevant chunks
> - **Generation:** The retrieved chunks are passed as context to an LLM with the user's question, and the LLM generates an answer based solely on that context

---

**Q: What is an embedding and why do we use them?**

> An embedding is a dense vector representation of text that captures semantic meaning. Similar semantic content produces vectors that are close together in high-dimensional space. We use them because you can't directly compare strings for meaning — but with embeddings you can do cosine similarity search across millions of documents in milliseconds using a vector database.

---

**Q: Why did you choose `text-embedding-ada-002`?**

> It was the standard OpenAI embedding model at the time of development — it produces high-quality 1536-dimensional embeddings and is cost-effective. It handles up to 8191 tokens and performs well for semantic similarity use cases like retrieval.

---

**Q: What is cosine similarity and why use it over Euclidean distance?**

> Cosine similarity measures the angle between two vectors regardless of their magnitude — it captures *directional* similarity. For text embeddings, the direction encodes meaning while magnitude can vary based on text length. Cosine is preferred for semantic search because two texts can be semantically similar even if they're of very different lengths.

---

**Q: What is `RecursiveCharacterTextSplitter` and why did you use it?**

> It's a LangChain text splitter that recursively tries to split text using a list of separators in priority order: `["\n\n", "\n", ". ", " ", ""]`. It first tries to break on paragraph boundaries, then sentences, then words, then characters — so it preserves semantic coherence as much as possible. The alternative, `CharacterTextSplitter`, just cuts strictly at character count which can break mid-sentence.

---

**Q: What are `chunk_size` and `chunk_overlap`? What values did you use and why?**

> - `chunk_size=1000`: Each chunk is at most 1000 characters. This fits well within the embedding model's token limit while providing enough context per chunk
> - `chunk_overlap=200`: Consecutive chunks share 200 characters of content. This ensures that if a key fact spans a chunk boundary, it still appears in at least one complete chunk and isn't lost during retrieval

---

**Q: How does multi-tenancy work in your vector database?**

> Every text chunk stored in Pinecone has `organization_id` in its metadata. Every similarity search includes `filter={"organization_id": current_user.organization_id}`. Since Pinecone supports metadata filtering, vectors from different organizations are stored in the same index but are always queried in isolation. The org ID comes from the server-verified JWT token, so it cannot be spoofed.

---

**Q: How do you determine confidence level of an answer?**

> After retrieving context chunks from Pinecone, I average their cosine similarity scores. A lower cosine distance means the chunks are more semantically close to the question. I map it as:
> - Average score `< 0.3` → **High** confidence
> - Average score `< 0.6` → **Medium** confidence
> - Otherwise → **Low** confidence

---

## SECTION 3: FastAPI & Python

**Q: Why FastAPI over Flask or Django?**

> FastAPI offers native async/await support (critical for concurrent DB and API calls), automatic Swagger/OpenAPI docs generation, built-in request validation via Pydantic, and type-hint-based dependency injection — all with performance close to Node.js/Go. Flask lacks native async and Pydantic integration. Django is much heavier and opinionated toward templated web apps.

---

**Q: What is the lifespan context manager in FastAPI?**

> It's the modern replacement for `@app.on_event("startup")` / `@app.on_event("shutdown")`. Using `@asynccontextmanager`, code before `yield` runs at startup (connect to MongoDB) and code after `yield` runs at shutdown (close connection). The benefit is that startup and shutdown logic live together and share the same scope, and `@app.on_event` is deprecated in newer FastAPI versions.

---

**Q: Explain FastAPI's dependency injection and how you used it.**

> FastAPI's `Depends()` lets you declare function parameters that FastAPI will resolve automatically. You build a chain: 
> 1. `get_database` → returns MongoDB `AsyncDatabase`
> 2. `get_current_user_from_token` → reads and validates JWT, returns `TokenData`
> 3. `get_current_active_user` → uses `TokenData` to fetch full user from DB
> 4. `get_current_admin_user` → checks `is_admin` from `TokenData`
> 
> This lets me add auth to an entire router with a single line: `router = APIRouter(dependencies=[Depends(get_current_active_user)])`, and every endpoint in that router automatically requires authentication.

---

**Q: Why do you use `HTTPBearer` instead of `OAuth2PasswordBearer`?**

> `OAuth2PasswordBearer` is tied to the OAuth2 password flow — it expects credentials as form data (`application/x-www-form-urlencoded`) and requires specifying a `tokenUrl`. My login endpoint accepts a JSON body (`UserLogin` model), which is not standard OAuth2 form data. `HTTPBearer` is a simpler scheme that just tells FastAPI to expect a `Bearer` token in the `Authorization` header without imposing OAuth2 semantics.

---

**Q: What is `StandardResponse[T]` and why is it generic?**

> It's a Pydantic `BaseModel` that wraps every API response in a consistent envelope: `{status, message, data}`. Making it generic with `TypeVar T` means the type of `data` is preserved — `StandardResponse[UserResponse]` tells Pydantic and FastAPI's OpenAPI generation exactly what schema `data` contains. Without generics, you'd lose type information and get a vague `data: object` in Swagger.

---

**Q: How do you do async MongoDB operations in Python?**

> PyMongo 4.5+ ships `AsyncMongoClient`. All collection methods (`find_one`, `insert_one`, `update_one`, `delete_one`) return coroutines that you `await`. For cursors from `find()`, you use `async for doc in cursor` to iterate asynchronously without blocking the event loop. This is critical in FastAPI because a blocking DB call would block all other concurrent requests.

---

**Q: What's the difference between `response_model` and returning a Pydantic model directly?**

> `response_model` tells FastAPI to serialize and validate the return value against that model — it will strip any extra fields and apply `exclude=True` annotations (like for `hashed_password`). Returning a Pydantic model directly won't apply that filtering. Using `response_model` is important for security: `hashed_password` is marked `exclude=True` on `UserInDB`, so it's always stripped from responses even if the CRUD function returns the full object.

---

## SECTION 4: Authentication & Security

**Q: How are passwords stored?**

> Using `passlib` with the `bcrypt` scheme. `CryptContext(schemes=["bcrypt"])` is configured once. `get_password_hash(password)` generates a bcrypt hash (which includes a random salt). `verify_password(plain, hashed)` runs a constant-time comparison. Bcrypt is intentionally slow and salted — resistant to rainbow table and brute-force attacks. The plain password is never stored or logged.

---

**Q: What's in the JWT token payload and why?**

> ```json
> { "sub": "username", "user_id": "mongo_object_id", "is_admin": true, "exp": timestamp }
> ```
> - `sub` is the standard JWT subject claim (the user's identifier for humans)
> - `user_id` avoids a DB lookup whenever we need to scope queries by the user
> - `is_admin` allows admin-check endpoints to skip the DB entirely (the flag was set at login from the database)
> - `exp` enforces the 30-minute expiry

---

**Q: Why is `get_current_admin_user` not hitting the database?**

> The `is_admin` flag is embedded in the JWT at login time. For every subsequent request, we trust the cryptographically signed token: if `is_admin=true`, the user was an admin at the time of login. This avoids a DB round-trip on every admin-endpoint call. The tradeoff is: if someone's admin status is revoked, they retain access until their token expires (30 minutes). For higher security, you'd add a DB check or maintain a token revocation list.

---

**Q: How do you prevent one organization's users from accessing another org's data?**

> Multi-layered:
> 1. The user's `organization_id` is stored in MongoDB, fetched via JWT validation — not user-supplied
> 2. All MongoDB queries include `organization_id` as a filter: `{"email": x, "organization_id": ObjectId(org_id)}`
> 3. Delete also scopes by org: `delete_one({"_id": ..., "organization_id": ...})`
> 4. Pinecone searches always include `filter={"organization_id": org_id}`
> 5. Document listing uses `db.documents.find({"organizationId": org_id})`

---

**Q: What is `PyObjectId` and why do you need it?**

> MongoDB's `_id` field is a BSON `ObjectId` type, not a string. Pydantic doesn't know how to validate or serialize it by default. `PyObjectId = Annotated[str, BeforeValidator(str)]` creates a custom type that runs `str()` on any value before validation — so when MongoDB returns an `ObjectId`, it's automatically converted to a string. The `Field(alias="_id")` maps MongoDB's `_id` to the model's `id` attribute.

---

## SECTION 5: Database & Infrastructure

**Q: Why MongoDB for the primary database?**

> MongoDB's document model fits the data naturally — users, organizations, and document metadata each map cleanly to JSON documents. It's schemaless/flexible for metadata storage, supports async operations natively in Python, and integrates easily with Pydantic's model serialization. For a RAG system, the document metadata (not the document content) is stored in MongoDB while the vector content lives in Pinecone.

---

**Q: Why Pinecone for vectors instead of a traditional database?**

> Pinecone is purpose-built for ANN (Approximate Nearest Neighbor) search at scale. It handles: embedding storage, metadata filtering, serverless auto-scaling, and sub-second similarity search over millions of vectors. Implementing the same with MongoDB or PostgreSQL would require pgvector and manual tuning. Atlas Vector Search is an alternative but Pinecone's standalone serverless offering and LangChain integration made it straightforward.

---

**Q: How is the Pinecone index created automatically?**

> In `VectorStoreManager._ensure_index_exists()`: it calls `pinecone_client.list_indexes()`, checks if `PINECONE_INDEX_NAME` exists. If not, it calls `create_index(name, dimension=1536, metric="cosine", spec=ServerlessSpec(...))` then polls `describe_index().status["ready"]` in a loop until the index is ready before proceeding.

---

**Q: Why `dimension=1536` for the Pinecone index?**

> `text-embedding-ada-002` always produces vectors of exactly 1536 dimensions. The Pinecone index must be created with the same dimension as the embeddings that will be stored in it — they must match exactly or upsert will fail.

---

**Q: How does LangChain's `add_texts()` work under the hood?**

> `PineconeVectorStore.add_texts(texts, metadatas)` internally:
> 1. Calls the configured `OpenAIEmbeddings.embed_documents(texts)` → gets a list of 1536-dim vectors
> 2. Generates unique IDs for each document
> 3. Calls Pinecone's `upsert()` with `[(id, vector, metadata)]` records
>
> It abstracts away the two-step process of "get embeddings, then store vectors" into one method call.

---

## SECTION 6: Architecture & Design Patterns

**Q: What design patterns did you use?**

> - **Singleton pattern**: `vector_store_manager` and `llm_manager` are module-level instances created once at startup — avoids the overhead of reconnecting to OpenAI/Pinecone on every request
> - **Repository/CRUD pattern**: `crud/` layer isolates all database operations; endpoints never query MongoDB directly
> - **Service layer pattern**: Business logic (PDF parsing, chunking, vector storage, QA) lives in `services/` — separate from transport (endpoints) and data access (CRUD)
> - **Dependency injection**: FastAPI's `Depends()` for auth, DB, and current user
> - **Generic response envelope**: `StandardResponse[T]` for consistent API responses

---

**Q: Explain the separation between CRUD, services, and endpoints.**

> - **Endpoints** (`api/v1/endpoints/`): HTTP concerns only — parse request, call CRUD or service, return response. No business logic here
> - **CRUD** (`crud/`): All MongoDB operations. Only knows about the database and Pydantic models. No HTTP concerns
> - **Services** (`services/`): Business logic that doesn't belong to a single CRUD operation — PDF processing, vector storage, AI querying. Calls CRUD and external APIs
>
> This layering means each piece has a single responsibility and can be tested independently.

---

**Q: What would you do differently if this were going to production?**

> 1. **Background task queue**: PDF processing (PDF parse → chunk → embed → upsert) is blocking. Move to Celery + Redis or FastAPI `BackgroundTasks` with a webhook/polling for completion
> 2. **Proper MongoDB indexes**: Index `users.email`, `users.username`, `documents.organizationId` for query performance
> 3. **Remove dead code**: `rag_service.py` is a leftover from the original monolithic implementation
> 4. **Token refresh**: Add a refresh token flow so users don't get logged out after 30 minutes
> 5. **Rate limiting**: Protect the `/qa/ask` endpoint since each call hits OpenAI (cost + abuse risk)
> 6. **Environment validation**: The `SECRET_KEY` has an insecure default — enforce a required, random key in production
> 7. **Centralized logging**: Replace `print()` statements with structured logging (JSON logs with request IDs)
> 8. **Document deletion**: Add a delete endpoint that removes both MongoDB metadata and Pinecone vectors

---

## SECTION 7: LangChain

**Q: Why use LangChain at all? Couldn't you call OpenAI directly?**

> Yes, you could call OpenAI directly. LangChain was used mainly for two things:
> 1. `RecursiveCharacterTextSplitter` — high-quality chunking with configurable separators
> 2. `PineconeVectorStore` — a unified abstraction that handles embed-then-upsert and embed-then-search in one call, so switching vector databases later would require minimal code changes
>
> The LLM call via `ChatOpenAI` could be replaced with `openai.chat.completions.create()` directly; LangChain doesn't add much there but it keeps the pattern consistent.

---

**Q: What is a prompt template and how did you use it?**

> A prompt template is a string with placeholders that gets filled at runtime with actual values. In `qa_service.py`, the template injects context chunks and the user's question:
> ```
> Context Information:
> {context}
> 
> Question: {question}
> 
> Instructions: Answer based ONLY on the provided context...
> ```
> The `Instructions` section is critical — it tells the model to stay grounded in the provided context and not fabricate information from training data.

---

## SECTION 8: Common Follow-Up Questions

**Q: What happens if no relevant context is found in Pinecone?**

> In `qa_service.py`, if `search_documents()` returns an empty list, the function returns early with: `"answer": "I could not find relevant information to answer your question."` and `"confidence": "LOW"`. This prevents sending an empty context to the LLM which would cause it to answer from training data.

---

**Q: How does the application handle errors?**

> Three layers:
> 1. **CRUD layer**: Raises `HTTPException` for known business errors (409 duplicate, 404 not found, 400 bad request)
> 2. **Endpoint layer**: Re-raises `HTTPException` from CRUD; catches unexpected `Exception` and raises HTTP 500
> 3. **Global handlers** in `main.py`: Catch `PyMongoError` (DB connectivity) and any unhandled `Exception` — both return generic HTTP 500 to avoid leaking stack traces to clients

---

**Q: Can a user search across all documents in their organization or only one?**

> Both. The `SearchRequest` and `QARequest` models have an optional `document_id` field:
> - If `document_id` is provided: Pinecone filter is `{"organization_id": ..., "document_id": ...}` — searches only that document
> - If `document_id` is `None`: filter is just `{"organization_id": ...}` — searches across all of the org's documents

---

**Q: How do you handle the fact that MongoDB stores `date` as `datetime`?**

> In `crud/user.py` during `create_user`, the `dob` date object is explicitly converted: `datetime.combine(dob, datetime.min.time())` before inserting. MongoDB doesn't have a native `date` type — it stores all dates as `datetime`. When the value is read back, Pydantic's `date` field validator accepts a `datetime` and extracts the date portion automatically.

---

**Q: You mentioned `hashed_password` has `exclude=True` — how does that work in Pydantic v2?**

> In Pydantic v2, `Field(exclude=True)` means that field is excluded from the model's `.model_dump()` output and from JSON serialization. When FastAPI serializes the response using `response_model=StandardResponse[UserResponse]`, it calls `.model_dump()` on the Pydantic object — `hashed_password` is never included. This is the safe way to have internal-only fields on a model.

---

**Q: What is the `GenderEnum` and how does it work with MongoDB?**

> `GenderEnum(str, Enum)` inherits from both `str` and `Enum`. The `str` inheritance means each enum member *is* a string — `GenderEnum.MALE == "Male"` is `True`. This means JSON serialization and MongoDB storage work naturally as strings. In `create_user`, there's an explicit extraction: `user_data['gender'] = user_data['gender'].value` to ensure the string value (not the enum wrapper) is stored in MongoDB.
