"""Configuration models using Pydantic."""

from pydantic import BaseModel, Field, SecretStr
from typing import Literal


class ZohoSDKConfig(BaseModel):
    """Zoho SDK configuration."""

    client_id: str
    client_secret: SecretStr
    refresh_token: SecretStr
    redirect_url: str = "http://localhost:8000/oauth/callback"
    region: Literal["us", "eu", "au", "in", "cn", "jp"] = "us"
    environment: Literal["production", "sandbox", "developer"] = "production"


class DatabaseConfig(BaseModel):
    """Database configuration."""

    host: str = "localhost"
    port: int = 5432
    database: str = "sergas_agent_db"
    user: str
    password: SecretStr


class AgentConfig(BaseModel):
    """Agent configuration."""

    name: str
    system_prompt: str
    allowed_tools: list[str] = Field(default_factory=list)
    max_iterations: int = 10
    temperature: float = 0.3
