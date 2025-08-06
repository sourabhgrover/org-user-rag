from langchain_openai import ChatOpenAI
from app.core.config import settings

class LLMManager:
    def __init__(self):
        self.llm = None
        self._initialize()
    
    def _initialize(self):
        try:
            print(f"Creating LLM Instance...")
            self.llm = ChatOpenAI(model="gpt-3.5-turbo",
                temperature=0.1,  # Low temperature for factual answers
                openai_api_key=settings.OPENAI_API_KEY)
        except Exception as e:
            print(f"Some thing went wrong while initializing LLM {e}")
            raise
    
    def get_llm(self):
        return self.llm
    
llm_manager = LLMManager()
