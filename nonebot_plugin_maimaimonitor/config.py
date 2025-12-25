from pydantic import BaseModel
from typing import Optional

class Config(BaseModel):
    maimai_bot_client_id: Optional[str] = None
    maimai_bot_private_key: Optional[str] = None
    maimai_bot_display_name: Optional[str] = "BOT"
    maimai_worker_url: str = "https://maiapi.chongxi.us"

    class Config:
        extra = "ignore"
