"""
Startup script for PostgreSQL-based Auto RFP platform.
This script sets up the database and starts the FastAPI server.
"""

import asyncio
import os
import sys
from pathlib import Path

def install_requirements():
    """Install required packages."""
    print("Installing PostgreSQL requirements...")
    
    required_packages = [
        "psycopg2-binary",
        "asyncpg", 
        "python-magic",
        "python-magic-bin"  # For Windows
    ]
    
    for package in required_packages:
        try:
            if package == "python-magic-bin" and sys.platform != "win32":
                continue  # Skip on non-Windows
                
            __import__(package.replace("-", "_"))
            print(f"✓ {package} is already installed")
        except ImportError:
            print(f"Installing {package}...")
            os.system(f"{sys.executable} -m pip install {package}")

async def setup_database():
    """Set up the PostgreSQL database."""
    print("\n=== Setting up PostgreSQL Database ===")
    
    try:
        # Import setup script
        from setup_postgresql_database import PostgreSQLDatabaseSetup
        
        setup = PostgreSQLDatabaseSetup()
        await setup.setup_complete_database()
        
        print("✓ Database setup completed successfully!")
        return True
        
    except Exception as e:
        print(f"✗ Database setup failed: {e}")
        return False

def start_server():
    """Start the FastAPI server."""
    print("\n=== Starting FastAPI Server ===")
    
    try:
        import uvicorn
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except Exception as e:
        print(f"✗ Server startup failed: {e}")

async def main():
    """Main startup function."""
    print("🚀 Starting Auto RFP Platform with PostgreSQL")
    print("=" * 50)
    
    # Check if we're in the correct directory
    if not Path("main.py").exists():
        print("❌ Error: Please run this script from the backend directory")
        print("   cd backend && python start_postgresql.py")
        return
    
    # Install requirements
    install_requirements()
    
    # Set up database
    database_ready = await setup_database()
    
    if not database_ready:
        print("❌ Cannot start server without database")
        return
    
    # Create storage directories
    print("\n=== Setting up File Storage ===")
    storage_dirs = [
        "storage",
        "storage/documents", 
        "storage/temp",
        "storage/exports"
    ]
    
    for dir_path in storage_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"✓ Created directory: {dir_path}")
    
    print("\n✅ Setup complete!")
    print("\n📊 Access points:")
    print("   • API Server: http://localhost:8000")
    print("   • API Documentation: http://localhost:8000/docs")
    print("   • Frontend: http://localhost:4200 (if running)")
    
    print("\n🔗 Database Connection:")
    database_url = os.getenv("DATABASE_URL", "Not configured")
    if database_url != "Not configured":
        # Hide credentials for security
        safe_url = database_url.split('@')[1] if '@' in database_url else database_url
        print(f"   • PostgreSQL: ...@{safe_url}")
    
    print("\n💾 File Storage:")
    print(f"   • Local Storage: {Path('storage').absolute()}")
    
    print("\n🚀 Starting server...")
    start_server()

if __name__ == "__main__":
    asyncio.run(main())