from pydantic import BaseModel
from typing import List, Dict, Any

class BancoApi(BaseModel):
    user_id: int
    name: str
    orders: List[Dict[str, Any]]

    class Config:
        from_attributes = True 