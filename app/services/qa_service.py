from app.core.llm import llm_manager
from app.services.search_service import search_documents
def answer_question(question: str,organization_id:str,document_id: str = None,max_context_chunks: int = 5):
    try:
        print(f"Answering question: {question}")
        # Step 1: Search for relevant context
        context_results =  search_documents(question,organization_id,document_id,max_context_chunks)
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