from app.core.vector_store import vector_store_manager
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