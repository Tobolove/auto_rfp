# AutoRFP Tool - Umfassende Dokumentation

## 🎯 **Überblick**

AutoRFP ist ein intelligentes AI-gestütztes System zur automatisierten Bearbeitung von RFP (Request for Proposal) Dokumenten. Das Tool kombiniert moderne Web-Technologien mit AI-Services und Vector-Datenbanken für eine intelligente Dokumentenverarbeitung.

## 🏗️ **System-Architektur**

### **Backend (Python FastAPI)**

- **API Server**: `http://localhost:8000`
- **Vector Database**: Qdrant Cloud für semantische Suche
- **AI Services**: Azure OpenAI (GPT-4) für Textgenerierung
- **Dokumentenverarbeitung**: Azure Document Intelligence
- **Datenbank**: SQLite (entwicklung) / PostgreSQL (produktion)

### **Frontend (Angular 19)**

- **Web Interface**: `http://localhost:4200`
- **UI Framework**: Angular Material Design
- **Architektur**: Standalone Components
- **Responsive Design**: Desktop und Mobile optimiert

## 🔄 **Workflow & Funktionsweise**

### **1. Organisation erstellen**

```
Startseite → Organizations → "Create Organization" → Formular ausfüllen
```

- **Name**: Organisation benennen
- **Slug**: Automatisch generiert (URL-freundlich)
- **Beschreibung**: Optional

### **2. Projekt anlegen**

```
Organisation auswählen → Projects → "Create Project" → Projektdetails
```

- **Projektname** und Beschreibung
- **Verknüpfung** mit Organisation
- **Dokumenten-Management** Setup

### **3. RFP-Dokumente hochladen**

```
Projekt → Upload Documents → PDF/Word-Dateien → Automatische Verarbeitung
```

- **Unterstützte Formate**: PDF, DOCX, DOC
- **Azure Document Intelligence**: Textextraktion
- **Strukturierte Speicherung** in Datenbank

### **4. Fragen extrahieren**

```
Dokumente → Extract Questions → AI-Analyse → Strukturierte Fragenliste
```

- **AI-gestützte Analyse** des Dokumenteninhalts
- **Automatische Kategorisierung** nach Themen
- **Fragenerkennung** und -strukturierung

### **5. Antworten generieren**

```
Fragen → Generate Response → Vector-Suche → AI-Antwortgenerierung
```

- **Qdrant Vector Search**: Ähnliche Antworten finden
- **Azure OpenAI**: Neue Antworten generieren
- **Kontext-bewusste** Antwortgenerierung

## 🧠 **Intelligente Funktionen**

### **Vector Database (Qdrant)**

```python
# Quote Collection System
await qdrant_service.create_quote_collection()
similar_quotes = await qdrant_service.search_similar_quotes(question_text)
```

- **Semantische Suche** in vorherigen Antworten
- **Machine Learning Embeddings** für Textvergleich
- **Kontinuierliches Lernen** aus neuen Projekten

### **AI-Powered Response Generation**

```python
# Multi-Step Response Generation
response = await ai_service.generate_multi_step_response(
    question=question_text,
    context=similar_quotes,
    organization_style=org_preferences
)
```

- **Azure OpenAI GPT-4** Integration
- **Kontext-bewusste** Antwortgenerierung
- **Firmenstil-Anpassung**

## 📊 **Datenfluss-Diagramm**

```
RFP-Dokument (PDF/DOCX)
         ↓
Azure Document Intelligence
         ↓
Text-Extraktion & Strukturierung
         ↓
AI-Fragen-Extraktion (GPT-4)
         ↓
Qdrant Vector Search (ähnliche Antworten)
         ↓
Azure OpenAI Response Generation
         ↓
Quality Check & Speicherung
         ↓
Benutzer-Interface (Angular)
```

## 🛠️ **API-Endpoints**

### **Organisationen**

```http
POST   /organizations              # Organisation erstellen
GET    /organizations              # Alle Organisationen
GET    /organizations/{id}         # Organisation by ID
PUT    /organizations/{id}         # Organisation updaten
DELETE /organizations/{id}         # Organisation löschen
```

### **Projekte**

```http
POST   /projects                   # Projekt erstellen
GET    /projects                   # Alle Projekte
GET    /projects/{id}              # Projekt by ID
PUT    /projects/{id}              # Projekt updaten
DELETE /projects/{id}              # Projekt löschen
GET    /projects/{id}/stats        # Projekt-Statistiken
```

### **Dokumente & AI**

```http
POST   /documents/upload           # RFP-Dokumente hochladen
POST   /ai/extract-questions       # Fragen extrahieren
POST   /ai/generate-response       # AI-Antworten generieren
POST   /ai/multi-step-response     # Mehrstufige Antwortgenerierung
```

### **Qdrant Vector Database**

```http
POST   /qdrant/quote-collection/initialize  # Quote-Collection setup
GET    /qdrant/connection/test              # Verbindungstest
POST   /qdrant/search-quotes               # Ähnliche Antworten suchen
POST   /qdrant/index-quote                 # Neue Antwort indexieren
```

### **System-Monitoring**

