# 🚀 AutoRFP Backend API

Eine vollständige FastAPI-basierte Backend-Lösung für automatisierte RFP-Antworten mit Azure Integration und Qdrant Vector Database.

## ✨ Features

- **🏢 Organization Management** - Multi-tenant Architektur
- **📄 Project & Document Management** - RFP-Projektmanagement
- **🤖 AI-powered Processing** - Automatische Fragen-Extraktion und Antwort-Generierung
- **🔍 Vector Search** - Semantische Suche mit Qdrant Vector Database
- **☁️ Azure Integration** - Document Intelligence, OpenAI, Storage
- **📊 Quote Collection** - Vollständige RFP-Angebotsverwaltung

## 🏗️ Architektur

```
backend/
├── main.py                 # FastAPI App mit 40+ Endpoints
├── models.py              # Pydantic Datenmodelle
├── config_path.py         # Python Path Konfiguration
├── requirements.txt       # Python Dependencies
├── services/              # Business Logic Layer
│   ├── organization_service.py
│   ├── project_service.py
│   ├── ai_service.py
│   ├── qdrant_vector_service.py
│   └── qdrant_service_factory.py
└── startup_scripts/       # Server-Start Skripte
    ├── start_backend.bat
    ├── start_backend.ps1
    ├── test_imports.py
    └── test_api.py
```

## 🚀 Quick Start

### 1. Dependencies installieren

```bash
pip install -r requirements.txt
```

### 2. Environment Variables konfigurieren

Erstellen Sie eine `.env` Datei mit:

```env
# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your-endpoint.cognitiveservices.azure.com/
AZURE_OPENAI_API_KEY=your-api-key

# Qdrant Vector Database
QDRANT_URL=https://your-qdrant-cluster.cloud.qdrant.io
QDRANT_API_KEY=your-qdrant-api-key

# Azure Document Intelligence
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://your-endpoint.cognitiveservices.azure.com/
AZURE_DOCUMENT_INTELLIGENCE_KEY=your-key

# Azure Storage
AZURE_STORAGE_CONNECTION_STRING=your-connection-string
```

### 3. Server starten

**Windows (PowerShell) - Empfohlen:**

```powershell
.\start_backend.ps1
```

**Windows (Batch):**

```cmd
start_backend.bat
```

**Python direkt:**

```bash
python -m uvicorn main:app --reload --port 8000
```

### 4. API testen

```bash
python test_api.py
```

## 📚 API Endpoints

### 🏢 Organizations

- `POST /organizations` - Organisation erstellen
- `GET /organizations` - Organisationen auflisten
- `GET /organizations/{id}` - Organisation abrufen
- `PUT /organizations/{id}` - Organisation aktualisieren

### 📁 Projects

- `POST /projects` - Projekt erstellen
- `GET /projects` - Projekte auflisten
- `POST /projects/{id}/documents` - Dokument hochladen
- `GET /projects/{id}/questions` - Fragen extrahieren

### 🤖 AI Processing

- `POST /ai/extract-questions` - Fragen aus RFP extrahieren
- `POST /ai/generate-response` - AI-Antwort generieren
- `POST /ai/multi-step-process` - Multi-Step AI Processing

### 🔍 Qdrant Vector Search

- `POST /qdrant/quote-collection/initialize` - Quote Collection initialisieren
- `POST /qdrant/quotes/index` - RFP Quote indizieren
- `POST /qdrant/search/quotes` - Semantische Quote-Suche
- `GET /qdrant/quote-collection/stats` - Collection Statistiken

### 🔧 System

- `GET /` - API Root
- `GET /health` - Health Check
- `GET /docs` - Swagger UI Dokumentation
- `GET /redoc` - ReDoc Dokumentation

## 🔧 Konfiguration

### Python Path

Das Backend verwendet automatische Python Path-Konfiguration via `config_path.py`:

```python
import config_path  # Konfiguriert Python imports automatisch
```

### OpenMP Warning Fix

Falls OpenMP-Warnungen auftreten, wird automatisch gesetzt:

```bash
export KMP_DUPLICATE_LIB_OK=TRUE
```

### Qdrant Collections

Das System erstellt automatisch:

- **Organization Collections**: `org_{organization_id}`
- **Quote Collection**: `quote_collection` (global)

## 🧪 Testing

### Import Tests

```bash
python test_imports.py
```

### API Tests

```bash
python test_api.py
```

### Health Check

```bash
curl http://localhost:8000/health
```

## 🌐 URLs nach dem Start

- **API Root**: http://localhost:8000
- **Swagger Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 🔍 Troubleshooting

### Import Fehler

```bash
# Test imports
python test_imports.py

# Pfad prüfen
python -c "import sys; print(sys.path)"
```

### Connection Errors

```bash
# Qdrant testen
curl http://localhost:8000/qdrant/connection/test

# Health Check
curl http://localhost:8000/health
```

### Dependencies

```bash
# Alle installieren
pip install -r requirements.txt

# Einzeln installieren
pip install fastapi uvicorn qdrant-client sentence-transformers
```

## 📦 Dependencies

### Core Framework

- `fastapi` - Web Framework
- `uvicorn` - ASGI Server
- `pydantic` - Data Validation

### AI & ML

- `openai` - OpenAI API Client
- `qdrant-client` - Vector Database
- `sentence-transformers` - Local Embeddings
- `numpy` - Scientific Computing

### Azure Services

- `azure-ai-documentintelligence` - Document Processing
- `azure-storage-blob` - File Storage
- `azure-identity` - Authentication

## 🚀 Deployment

### Development

```bash
uvicorn main:app --reload --port 8000
```

### Production

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Docker (kommend)

```dockerfile
FROM python:3.11
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

**✅ Status: Vollständig implementiert und funktionsfähig!**

Das Backend startet erfolgreich und alle Imports funktionieren korrekt. 🎉
