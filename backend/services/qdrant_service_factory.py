"""
Qdrant Service Factory - Erstellt Qdrant Vector Service mit Azure-Konfiguration
"""

import os
from typing import Optional
import openai
from .qdrant_vector_service import QdrantVectorService

def create_qdrant_service() -> QdrantVectorService:
    """
    Erstellt einen Qdrant Vector Service mit Azure-Konfiguration aus Environment-Variablen.
    
    Returns:
        Konfigurierter QdrantVectorService
    """
    # Qdrant Konfiguration aus .env
    qdrant_url = os.getenv("QDRANT_URL") or os.getenv("QDRANT_PROD_URL")
    qdrant_api_key = os.getenv("QDRANT_API_KEY") or os.getenv("QDRANT_PROD_API_KEY")
    
    # Azure OpenAI Konfiguration
    azure_openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    azure_openai_key = os.getenv("AZURE_OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
    
    # OpenAI Client für Embeddings (fallback)
    openai_client = None
    if azure_openai_key and azure_openai_endpoint:
        openai_client = openai.AsyncOpenAI(
            api_key=azure_openai_key,
            base_url=f"{azure_openai_endpoint.rstrip('/')}/openai/deployments/text-embedding-3-small",
            api_version="2024-02-01"
        )
    
    # SentenceTransformers Model für lokale Embeddings
    embedding_model = "all-MiniLM-L6-v2"  # Schnell und effizient
    
    # Erstelle Qdrant Service
    qdrant_service = QdrantVectorService(
        qdrant_url=qdrant_url,
        qdrant_api_key=qdrant_api_key,
        openai_client=openai_client,
        embedding_model=embedding_model
    )
    
    return qdrant_service

# Singleton Instance
_qdrant_service: Optional[QdrantVectorService] = None

def get_qdrant_service() -> QdrantVectorService:
    """
    Gibt die Singleton-Instanz des Qdrant Services zurück.
    
    Returns:
        QdrantVectorService Singleton
    """
    global _qdrant_service
    
    if _qdrant_service is None:
        _qdrant_service = create_qdrant_service()
    
    return _qdrant_service

async def initialize_quote_collection() -> bool:
    """
    Initialisiert die Quote Collection beim Startup.
    
    Returns:
        True wenn erfolgreich
    """
    try:
        qdrant_service = get_qdrant_service()
        success = await qdrant_service.create_quote_collection()
        
        if success:
            print("✅ Quote Collection erfolgreich initialisiert")
        else:
            print("❌ Fehler beim Initialisieren der Quote Collection")
        
        return success
    
    except Exception as e:
        print(f"❌ Fehler beim Initialisieren des Qdrant Services: {str(e)}")
        return False

async def test_qdrant_connection() -> bool:
    """
    Testet die Verbindung zu Qdrant.
    
    Returns:
        True wenn Verbindung erfolgreich
    """
    try:
        qdrant_service = get_qdrant_service()
        
        # Test der Verbindung durch Abrufen der Collections
        collections = qdrant_service.qdrant_client.get_collections()
        print(f"✅ Qdrant Verbindung erfolgreich. Verfügbare Collections: {len(collections.collections)}")
        
        # Zeige verfügbare Collections
        for collection in collections.collections:
            print(f"  - {collection.name}")
        
        return True
    
    except Exception as e:
        print(f"❌ Qdrant Verbindungsfehler: {str(e)}")
        return False