```http
GET    /health                     # System-Health-Check
GET    /                          # API-Status
```

## 💻 **Technische Implementation**

### **Backend-Services**

#### **OrganizationService**

```typescript
createOrganization(organization: OrganizationCreate, ownerEmail: string): Observable<Organization>
getOrganizations(userEmail?: string): Observable<Organization[]>
setCurrentOrganization(organization: Organization | null): void
```

#### **ProjectService**

```python
async def create_project(project_data: ProjectCreate) -> Project
async def get_projects_by_organization(org_id: UUID) -> List[Project]
async def get_project_stats(project_id: UUID) -> ProjectStats
```

#### **AIService**

```python
async def extract_questions(document_content: str) -> ExtractQuestionsResponse
async def generate_response(request: GenerateResponseRequest) -> GenerateResponseResponse
async def multi_step_response(request: MultiStepRequest) -> MultiStepResponse
```

#### **QdrantService**

```python
async def create_quote_collection() -> bool
async def search_similar_quotes(query: str, limit: int = 5) -> List[Quote]
async def index_rfp_quote(quote_data: QuoteData) -> bool
```

### **Frontend-Komponenten**

#### **OrganizationsComponent**

```typescript
// Hauptkomponente für Organisationsverwaltung
loadOrganizations(): void
createNewOrganization(): void
selectOrganization(organization: Organization): void
```

#### **CreateOrganizationComponent**

```typescript
// Formular für neue Organisationen
onSubmit(): void
onNameChange(): void  // Auto-Slug-Generation
getErrorMessage(fieldName: string): string
```

## 🚀 **Deployment & Setup**

### **Backend starten**

```bash
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### **Frontend starten**

```bash
cd frontend
npm install
npm start
```

### **Umgebungsvariablen (.env)**

```env
# Azure Services
AZURE_OPENAI_API_KEY=your_azure_openai_key
AZURE_OPENAI_ENDPOINT=your_azure_endpoint
AZURE_DOCUMENT_INTELLIGENCE_KEY=your_doc_intelligence_key
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=your_doc_endpoint

# Qdrant Vector Database
QDRANT_URL=your_qdrant_cloud_url
QDRANT_API_KEY=your_qdrant_api_key

# Optional: LlamaCloud (legacy)
LLAMACLOUD_API_KEY=your_llamacloud_key
```

## 🧪 **Testing-Workflow**

### **1. System-Health überprüfen**

```bash
curl http://localhost:8000/health
```

### **2. Organisation erstellen**

1. Browser: `http://localhost:4200/organizations`
2. "Create Organization" klicken
3. Formular ausfüllen
4. Submit

### **3. Vollständiger Workflow testen**

1. ✅ Organisation erstellen
2. ✅ Projekt anlegen
3. ✅ RFP-Dokument hochladen
4. ✅ Fragen extrahieren
5. ✅ AI-Antworten generieren

## 🔧 **Entwickler-Tools**

### **API-Dokumentation**

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### **Debug-Endpoints**

```http
GET /qdrant/connection/test         # Qdrant-Verbindung testen
GET /health                         # Alle Services prüfen
POST /qdrant/quote-collection/initialize  # Vector DB setup
```

## 📈 **Performance & Skalierung**

### **Vector Database Optimierung**

- **Qdrant Cloud**: Hochperformante semantische Suche
- **Embedding Models**: sentence-transformers/all-MiniLM-L6-v2
- **Collection Management**: Automatische Indexierung

### **AI-Service Optimierung**

- **Azure OpenAI**: GPT-4 für beste Qualität
- **Prompt Engineering**: Optimierte Prompts für RFP-Antworten
- **Caching**: Wiederverwendung ähnlicher Antworten

## 🔒 **Sicherheit & Compliance**

### **Authentifizierung**

- **Placeholder**: `user@example.com` (Development)
- **Production**: Azure AD / OAuth2 Integration geplant

### **Datenschutz**

- **Lokale Speicherung**: Sensitive Daten verschlüsselt
- **API-Sicherheit**: CORS, HTTPS in Produktion
- **Audit-Trail**: Vollständige Aktivitätsverfolgung

## 🚨 **Troubleshooting**

### **Häufige Probleme**

#### **Backend startet nicht**

```bash
# Python-Path-Probleme
python -c "import sys; print(sys.path)"
# Lösung: config_path.py wird automatisch geladen
```

#### **Frontend-Compilation-Fehler**

```bash
# Angular standalone components
npm install @angular/material @angular/cdk
# Lösung: Alle Material-Module sind konfiguriert
```

#### **Qdrant-Verbindung fehlschlägt**

```bash
curl http://localhost:8000/qdrant/connection/test
# Lösung: API-Key und URL in .env prüfen
```

## 📚 **Weitere Ressourcen**

- **Angular Material**: https://material.angular.io/
- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **Qdrant Documentation**: https://qdrant.tech/documentation/
- **Azure OpenAI**: https://azure.microsoft.com/services/cognitive-services/openai-service/

---

**Entwickelt mit ❤️ für intelligente RFP-Bearbeitung**

_Letzte Aktualisierung: 24. Juli 2025_
