import os
import yaml
from pydantic_settings import BaseSettings
from typing import List, Dict, Any

def load_project_config() -> Dict[str, Any]:
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "configs", "project.yaml")
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        return {}

class Settings(BaseSettings):
    project_name: str = "SIH26191 Backend API"
    api_version: str = "1.0.0"
    
    # CORS Configuration
    # Defaults to local dev allowed origins if not specified in environment
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000"
    ]
    
    project_config: Dict[str, Any] = load_project_config()

settings = Settings()
