from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings

from app.core.config import settings

def process_documents(file_path: str,document_id:str):
    print(f"Processing Document {file_path} with {document_id}")
    try:
        #Step 1: Extract text from PDF file
        text = extract_text_from_pdf(file_path)
        print(f"Extracted {len(text)} characters from PDF")
        # print(f"First 200 characters {text[:200]} characters from PDF")

        # Step 2: Split Text into chunks
        chunks = extract_text_into_chunks(text,document_id)
        
        # Step 3: Generate embeddings from Chunks
        chunks_with_embeddings = generate_embeddings_for_chunks(chunks)
        print(chunks_with_embeddings)
        return True
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