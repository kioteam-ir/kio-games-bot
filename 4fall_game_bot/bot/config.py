import os
from dotenv import load_dotenv
from dataclasses import dataclass

# load .env file
load_dotenv()

@dataclass
class Config:
    SESSION_NAME : str
    TOKEN        : str
    API_HASH     : str
    API_ID       : int
    
# raise TypeError or ValueError for None or incorrect fields
config = Config(
    SESSION_NAME = os.getenv("SESSION_NAME"),                                   # type: ignore
    TOKEN        = os.getenv("TOKEN"),                                          # type: ignore
    API_HASH     = os.getenv("API_HASH"),                                       # type: ignore
    API_ID       = int(api_id) if (api_id := os.getenv("API_ID")) else None     # type: ignore
)

__all__ = ("config",)       # Only can import 'config' name-space from this file