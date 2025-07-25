"""
Configuration for Azure + Qdrant integration.
Replace LlamaCloud configuration with Azure and Qdrant settings.
"""

import os
from typing import Optional
from pydantic import BaseSettings, Field

class AzureQdrantConfig(BaseSettings):
    """Configuration for Azure Document Intelligence and Qdrant Vector Database."""
    
    # Azure Document Intelligence
    azure_document_intelligence_endpoint: Optional[str] = Field(
        default=None,
        env="AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT",
        description="Azure Document Intelligence service endpoint"
    )
    
    # Azure Storage
    azure_storage_account_url: Optional[str] = Field(
        default=None,
        env="AZURE_STORAGE_ACCOUNT_URL",
        description="Azure Storage account URL for document storage"
    )
    
    azure_storage_container_name: str = Field(
        default="rfp-documents",
        env="AZURE_STORAGE_CONTAINER_NAME",
        description="Default container name for document storage"
    )
    
    # Qdrant Vector Database
    qdrant_url: Optional[str] = Field(
        default="http://localhost:6333",
        env="QDRANT_URL",
        description="Qdrant server URL"
    )
    
    qdrant_api_key: Optional[str] = Field(
        default=None,
        env="QDRANT_API_KEY",
        description="Qdrant API key for authentication"
    )
    
    # Embedding Configuration
    embedding_model: str = Field(
        default="all-MiniLM-L6-v2",
        env="EMBEDDING_MODEL",
        description="SentenceTransformers model for text embeddings"
    )
    
    embedding_dimension: int = Field(
        default=384,
        env="EMBEDDING_DIMENSION",
        description="Dimension of embedding vectors"
    )
    
    # OpenAI (for AI processing)
    openai_api_key: Optional[str] = Field(
        default=None,
        env="OPENAI_API_KEY",
        description="OpenAI API key for AI operations"
    )
    
    # Document Processing
    chunk_size: int = Field(
        default=1000,
        env="CHUNK_SIZE",
        description="Size of text chunks for embedding"
    )
    
    chunk_overlap: int = Field(
        default=200,
        env="CHUNK_OVERLAP",
        description="Overlap between consecutive chunks"
    )
    
    max_context_length: int = Field(
        default=4000,
        env="MAX_CONTEXT_LENGTH",
        description="Maximum context length for AI responses"
    )
    
    # Search Configuration
    search_limit: int = Field(
        default=10,
        env="SEARCH_LIMIT",
        description="Default limit for search results"
    )
    
    search_score_threshold: float = Field(
        default=0.7,
        env="SEARCH_SCORE_THRESHOLD",
        description="Minimum similarity score for search results"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Global configuration instance
azure_qdrant_config = AzureQdrantConfig()

def get_azure_qdrant_config() -> AzureQdrantConfig:
    """Get the Azure + Qdrant configuration."""
    return azure_qdrant_config

def validate_azure_qdrant_config() -> bool:
    """
    Validate that required Azure + Qdrant configuration is available.
    
    Returns:
        True if configuration is valid
    """
    config = get_azure_qdrant_config()
    
    required_configs = [
        (config.azure_document_intelligence_endpoint, "AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT"),
        (config.azure_storage_account_url, "AZURE_STORAGE_ACCOUNT_URL"),
        (config.qdrant_url, "QDRANT_URL"),
        (config.openai_api_key, "OPENAI_API_KEY")
    ]
    
    missing_configs = []
    for value, name in required_configs:
        if not value:
            missing_configs.append(name)
    
    if missing_configs:
        print(f"Missing required configuration: {', '.join(missing_configs)}")
        return False
    
    return True
