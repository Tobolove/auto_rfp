import os
from qdrant_client import QdrantClient, models

# Annahme: Diese Umgebungsvariablen sind gesetzt
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_COLLECTION_NAME = "RFP_Documents_Collection"

def init_qdrant_client():
    """Initialisiert und gibt den Qdrant Client zurück."""
    client = QdrantClient(
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY,
    )
    return client

def add_document_to_qdrant(new_document, markdown_content, qdrant_client, embeddings_model):
    """
    Erstellt ein Embedding für den Dokumenteninhalt und lädt es als Punkt zu Qdrant hoch.

    Args:
        new_document: Das ORM-Objekt des Dokuments (z.B. von SQLAlchemy).
        markdown_content (str): Der Textinhalt des Dokuments.
        qdrant_client (QdrantClient): Der initialisierte Qdrant Client.
        embeddings_model: Das initialisierte Modell zum Erstellen von Vektoren.
    """
    try:
        document_id = new_document.id
        print(f"🚀 Starte Upload zu Qdrant für Dokument-ID: {document_id}")

        # 1. Erstelle das Vektor-Embedding für den Inhalt
        vector = embeddings_model.embed_query(markdown_content)

        # 2. Definiere den Payload (Metadaten für die Filterung)
        #    Speichere die ID deiner Haupt-DB, um eine Verknüpfung zu haben.
        payload = {
            "db_id": document_id,
            "content": markdown_content,
            "created_at": new_document.created_at.isoformat() # Beispiel für weitere Metadaten
        }

        # 3. Lade den Punkt (Vektor + Payload) zu Qdrant hoch
        qdrant_client.upsert(
            collection_name=QDRANT_COLLECTION_NAME,
            points=[
                models.PointStruct(
                    id=document_id,  # Wichtig: Nutze die ID aus deiner relationalen DB
                    vector=vector,
                    payload=payload
                )
            ],
            wait=True # Warte auf die Bestätigung des Servers
        )
        print(f"✅ Dokument-ID {document_id} erfolgreich zu Qdrant hinzugefügt.")

    except Exception as e:
        print(f"Fehler beim Hinzufügen des Dokuments {new_document.id} zu Qdrant: {e}")
        # Wirf die Exception erneut, damit die darüberliegende Transaktion fehlschlägt
        raise e