import os
import sys
from dotenv import load_dotenv
from qdrant_client import QdrantClient, models
from langchain_openai import AzureOpenAIEmbeddings
from langchain_qdrant import FastEmbedSparse, QdrantVectorStore, RetrievalMode
from langfuse.openai import AzureOpenAI
from typing import List, Tuple

# Load environment variables
load_dotenv()

COLLECTION_NAME = "vivavis_basic_knowledge"
QDRANT_URL = os.getenv("QDRANT_PROD_URL", os.getenv("QDRANT_URL"))
QDRANT_API_KEY = os.getenv("QDRANT_PROD_API_KEY", os.getenv("QDRANT_API_KEY"))
AZURE_ENDPOINT = os.getenv("AZURE_GPT_ENDPOINT")
AZURE_API_KEY = os.getenv("AZURE_GPT_KEY")

# Initialize clients
qdrant_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

# Initialize embeddings
embeddings = AzureOpenAIEmbeddings(model="text-embedding-3-large-2")
sparse_embeddings = FastEmbedSparse(model_name="Qdrant/bm25")

# Initialize Azure OpenAI
openai_client = AzureOpenAI(
    azure_endpoint=AZURE_ENDPOINT,
    api_version="2025-01-01-preview",
    api_key=AZURE_API_KEY
)


def ensure_collection_exists():
    """Check if collection exists and create if it doesn't"""
    try:
        collections = qdrant_client.get_collections().collections
        collection_names = [collection.name for collection in collections]

        if COLLECTION_NAME not in collection_names:
            print(f"Collection '{COLLECTION_NAME}' doesn't exist. Creating it...")
            qdrant_client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config={
                    "size": 3072,
                    "distance": "Cosine",
                },
                sparse_vectors_config={
                    "sparse": models.SparseVectorParams(
                        index=models.SparseIndexParams(on_disk=False)
                    )
                },
            )
            print(f"Collection '{COLLECTION_NAME}' created successfully.")
        else:
            print(f"Collection '{COLLECTION_NAME}' already exists.")
    except Exception as e:
        print(f"Error checking/creating collection: {e}")
        sys.exit(1)


def search_documents(query: str, k: int = 5) -> List[Tuple[dict, float]]:
    """Search for relevant documents in Qdrant"""
    try:
        vector_store = QdrantVectorStore(
            client=qdrant_client,
            collection_name=COLLECTION_NAME,
            embedding=embeddings,
            sparse_embedding=sparse_embeddings,
            retrieval_mode=RetrievalMode.HYBRID,
            vector_name="",
            sparse_vector_name="sparse",
        )

        # Perform similarity search with relevance scores
        results = vector_store._similarity_search_with_relevance_scores(query, k=k)
        return results
    except Exception as e:
        print(f"Error searching documents: {e}")
        return []


def generate_answer(query: str, context: str) -> str:
    """Generate answer using Azure OpenAI"""
    try:
        system_prompt = """Du bist ein hilfreicher Assistent, der Fragen basierend auf dem gegebenen Kontext beantwortet. 
        Antworte präzise und nutze nur die Informationen aus dem Kontext. 
        Wenn die Antwort nicht im Kontext zu finden ist, sage das klar."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Kontext:\n{context}\n\nFrage: {query}"}
        ]

        response = openai_client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=messages,
            temperature=0.7,
            max_tokens=500
        )

        return response.choices[0].message.content
    except Exception as e:
        return f"Error generating answer: {e}"


def format_search_results(results: List[Tuple[dict, float]]) -> str:
    """Format search results into a context string"""
    context_parts = []

    for i, (doc, score) in enumerate(results, 1):
        metadata = doc.metadata
        content = doc.page_content

        # Extract metadata
        doc_id = metadata.get('doc_id', 'Unknown')
        page = metadata.get('page_number', 'Unknown')
        headers = []
        for j in range(1, 7):
            header_key = f'header_{j}'
            if header_key in metadata and metadata[header_key]:
                headers.append(metadata[header_key])

        header_path = " > ".join(headers) if headers else "No headers"

        context_parts.append(f"--- Dokument {i} (Score: {score:.3f}) ---")
        context_parts.append(f"ID: {doc_id}")
        context_parts.append(f"Seite: {page}")
        context_parts.append(f"Pfad: {header_path}")
        context_parts.append(f"Inhalt:\n{content}\n")

    return "\n".join(context_parts)


def main():
    """Main function for terminal RAG"""
    print("=== Terminal RAG System ===")
    print(f"Using collection: {COLLECTION_NAME}")
    print(f"Qdrant URL: {QDRANT_URL}")

    # Ensure collection exists
    ensure_collection_exists()

    while True:
        print("\n" + "=" * 50)
        query = input("Deine Frage (oder 'exit' zum Beenden): ").strip()

        if query.lower() in ['exit', 'quit', 'q']:
            print("Auf Wiedersehen!")
            break

        if not query:
            print("Bitte gib eine Frage ein.")
            continue

        print(f"\nSuche nach relevanten Dokumenten für: '{query}'...")

        # Search for relevant documents
        results = search_documents(query, k=5)

        if not results:
            print("Keine relevanten Dokumente gefunden.")
            #continue

        print(f"\n{len(results)} relevante Dokumente gefunden:")

        # Format results for display
        for i, (doc, score) in enumerate(results, 1):
            metadata = doc.metadata
            print(f"{i}. Dokument ID: {metadata.get('doc_id', 'Unknown')} (Score: {score:.3f})")

        # Generate context from results
        context = format_search_results(results)

        # Generate answer
        print("\nGeneriere Antwort...")
        answer = generate_answer(query, context)

        print("\n--- ANTWORT ---")
        print(answer)

        # Optionally show the full context
        show_context = input("\nMöchtest du den vollständigen Kontext sehen? (j/n): ").strip().lower()
        if show_context == 'j':
            print("\n--- KONTEXT ---")
            print(context)


if __name__ == "__main__":
    main()