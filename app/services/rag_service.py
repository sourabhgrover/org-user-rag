from operator import index
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec
import time


from app.core.config import settings

embeddings = OpenAIEmbeddings(
    model="text-embedding-ada-002",
    openai_api_key=settings.OPENAI_API_KEY
)


index_name = settings.PINECONE_INDEX_NAME

# Initialize Pinecone client manually
pc = Pinecone(api_key=settings.PINECONE_API_KEY)

# Fix: Get the list of index names correctly
existing_indexes = [index_info["name"] for index_info in pc.list_indexes()]

# Check if the index exists, and create it if not
if index_name not in existing_indexes:
    print(f"Creating Pinecone index: {index_name}...")
    pc.create_index(
        name=index_name,
        dimension=1536,
        metric="cosine", # Or "dotproduct" or "euclidean"
        spec=ServerlessSpec(cloud="aws", region="us-east-1") # Adjust cloud and region as needed
    )
    # Wait for index to be ready
    while not pc.describe_index(index_name).status["ready"]:
         print("Waiting for index to be ready...")
         time.sleep(1)
    print("Index created.")
else:
    print(f"Pinecone index '{index_name}' already exists.")

# Connect to the index
pinecone_index = pc.Index(index_name)

# Create vector store with the index
vector_store = PineconeVectorStore(index=pinecone_index, embedding=embeddings)

def process_documents(file_path: str,document_id:str):
    print(f"Processing Document {file_path} with {document_id}")
    try:

        #Step 1: Extract text from PDF file
        text = extract_text_from_pdf(file_path)
        print(f"Extracted {len(text)} characters from PDF")
        # print(f"First 200 characters {text[:200]} characters from PDF")

        # Step 2: Split Text into chunks
        chunks = extract_text_into_chunks(text,document_id)
        
        # # Step 3: Generate embeddings from Chunks
        # chunks_with_embeddings = generate_embeddings_for_chunks(chunks)
        # print(chunks_with_embeddings)

         # Step 3 & 4: Store in Pinecone (embeddings generated automatically!)
        success = store_chunks_in_pinecone(chunks)
        if success:
            print(f"✅ Successfully processed and stored {len(chunks)} chunks!")
        else:
            print(" Failed to store chunks")


        return success
    except Exception as e:
        print(f"Error in proeccession file {file_path}")
        return False

def extract_text_from_pdf(file_path) -> str:
    try:
        with open(file_path,"rb") as file:
            pdf_reader = PdfReader(file)

            text = ""

            for index, page in enumerate(pdf_reader.pages):
                page_text = page.extract_text()
                text += f"\n--- Page {index + 1} ---\n"
                text += page_text
        return text    
    except Exception as e:
        return print(f"Erorr while extracting text from PDF {e}")
    
def extract_text_into_chunks(text:str,document_id:str):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000,chunk_overlap=200,separators=["\n\n", "\n", ". ", " ", ""])
    chunks = text_splitter.split_text(text)
    vector_ready_chunks = []
    for i,chunk in enumerate(chunks):
        chunk_data = {
            "id": f"{document_id}_chunk_{i}",
            "text": chunk.strip(),
            "metadata": {
                "document_id": document_id,
                "chunk_index": i,
                "chunk_length": len(chunk.strip())
            }
        }
        vector_ready_chunks.append(chunk_data)
    return vector_ready_chunks

# def generate_embeddings_for_chunks(chunks):
#     chunks_with_embeddings = []
#     text = []
#     for chunk in chunks:
#         text.append(chunk["text"])
    
#     try:
#         embeddings = OpenAIEmbeddings(model="text-embedding-ada-002", openai_api_key=settings.OPENAI_API_KEY)
#         print(f"Generating embeddings for {len(text)} chunks...")
#         embedding_vectors = embeddings.embed_documents(text)

#         for i, (chunk, embedding) in enumerate(zip(chunks, embedding_vectors)):
#             chunk_with_embedding = {
#                 "id": chunk["id"],
#                 "text": chunk["text"],
#                 "embedding": embedding,
#                 "metadata": chunk["metadata"]
#             }
#             chunks_with_embeddings.append(chunk_with_embedding)

#     except Exception as e:
#         print(f"Error in generating embeddings: {e}")
#         return []
#     return chunks_with_embeddings

def store_chunks_in_pinecone(chunks):
    try:
        texts = []
        metadatas = []
        for chunk in chunks:
         texts.append(chunk["text"])
         metadatas.append(chunk["metadata"])

         # LangChain handles embedding generation + storage automatically!
        vector_store.add_texts(texts=texts, metadatas=metadatas)
        
        print(f"✅ Successfully stored {len(chunks)} chunks in Pinecone!")
        return True
        print(f"✅ Successfully stored {len(chunks)} chunks in Pinecone!")
        return True
    except Exception as e:
        print(f"Error in storing chunks in Pinecone: {e}")

def search_documents(query: str, document_id: str = None, organization_id: str = None, top_k: int = 5):
    """
    Universal search method - handles all search scenarios
    """
    try:
        print(f"Searching for: '{query}'")
        
        # Build filter based on what's provided
        filter_dict = {}
        
        if document_id:
            # Search in specific document
            filter_dict = {"document_id": document_id}
            print(f"Searching in document: {document_id}")
        elif organization_id:
            # Search in organization
            filter_dict = {"document_id": {"$regex": f"^{organization_id}_"}}
            print(f"Searching in organization: {organization_id}")
        else:
            # Search all documents
            print("Searching across all documents")
        
        print (f"Filter applied: {filter_dict}")
        # Perform search with or without filter
        if filter_dict:
            results = vector_store.similarity_search_with_score(
                query, k=top_k, filter=filter_dict
            )
        else:
            results = vector_store.similarity_search_with_score(query, k=top_k)
        
        # Format results
        formatted_results = []
        for doc, score in results:
            result = {
                "text": doc.page_content,
                "score": float(score),
                "relevance": "High" if score < 0.3 else "Medium" if score < 0.6 else "Low",
                "metadata": doc.metadata
            }
            formatted_results.append(result)
        
        print(f"Found {len(formatted_results)} results")
        return formatted_results
        
    except Exception as e:
        print(f"Error searching documents: {e}")
        return []