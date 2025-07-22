from pydantic import BaseModel
from typing import Optional, Any, Generic, TypeVar

T = TypeVar('T')

class StandardResponse(BaseModel, Generic[T]):
    """Standard response model for all API endpoints"""
    status: str
    message: str
    data: Optional[T] = None
    
    class Config:
        json_encoders = {
            # Add any custom encoders if needed
        }
