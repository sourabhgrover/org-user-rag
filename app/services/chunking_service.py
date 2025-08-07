from langchain.text_splitter import RecursiveCharacterTextSplitter
def extract_text_into_chunks(text:str,document_id:str):
    try:
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000,chunk_overlap=200,separators=["\n\n", "\n", ". ", " ", ""])
        chunks = text_splitter.split_text(text)
        vector_ready_chunks_list = []
        for index,chunk in enumerate(chunks):
            chunk_data_dict = {
                "id": f"{document_id}_chunk_{index}",
                "text": chunk.strip(),
                "metadata" : {
                    "document_id" : document_id,
                    "chunk_index": index,
                    "chunk_length": len(chunk.strip())
                }
            }
            vector_ready_chunks_list.append(chunk_data_dict)
        return vector_ready_chunks_list
    except Exception as e:
        print(f"Error while chunking {e}")
        raise