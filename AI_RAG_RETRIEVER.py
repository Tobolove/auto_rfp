import os
from flask import request, Blueprint, jsonify, Response, stream_with_context
from dotenv import find_dotenv, load_dotenv
import traceback
from langchain_openai import AzureOpenAIEmbeddings
from langchain_qdrant import FastEmbedSparse, QdrantVectorStore, RetrievalMode
from langfuse.openai import AzureOpenAI
from qdrant_client import QdrantClient, models
from models import Document, VisibilityEnum, db, ChatHistory
from constants import SYSTEM_PROMPTS
import time
from datetime import datetime, timedelta

# Ratenbegrenzungskonstanten
RATE_LIMIT_PER_HOUR = 30
RATE_LIMIT_WINDOW_SECONDS = 3600 # 1 Stunde

# Dictionary zum Speichern der Anfragen pro IP-Adresse
# Format: { "ip_address": [timestamp1, timestamp2, ...] }
request_counts = {}

# Blueprint für Public API
public_api = Blueprint("public_api", __name__)

# Umgebungsvariablen laden
load_dotenv(find_dotenv())

# Azure OpenAI Konfiguration
endpoint = os.getenv("AZURE_GPT_ENDPOINT")
api_key = os.getenv("AZURE_GPT_KEY")
model_name = "gpt-4.1-mini"
collection_name = os.getenv("COLLECTION_NAME")

# Sicherstellen, dass API-Schlüssel geladen sind
if not api_key or not endpoint:
    raise ValueError("Azure OpenAI API key or endpoint is missing. Check your .env file.")

# Azure OpenAI Client initialisieren
client = AzureOpenAI(
    azure_endpoint=endpoint,
    api_version="2025-01-01-preview",
    api_key=api_key
)

# Qdrant und Embeddings initialisieren
embeddings = AzureOpenAIEmbeddings(
    model="text-embedding-3-large-2"
)
sparse_embeddings = FastEmbedSparse(model_name="Qdrant/bm25")

qdrant_client = QdrantClient(
    url=os.getenv("QDRANT_PROD_URL"),
    api_key=os.getenv("QDRANT_PROD_API_KEY")
)


