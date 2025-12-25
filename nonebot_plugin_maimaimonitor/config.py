from pydantic_settings import BaseSettings

class Config(BaseSettings):
    maimai_bot_client_id: str
    maimai_bot_private_key: str
    maimai_bot_display_name: str
    maimai_worker_url: str = "https://maiapi.chongxi.us"
