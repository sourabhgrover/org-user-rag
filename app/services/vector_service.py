from app.core.vector_store import vector_store_manager
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
    except Exception as e:
        print(f"Error while storing chunks in db {e}")
        raise