@public_api.route('/chat', methods=['POST'])
def public_chat():
    """
    Öffentlicher Endpoint für GPT-Anfragen mit History-Support.
    Erwartet JSON mit 'prompt' Feld und optionalem 'history' Array.

    Request Format:
    {
        "prompt": "Deine Frage hier",
        "history": [
            {"role": "user", "content": "Vorherige Frage"},
            {"role": "assistant", "content": "Vorherige Antwort"}
        ]
    }
    """
    try:
        # Ratenbegrenzung implementieren
        user_ip = request.remote_addr
        current_time = time.time()

        if user_ip not in request_counts:
            request_counts[user_ip] = []

        # Alte Anfragen entfernen (älter als das Zeitfenster)
        request_counts[user_ip] = [
            t for t in request_counts[user_ip]
            if current_time - t < RATE_LIMIT_WINDOW_SECONDS
        ]

        # Prüfen, ob das Limit überschritten wurde
        if len(request_counts[user_ip]) >= RATE_LIMIT_PER_HOUR:
            print(f"⚠️ PUBLIC API - Ratenbegrenzung für IP {user_ip} überschritten.")
            return jsonify({
                'error': 'Zu viele Anfragen. Bitte versuchen Sie es in einer Stunde erneut.'
            }), 429

        # Aktuelle Anfrage hinzufügen
        request_counts[user_ip].append(current_time)
        print(f"✅ PUBLIC API - Anfrage von IP {user_ip}. Aktuelle Anfragen in Stunde: {len(request_counts[user_ip])}")

        # Request-Validierung
        if not request.json:
            return jsonify({'error': 'Invalid request format. JSON required.'}), 400
            
        if "prompt" not in request.json:
            return jsonify({'error': 'Missing required field: prompt.'}), 400

        user_prompt = request.json.get("prompt", "").strip()
        history = request.json.get("history", [])

        # Input validation
        if not user_prompt:
            return jsonify({'error': 'Prompt cannot be empty.'}), 400
            
        if len(user_prompt) > 1000:  # Prevent DoS through large inputs
            return jsonify({'error': 'Prompt too long. Maximum 1000 characters.'}), 400

        # History validieren (falls vorhanden)
        if history and not isinstance(history, list):
            return jsonify({'error': 'History must be an array.'}), 400
            
        if len(history) > 20:  # Prevent DoS through large history
            return jsonify({'error': 'History too long. Maximum 20 messages.'}), 400

        print(f"🔍 PUBLIC API - Prompt erhalten: {user_prompt[:100]}...")
        print(f"📚 PUBLIC API - History Nachrichten: {len(history)}")

        # RAG: Qdrant-Suche für relevante Dokumente
        context_content = ""
        try:
            print("🔍 PUBLIC API - Starte Qdrant-Suche...")

            # Qdrant VectorStore initialisieren
            vectorstore = QdrantVectorStore(
                client=qdrant_client,
                collection_name=collection_name,
                embedding=embeddings,
                sparse_embedding=sparse_embeddings,
                retrieval_mode=RetrievalMode.HYBRID,
                vector_name="",
                sparse_vector_name="sparse"
            )

            # Nur öffentliche Dokumente aus der Datenbank holen
            public_docs = Document.query.filter(
                Document.visibility == VisibilityEnum.PUBLIC
            ).all()

            print(f"📊 PUBLIC API - Gefundene öffentliche Dokumente: {len(public_docs)}")

            if public_docs:
                # Document IDs für Qdrant-Filter extrahieren
                doc_ids = [str(doc.id) for doc in public_docs]

                # Qdrant-Suche mit Filter auf öffentliche Dokumente
                qdrant_chunks = vectorstore._similarity_search_with_relevance_scores(
                    user_prompt,
                    k=8,
                    filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="metadata.doc_id",
                                match=models.MatchAny(any=doc_ids)
                            )
                        ]
                    )
                )

                print(f"🔍 PUBLIC API - Qdrant Chunks gefunden: {len(qdrant_chunks)}")

                # Kontext aus gefundenen Chunks erstellen
                if qdrant_chunks:
                    context_parts = []
                    for doc, score in qdrant_chunks:
                        if hasattr(doc, 'page_content') and doc.page_content:
                            context_parts.append(doc.page_content)

                    if context_parts:
                        context_content = "\n\n".join(context_parts[:5])  # Maximal 5 Chunks
                        print(f"✅ PUBLIC API - Kontext erstellt: {len(context_content)} Zeichen")

        except Exception as e:
            print(f"⚠️ PUBLIC API - Qdrant-Suche Fehler: {str(e)}")
            # Fallback: Weiter ohne Kontext

        # Messages Array für GPT erstellen
        system_message = SYSTEM_PROMPTS["PUBLIC"]
        if context_content:
            system_message += f"\n\nVerwende die folgenden Informationen als Kontext für deine Antwort:\n\n{context_content}"

        messages = [{"role": "system", "content": system_message}]

        # History hinzufügen (falls vorhanden)
        for msg in history:
            if isinstance(msg, dict) and "role" in msg and "content" in msg:
                if msg["role"] in ["user", "assistant"]:
                    messages.append({
                        "role": msg["role"],
                        "content": str(msg["content"])
                    })

        # Aktuelle Benutzerfrage hinzufügen
        messages.append({"role": "user", "content": user_prompt})

        print(f"💬 PUBLIC API - Gesamt Messages: {len(messages)}")
        print(f"📄 PUBLIC API - Kontext verwendet: {'Ja' if context_content else 'Nein'}")

        # GPT-Anfrage erstellen (gestreamt)
        stream = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=0.7,
            max_tokens=1500,
            stream=True
        )

        # Variable to collect the full response for chat history
        full_response = []

        @stream_with_context
        def generate():
            """Streamt die Antwort von OpenAI."""
            try:
                for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        full_response.append(content)
                        yield content
                
                # Save chat history after streaming is complete
                try:
                    answer_text = ''.join(full_response)
                    chat_history_entry = ChatHistory(
                        user_id=None,  # NULL for public endpoint
                        prompt=user_prompt,
                        answer=answer_text,
                        persona='PUBLIC'
                    )
                    db.session.add(chat_history_entry)
                    db.session.commit()
                    print(f"✅ PUBLIC API - Chat history saved for public user")
                except Exception as e:
                    print(f"⚠️ PUBLIC API - Error saving chat history: {str(e)}")
                    # Don't fail the request if chat history saving fails
                    
            except Exception as e:
                print(f"❌ PUBLIC API - Fehler beim Streamen: {str(e)}")
                # Don't expose internal error details
                yield "An error occurred while processing your request."


        print("✅ PUBLIC API - Streaming-Antwort wird generiert...")

        # Erfolgreiche Antwort als Stream zurückgeben
        return Response(generate(), mimetype='text/plain; charset=utf-8')

    except Exception as e:
        print(f"❌ PUBLIC API - Fehler: {str(e)}")
        print(f"❌ PUBLIC API - Traceback: {traceback.format_exc()}")

        # Don't expose internal error details to prevent information disclosure
        return jsonify({
            'error': 'An internal error occurred while processing your request. Please try again later.'
        }), 500

