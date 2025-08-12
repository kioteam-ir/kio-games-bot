import os
from dotenv import load_dotenv
from dataclasses import dataclass
from typing import Optional, Self

DEFAULT_SESSION_NAME = 'bot'

# load .env file
load_dotenv()

@dataclass(frozen=True, slots=True)
class Config:
    SESSION_NAME : str
    TOKEN        : Optional[str]
    API_HASH     : Optional[str]
    API_ID       : Optional[str]
    
    @classmethod
    def from_env(cls) -> Self:
        return cls(
            SESSION_NAME = os.getenv("SESSION_NAME", DEFAULT_SESSION_NAME),                          
            TOKEN        = os.getenv("TOKEN"),                                  
            API_HASH     = os.getenv("API_HASH"),                               
            API_ID       = os.getenv("API_ID"),                                 
        )
    

config = Config.from_env()

__all__ = ("config",)       # Only can import 'config' name-space from this file