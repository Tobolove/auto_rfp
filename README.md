# Auto RFP - AI-Powered RFP Response Platform

An advanced AI-powered platform for automating RFP (Request for Proposal) response generation with comprehensive document processing, question extraction, and intelligent answer generation capabilities.

## 🏗️ Architecture

### Backend (Python FastAPI)
- **Framework**: FastAPI with async/await support
- **AI Integration**: Azure OpenAI + Azure Document Intelligence
- **Vector Database**: Qdrant for semantic search
- **Database**: SQLite (development) / PostgreSQL (production)
- **Document Processing**: Azure Document Intelligence + custom parsers
- **Authentication**: JWT-based authentication system

### Frontend (Angular 19)
- **Framework**: Angular 19 with standalone components
- **UI Library**: Angular Material
- **State Management**: RxJS observables + services
- **Routing**: Multi-level routing for organizations/projects
- **Real-time Updates**: WebSocket integration (planned)

### Key Features
- **Multi-tenant Architecture**: Organization-based data isolation
- **Intelligent Document Processing**: AI-powered question extraction
- **Semantic Search**: Vector-based document retrieval
- **Response Generation**: Context-aware AI response generation
- **Collaborative Workflow**: Team-based RFP management
- **Export Capabilities**: Multiple export formats (PDF, DOCX, JSON)

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 18+
- Azure OpenAI account (optional for AI features)
- Qdrant instance (optional for vector search)

### Backend Setup

1. **Clone and navigate to backend**:
```bash
git clone <repository-url>
cd backend
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. **Setup database**:
```bash
python setup_enhanced_database.py
```

5. **Start backend server**:
```bash
# Windows PowerShell (recommended)
.\start_backend.ps1

# Windows batch
start_backend.bat

# Direct Python
python -m uvicorn main:app --reload --port 8000
```

### Frontend Setup

1. **Navigate to frontend**:
```bash
cd frontend
```

2. **Install dependencies**:
```bash
npm install
```

3. **Start development server**:
```bash
npm start
# Runs on http://localhost:4200
```

### Alternative Startup Commands

**Backend**:
```bash
cd backend
python -m uvicorn main:app --reload --port 8000
```

**Frontend**:
```bash
cd frontend
ng serve --port 4200
```

## 📋 API Documentation

Once the backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key API Endpoints

#### Organizations
- `POST /organizations` - Create organization
- `GET /organizations` - List organizations
- `GET /organizations/{id}` - Get organization details
- `PUT /organizations/{id}` - Update organization

#### Projects
- `POST /projects` - Create RFP project
- `GET /projects` - List projects
- `POST /projects/{id}/documents` - Upload documents
- `GET /projects/{id}/questions` - Get extracted questions

#### AI Processing
- `POST /ai/extract-questions` - Extract questions from documents
- `POST /ai/generate-response` - Generate AI responses
- `POST /ai/multi-step-response` - Multi-step AI processing

#### Vector Search
- `POST /qdrant/search/documents` - Semantic document search
- `POST /qdrant/quotes/index` - Index RFP quotes
- `POST /qdrant/search/quotes` - Search similar quotes

## 🛠️ Development

### Testing

**Backend Tests**:
```bash
cd backend
pip install -r requirements-test.txt
pytest
```

**Frontend Tests**:
```bash
cd frontend
npm test
```

### Code Quality

**Backend Linting**:
```bash
cd backend
flake8 .
black .
```

**Frontend Linting**:
```bash
cd frontend
ng lint
```

### Database Management

**Reset Database**:
```bash
cd backend
python setup_enhanced_database.py
```

**Run Migrations** (when available):
```bash
cd backend
python migrate_database.py
```

## 🔧 Configuration

### Environment Variables

#### Backend (.env)
```env
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True

# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your-endpoint.cognitiveservices.azure.com/
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4

# Qdrant Vector Database
QDRANT_URL=https://your-qdrant-cluster.cloud.qdrant.io
QDRANT_API_KEY=your-qdrant-api-key

# Azure Document Intelligence
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://your-endpoint.cognitiveservices.azure.com/
AZURE_DOCUMENT_INTELLIGENCE_KEY=your-key

# Database
DATABASE_URL=sqlite:///./data/auto_rfp_local.db
```

#### Frontend (environment.ts)
```typescript
export const environment = {
  production: false,
  apiUrl: 'http://localhost:8000',
  // Add other configuration as needed
};
```

## 📊 Project Structure

```
auto_rfp/
├── backend/                 # Python FastAPI backend
│   ├── services/           # Business logic services
│   ├── models.py          # Pydantic data models
│   ├── main.py           # FastAPI application
│   ├── database_config.py # Database configuration
│   ├── sql/              # SQL schema files
│   └── tests/            # Backend tests
├── frontend/              # Angular frontend
│   ├── src/app/
│   │   ├── components/   # Angular components
│   │   ├── services/     # Angular services
│   │   └── models/       # TypeScript interfaces
│   └── ...
└── README.md
```

## 🔐 Security

- JWT-based authentication
- Organization-based access control
- API key encryption for external services
- Input validation and sanitization
- CORS configuration for development

## 🚀 Deployment

### Production Deployment

**Backend**:
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

**Frontend**:
```bash
cd frontend
npm run build
# Serve dist/ folder with web server
```

### Docker Support (Planned)
```bash
docker-compose up -d
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Workflow

1. **Backend Development**:
   - Follow FastAPI best practices
   - Add tests for new endpoints
   - Update API documentation
   - Ensure proper error handling

2. **Frontend Development**:
   - Use Angular standalone components
   - Follow Material Design guidelines
   - Implement proper TypeScript typing
   - Add unit tests for components

## 📈 Performance

- **Backend**: Async/await throughout for high concurrency
- **Frontend**: OnPush change detection + lazy loading
- **Database**: Optimized indexes and query patterns
- **Vector Search**: Efficient Qdrant integration
- **Caching**: Redis integration (planned)

## 🐛 Troubleshooting

### Common Issues

**Backend won't start**:
- Check Python version (3.9+ required)
- Verify all dependencies installed
- Check database connectivity
- Review .env configuration

**Frontend won't start**:
- Check Node.js version (18+ required)
- Clear npm cache: `npm cache clean --force`
- Delete node_modules and reinstall

**Database issues**:
- Run database setup: `python setup_enhanced_database.py`
- Check file permissions in data/ directory
- Verify SQLite installation

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- OpenAI for GPT models
- Microsoft Azure for AI services
- Qdrant for vector database
- FastAPI and Angular communities

## 📞 Support

For support and questions:
- Create an issue in the GitHub repository
- Check the documentation at `/docs` endpoint
- Review API documentation at `/docs` and `/redoc`

---

**Note**: This is a comprehensive AI-powered RFP platform designed for enterprise use. Ensure proper configuration of AI services and security settings before production deployment.