from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from app.core.config import settings
from pinecone import Pinecone , ServerlessSpec
import time
import logging

logger = logging.getLogger(__name__)

class VectorStoreManager:
    def __init__(self):
        self.embeddings = None
        self.vector_store = None
        self.pinecone_client = None
        self._initialize()
    
    def _initialize(self):
        try:
            logger.info("Initializing vector store")
            self.embeddings = OpenAIEmbeddings(model="text-embedding-ada-002",api_key=settings.OPENAI_API_KEY)
            self.pinecone_client = Pinecone(api_key=settings.PINECONE_API_KEY)
            self._ensure_index_exists();

            pinecone_index = self.pinecone_client.Index(settings.PINECONE_INDEX_NAME)
            self.vector_store = PineconeVectorStore(index=pinecone_index,embedding=self.embeddings)
        except Exception as e:
            logger.error(f"Error initializing vector store")
            raise

    def _ensure_index_exists(self):

        try:
            # Get all the index name
            existing_index = [index_detail["name"] for index_detail in self.pinecone_client.list_indexes()]

            # Check if index exists if not than create it

            if settings.PINECONE_INDEX_NAME not in existing_index:
                self.pinecone_client.create_index(
                    name=settings.PINECONE_INDEX_NAME,
                    dimension=1536,
                    metric="cosine", # Or "dotproduct" or "euclidean"
                    spec=ServerlessSpec(cloud="aws", region="us-east-1")
                )

                while not self.pinecone_client.describe_index(settings.PINECONE_INDEX_NAME).status["ready"]:
                    logger.info("Waiting for index to be ready")
                    time.sleep(1)
                logger.info(f"Pinecone index {settings.PINECONE_INDEX_NAME} created")
            else:
                logger.info(f"Pinecode index {settings.PINECONE_INDEX_NAME} already exists")

        except Exception as e:
            logger.error(f"Error creating index {e}")
            raise

    def get_vector_store(self):
        return self.vector_store
    
    def get_embeddings(self):
        return self.embeddings


vector_store_manager = VectorStoreManager()