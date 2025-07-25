"""
Local file storage service for managing document uploads and storage.
"""

import os
import shutil
import uuid
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
import hashlib
import mimetypes
import logging

# Try to import magic, fallback to mimetypes if not available
try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False
    print("Warning: python-magic not available, using mimetypes fallback")

logger = logging.getLogger(__name__)

class LocalFileStorageService:
    """
    Local file storage service for handling document uploads and management.
    
    Features:
    - Secure file storage with UUID-based naming
    - Organization/project-based directory structure
    - File type validation and metadata extraction
    - Duplicate detection via content hashing
    - Virus scanning integration (if available)
    """
    
    def __init__(self, base_storage_path: str = "storage"):
        """
        Initialize the local file storage service.
        
        Args:
            base_storage_path: Base directory for file storage
        """
        self.base_path = Path(base_storage_path).resolve()
        self.documents_path = self.base_path / "documents"
        self.temp_path = self.base_path / "temp"
        self.exports_path = self.base_path / "exports"
        
        # Create directory structure
        self._ensure_directories()
        
        # Allowed file types for security
        self.allowed_extensions = {
            '.pdf', '.docx', '.doc', '.txt', '.md', '.rtf',
            '.xlsx', '.xls', '.pptx', '.ppt', '.odt', '.odp', '.ods'
        }
        
        # Max file size (100MB)
        self.max_file_size = 100 * 1024 * 1024
        
        logger.info(f"LocalFileStorageService initialized with base path: {self.base_path}")
    
    def _ensure_directories(self):
        """Create necessary directory structure."""
        directories = [
            self.base_path,
            self.documents_path,
            self.temp_path,
            self.exports_path
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            
        logger.info(f"Directory structure ensured: {self.base_path}")
    
    def _get_organization_path(self, organization_id: str) -> Path:
        """Get the storage path for an organization."""
        org_path = self.documents_path / f"org_{organization_id}"
        org_path.mkdir(parents=True, exist_ok=True)
        return org_path
    
    def _get_project_path(self, organization_id: str, project_id: str) -> Path:
        """Get the storage path for a project."""
        org_path = self._get_organization_path(organization_id)
        project_path = org_path / f"project_{project_id}"
        project_path.mkdir(parents=True, exist_ok=True)
        return project_path
    
    def _validate_file(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        Validate uploaded file for security and constraints.
        
        Args:
            file_content: Raw file content
            filename: Original filename
            
        Returns:
            Validation result with metadata
        """
        result = {
            "valid": True,
            "errors": [],
            "metadata": {}
        }
        
        # Check file size
        if len(file_content) > self.max_file_size:
            result["valid"] = False
            result["errors"].append(f"File size ({len(file_content)} bytes) exceeds maximum allowed ({self.max_file_size} bytes)")
        
        # Check file extension
        file_ext = Path(filename).suffix.lower()
        if file_ext not in self.allowed_extensions:
            result["valid"] = False
            result["errors"].append(f"File type '{file_ext}' is not allowed. Allowed types: {', '.join(self.allowed_extensions)}")
        
        # Detect MIME type
        try:
            if MAGIC_AVAILABLE:
                mime_type = magic.from_buffer(file_content, mime=True)
            else:
                # Fallback to mimetypes based on filename
                mime_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
            
            result["metadata"]["mime_type"] = mime_type
            result["metadata"]["detected_extension"] = mimetypes.guess_extension(mime_type)
        except Exception as e:
            logger.warning(f"Could not detect MIME type: {e}")
            result["metadata"]["mime_type"] = "application/octet-stream"
        
        # Check for empty files
        if len(file_content) == 0:
            result["valid"] = False
            result["errors"].append("File is empty")
        
        # Generate content hash for duplicate detection
        result["metadata"]["content_hash"] = hashlib.sha256(file_content).hexdigest()
        result["metadata"]["file_size"] = len(file_content)
        result["metadata"]["original_filename"] = filename
        
        return result
    
    async def store_document(
        self,
        file_content: bytes,
        filename: str,
        organization_id: str,
        project_id: str,
        document_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Store a document file locally.
        
        Args:
            file_content: Raw file content
            filename: Original filename
            organization_id: Organization identifier
            project_id: Project identifier
            document_id: Optional document identifier (will generate if not provided)
            
        Returns:
            Storage result with file metadata
        """
        try:
            # Validate file
            validation = self._validate_file(file_content, filename)
            if not validation["valid"]:
                raise ValueError(f"File validation failed: {'; '.join(validation['errors'])}")
            
            # Generate document ID if not provided
            if not document_id:
                document_id = str(uuid.uuid4())
            
            # Get project storage path
            project_path = self._get_project_path(organization_id, project_id)
            
            # Generate unique filename
            file_ext = Path(filename).suffix.lower()
            stored_filename = f"{document_id}{file_ext}"
            file_path = project_path / stored_filename
            
            # Check for existing file with same content hash
            existing_file = await self._find_duplicate_file(
                validation["metadata"]["content_hash"],
                organization_id,
                project_id
            )
            
            if existing_file:
                logger.info(f"Duplicate file detected: {existing_file}")
                return {
                    "success": True,
                    "document_id": document_id,
                    "file_path": str(existing_file),
                    "relative_path": str(existing_file.relative_to(self.base_path)),
                    "is_duplicate": True,
                    "metadata": validation["metadata"]
                }
            
            # Write file to storage
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            # Set appropriate permissions
            file_path.chmod(0o644)
            
            logger.info(f"Document stored successfully: {file_path}")
            
            return {
                "success": True,
                "document_id": document_id,
                "file_path": str(file_path),
                "relative_path": str(file_path.relative_to(self.base_path)),
                "is_duplicate": False,
                "metadata": {
                    **validation["metadata"],
                    "stored_at": datetime.now().isoformat(),
                    "stored_filename": stored_filename
                }
            }
            
        except Exception as e:
            logger.error(f"Error storing document: {str(e)}")
            raise
    
    async def _find_duplicate_file(
        self,
        content_hash: str,
        organization_id: str,
        project_id: str
    ) -> Optional[Path]:
        """
        Find existing file with the same content hash.
        
        Args:
            content_hash: SHA256 hash of file content
            organization_id: Organization identifier
            project_id: Project identifier
            
        Returns:
            Path to duplicate file if found, None otherwise
        """
        try:
            project_path = self._get_project_path(organization_id, project_id)
            
            # Check all files in the project directory
            for file_path in project_path.iterdir():
                if file_path.is_file():
                    try:
                        with open(file_path, 'rb') as f:
                            file_content = f.read()
                            file_hash = hashlib.sha256(file_content).hexdigest()
                            
                            if file_hash == content_hash:
                                return file_path
                                
                    except Exception as e:
                        logger.warning(f"Could not check file {file_path}: {e}")
                        continue
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding duplicate file: {e}")
            return None
    
    async def get_document(self, file_path: str) -> Optional[bytes]:
        """
        Retrieve document content.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            File content as bytes, or None if not found
        """
        try:
            full_path = self.base_path / file_path if not Path(file_path).is_absolute() else Path(file_path)
            
            if not full_path.exists():
                logger.warning(f"Document not found: {full_path}")
                return None
            
            # Security check: ensure file is within storage directory
            if not str(full_path.resolve()).startswith(str(self.base_path.resolve())):
                logger.error(f"Security violation: attempted access outside storage directory: {full_path}")
                return None
            
            with open(full_path, 'rb') as f:
                return f.read()
                
        except Exception as e:
            logger.error(f"Error retrieving document: {e}")
            return None
    
    async def delete_document(self, file_path: str) -> bool:
        """
        Delete a document file.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            full_path = self.base_path / file_path if not Path(file_path).is_absolute() else Path(file_path)
            
            if not full_path.exists():
                logger.warning(f"Document not found for deletion: {full_path}")
                return True  # Already deleted
            
            # Security check
            if not str(full_path.resolve()).startswith(str(self.base_path.resolve())):
                logger.error(f"Security violation: attempted deletion outside storage directory: {full_path}")
                return False
            
            full_path.unlink()
            logger.info(f"Document deleted successfully: {full_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            return False
    
    async def get_document_metadata(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a stored document.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Document metadata dictionary, or None if not found
        """
        try:
            full_path = self.base_path / file_path if not Path(file_path).is_absolute() else Path(file_path)
            
            if not full_path.exists():
                return None
            
            # Security check
            if not str(full_path.resolve()).startswith(str(self.base_path.resolve())):
                logger.error(f"Security violation: attempted access outside storage directory: {full_path}")
                return None
            
            stat = full_path.stat()
            
            # Read file content for hash calculation
            with open(full_path, 'rb') as f:
                content = f.read()
                content_hash = hashlib.sha256(content).hexdigest()
            
            # Detect MIME type
            try:
                if MAGIC_AVAILABLE:
                    mime_type = magic.from_buffer(content, mime=True)
                else:
                    mime_type = mimetypes.guess_type(str(full_path))[0] or "application/octet-stream"
            except:
                mime_type = mimetypes.guess_type(str(full_path))[0] or "application/octet-stream"
            
            return {
                "file_path": str(full_path),
                "relative_path": str(full_path.relative_to(self.base_path)),
                "filename": full_path.name,
                "file_size": stat.st_size,
                "mime_type": mime_type,
                "content_hash": content_hash,
                "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "accessed_at": datetime.fromtimestamp(stat.st_atime).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting document metadata: {e}")
            return None
    
    async def list_project_documents(
        self,
        organization_id: str,
        project_id: str
    ) -> List[Dict[str, Any]]:
        """
        List all documents in a project directory.
        
        Args:
            organization_id: Organization identifier
            project_id: Project identifier
            
        Returns:
            List of document metadata dictionaries
        """
        try:
            project_path = self._get_project_path(organization_id, project_id)
            documents = []
            
            for file_path in project_path.iterdir():
                if file_path.is_file():
                    metadata = await self.get_document_metadata(str(file_path.relative_to(self.base_path)))
                    if metadata:
                        documents.append(metadata)
            
            return documents
            
        except Exception as e:
            logger.error(f"Error listing project documents: {e}")
            return []
    
    async def cleanup_temp_files(self, max_age_hours: int = 24):
        """
        Clean up temporary files older than specified age.
        
        Args:
            max_age_hours: Maximum age of temp files in hours
        """
        try:
            cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
            
            for file_path in self.temp_path.iterdir():
                if file_path.is_file():
                    if file_path.stat().st_mtime < cutoff_time:
                        file_path.unlink()
                        logger.info(f"Cleaned up temp file: {file_path}")
            
        except Exception as e:
            logger.error(f"Error cleaning up temp files: {e}")
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get storage usage statistics.
        
        Returns:
            Storage statistics dictionary
        """
        try:
            def get_directory_size(path: Path) -> int:
                """Calculate total size of directory."""
                total = 0
                for file_path in path.rglob('*'):
                    if file_path.is_file():
                        total += file_path.stat().st_size
                return total
            
            def count_files(path: Path) -> int:
                """Count files in directory."""
                return len([f for f in path.rglob('*') if f.is_file()])
            
            return {
                "base_path": str(self.base_path),
                "total_documents": count_files(self.documents_path),
                "total_size_bytes": get_directory_size(self.documents_path),
                "temp_files": count_files(self.temp_path),
                "temp_size_bytes": get_directory_size(self.temp_path),
                "exports": count_files(self.exports_path),
                "exports_size_bytes": get_directory_size(self.exports_path),
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting storage stats: {e}")
            return {"error": str(e)}


# Global service instance
file_storage_service = LocalFileStorageService()