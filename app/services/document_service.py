from app.services.pdf_service import extract_text_from_pdf
from app.services.chunking_service import extract_text_into_chunks
from app.services.vector_service import store_chunks_in_pinecone

def process_documents(file_path:str,document_id:str,organization_id : str):
    try:
        # Step 1: Extract text from PDF file
        text = extract_text_from_pdf(file_path)
        print(f"Extracted {len(text)} characters from PDF")
        # Step 2: Split Text into chunks
        chunks = extract_text_into_chunks(text,document_id,organization_id)

        # Step 3: Store in Pinecone
        success = store_chunks_in_pinecone(chunks)
        if success:
            print(f"✅ Successfully processed and stored {len(chunks)} chunks!")
        else:
            print("❌ Failed to store chunks")

        return success
        
    except Exception as e:
        print(f"Error while processing document {e}")
        return False