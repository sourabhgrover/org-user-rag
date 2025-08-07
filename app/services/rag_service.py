from operator import index
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings , ChatOpenAI
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec
import time
from app.core.vector_store import vector_store_manager
from app.core.config import settings
from app.core.llm import llm_manager

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
    # print(f"TEXTTT {type(text_splitter)}  {text_splitter}")
    # print(f"Extracted {len(chunks)} chunks from document {chunks}")
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

def generate_embeddings_for_chunks(chunks):
    chunks_with_embeddings = []
    text = []
    for chunk in chunks:
        text.append(chunk["text"])
    
    try:
        embeddings = OpenAIEmbeddings(model="text-embedding-ada-002", openai_api_key=settings.OPENAI_API_KEY)
        print(f"Generating embeddings for {len(text)} chunks...")
        embedding_vectors = embeddings.embed_documents(text)

        for i, (chunk, embedding) in enumerate(zip(chunks, embedding_vectors)):
            chunk_with_embedding = {
                "id": chunk["id"],
                "text": chunk["text"],
                "embedding": embedding,
                "metadata": chunk["metadata"]
            }
            chunks_with_embeddings.append(chunk_with_embedding)

    except Exception as e:
        print(f"Error in generating embeddings: {e}")
        return []
    return chunks_with_embeddings

def store_chunks_in_pinecone(chunks):
    try:
        vector_store = vector_store_manager.get_vector_store()
        texts = []
        metadatas = []
        for chunk in chunks:
         texts.append(chunk["text"])
         metadatas.append(chunk["metadata"])

         # LangChain handles embedding generation + storage automatically!
        # vector_store.add_texts(texts=texts, metadatas=metadatas)
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
        vector_store = vector_store_manager.get_vector_store()
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
    
def answer_question(question: str,document_id: str = None, organization_id:str = None,max_context_chunks: int = 5):
    try:
        print(f"Answering question: {question}")
        # Step 1: Search for relevant context
        context_results =  search_documents(question,document_id,organization_id,max_context_chunks)
        if not context_results:
            return {
                "answer": "I counld not find relevant information to answer your question.",
                "confidence": "LOW",
                "context_sources": [],
                "context_used": ""
            }
        print(  f"Found {len(context_results)} context chunks for question '{question}'")
        #2 : Prepare context for LLM
        context_texts = []
        for result in context_results:
            context_texts.append(f"Context {len(context_texts) + 1}: {result['text']}")
        
        context_string = "\n\n".join(context_texts)

        # Step 3: Create prompt for GPT
        prompt_template = """
        You are a helpful AI assistant that answers questions based on the provided context.
        
        Context Information:
        {context}
        
        Question: {question}
        
        Instructions:
        - Answer the question based ONLY on the provided context
        - If the context doesn't contain enough information, say so
        - Be concise but comprehensive
        - Don't make up information not in the context
        - If you're unsure, mention your uncertainty
        
        Answer:
        """

         # Step 4: Get answer from GPT
        # llm = ChatOpenAI(
        #     model="gpt-3.5-turbo",
        #     temperature=0.1,  # Low temperature for factual answers
        #     openai_api_key=settings.OPENAI_API_KEY
        # )
        llm = llm_manager.get_llm()

        prompt = prompt_template.format(context=context_string, question=question)
        response = llm.invoke(prompt)

        # Step 5: Determine confidence based on context quality
        avg_score = sum(result['score'] for result in context_results) / len(context_results)
        confidence = "High" if avg_score < 0.3 else "Medium" if avg_score < 0.6 else "Low"

        # Return the actual response, not just True!
        return {
            "answer": response.content,
            "confidence": confidence,
            "context_sources": context_results,
            "context_used": context_string
        }
    except Exception as e:
        print(f"Error answering question: {e}")
        return None