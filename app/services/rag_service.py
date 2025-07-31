from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter

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
        print(chunks)
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