# SETUP Directory

This directory contains all database setup and initialization scripts for the RFP AI backend.

## 📂 Setup Scripts

### Database Setup Scripts
- `setup_database.py` - Main database setup script
- `setup_database_simple.py` - Simplified database setup
- `setup_enhanced_database.py` - Enhanced database with additional features
- `setup_local_database.py` - Local SQLite database setup
- `setup_postgresql_database.py` - PostgreSQL-specific database setup

## 🗄️ Database Types Supported

### PostgreSQL (Recommended)
```bash
python SETUP/setup_postgresql_database.py
```
- Full-featured production database
- Supports all RFP AI features
- Best performance and scalability

### SQLite (Development)
```bash
python SETUP/setup_local_database.py
```
- Local file-based database
- Good for development and testing
- Simpler setup process

### Enhanced Setup
```bash
python SETUP/setup_enhanced_database.py
```
- Additional features and optimizations
- Extended schema with performance improvements
- Recommended for production deployments

## 🚀 Quick Setup

### For Development
1. Use SQLite for quick local development:
   ```bash
   python SETUP/setup_local_database.py
   ```

### For Production
1. Set up PostgreSQL database
2. Configure `.env` file with database connection
3. Run enhanced setup:
   ```bash
   python SETUP/setup_enhanced_database.py
   ```

## 📋 Prerequisites

### Environment Variables
Make sure your `.env` file contains:
```env
DATABASE_URL=postgresql://user:password@host:port/database
# or for SQLite:
DATABASE_URL=sqlite:///./data/auto_rfp_local.db
```

### Dependencies
- PostgreSQL (for production)
- Python packages from `requirements.txt`
- Proper network access to database server

## 🔧 Troubleshooting

### Connection Issues
- Verify database server is running
- Check firewall settings
- Validate connection string format

### Permission Issues
- Ensure database user has CREATE privileges
- Check file permissions for SQLite databases

### Schema Issues
- Drop existing tables if needed
- Run simple setup first, then enhanced
- Check SQL scripts in `../sql/` directory

## 📝 Schema Information

The database schema includes:
- **Organizations** - Multi-tenant organization management
- **Projects** - RFP project containers
- **Documents** - Uploaded RFP documents
- **Questions** - Extracted questions from RFPs
- **Answers** - AI-generated responses
- **Sources** - Reference source tracking