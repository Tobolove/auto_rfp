"""
Simplified reference document endpoints without heavy dependencies
"""
from fastapi import APIRouter, HTTPException, File, UploadFile, Form
from typing import Optional
import uuid
import os
from datetime import datetime

router = APIRouter()

@router.get("/reference-documents/types")
async def get_document_types():
    """Get available document types and tags for the frontend."""
    return {
        "document_types": [
            {"value": "company_profile", "label": "Company Profile"},
            {"value": "case_study", "label": "Case Study"},
            {"value": "technical_specs", "label": "Technical Specs"},
            {"value": "certifications", "label": "Certifications"},
            {"value": "team_bios", "label": "Team Bios"},
            {"value": "pricing_templates", "label": "Pricing Templates"},
            {"value": "methodology", "label": "Methodology"},
            {"value": "partnerships", "label": "Partnerships"},
            {"value": "awards", "label": "Awards"},
            {"value": "other", "label": "Other"}
        ],
        "industry_tags": [
            {"value": "healthcare", "label": "Healthcare"},
            {"value": "finance", "label": "Finance"},
            {"value": "technology", "label": "Technology"},
            {"value": "manufacturing", "label": "Manufacturing"},
            {"value": "government", "label": "Government"},
            {"value": "education", "label": "Education"},
            {"value": "retail", "label": "Retail"},
            {"value": "energy", "label": "Energy"},
            {"value": "telecommunications", "label": "Telecommunications"},
            {"value": "automotive", "label": "Automotive"},
            {"value": "aerospace", "label": "Aerospace"},
            {"value": "other", "label": "Other"}
        ],
        "capability_tags": [
            {"value": "cloud_migration", "label": "Cloud Migration"},
            {"value": "data_analytics", "label": "Data Analytics"},
            {"value": "cybersecurity", "label": "Cybersecurity"},
            {"value": "ai_ml", "label": "AI/ML"},
            {"value": "integration", "label": "Integration"},
            {"value": "mobile_development", "label": "Mobile Development"},
            {"value": "web_development", "label": "Web Development"},
            {"value": "database_management", "label": "Database Management"},
            {"value": "devops", "label": "DevOps"},
            {"value": "consulting", "label": "Consulting"},
            {"value": "project_management", "label": "Project Management"},
            {"value": "quality_assurance", "label": "Quality Assurance"},
            {"value": "ui_ux_design", "label": "UI/UX Design"},
            {"value": "blockchain", "label": "Blockchain"},
            {"value": "iot", "label": "IoT"},
            {"value": "other", "label": "Other"}
        ],
        "project_sizes": [
            {"value": "small", "label": "Small"},
            {"value": "medium", "label": "Medium"},
            {"value": "large", "label": "Large"},
            {"value": "enterprise", "label": "Enterprise"}
        ],
        "geographic_scopes": [
            {"value": "local", "label": "Local"},
            {"value": "regional", "label": "Regional"},
            {"value": "national", "label": "National"},
            {"value": "international", "label": "International"}
        ],
        "confidence_levels": [
            {"value": "high", "label": "High"},
            {"value": "medium", "label": "Medium"},
            {"value": "low", "label": "Low"}
        ]
    }

# DISABLED: Simulation upload endpoint - replaced by real Qdrant upload in main.py
# @router.post("/organizations/{organization_id}/reference-documents/upload")
# async def upload_reference_document(
#     organization_id: str,
#     file: UploadFile = File(...),
#     document_type: str = Form(...),
#     industry_tags: str = Form(default=""),
#     capability_tags: str = Form(default=""),
#     project_size: str = Form(default=""),
#     geographic_scope: str = Form(default=""),
#     confidence_level: str = Form(default="medium"),
#     custom_tags: str = Form(default=""),
#     description: str = Form(default=""),
#     keywords: str = Form(default="")
# ):
#     """Upload a reference document (simplified version)."""
#     try:
#         # For now, just simulate success
#         document_id = str(uuid.uuid4())
#         
#         print(f"📤 Simulated upload for organization {organization_id}:")
#         print(f"   📄 File: {file.filename}")
#         print(f"   🏷️  Type: {document_type}")
#         print(f"   🏭 Industries: {industry_tags}")
#         print(f"   💪 Capabilities: {capability_tags}")
#         print(f"   📊 Size: {project_size}")
#         print(f"   🌍 Scope: {geographic_scope}")
#         
#         return {
#             "success": True,
#             "document_id": document_id,
#             "message": "Document upload simulated successfully! Full processing will be available soon.",
#             "metadata": {
#                 "filename": file.filename,
#                 "document_type": document_type,
#                 "industry_tags": industry_tags.split(",") if industry_tags else [],
#                 "capability_tags": capability_tags.split(",") if capability_tags else [],
#                 "project_size": project_size,
#                 "geographic_scope": geographic_scope,
#                 "confidence_level": confidence_level,
#                 "organization_id": organization_id,
#                 "upload_date": datetime.now().isoformat()
#             }
#         }
#         
#     except Exception as e:
#         print(f"❌ Error in upload simulation: {e}")
#         raise HTTPException(status_code=500, detail=f"Upload simulation failed: {str(e)}")

@router.get("/organizations/{organization_id}/reference-documents")
async def get_organization_reference_documents(
    organization_id: str,
    document_type: Optional[str] = None,
    is_active: bool = True
):
    """Get reference documents for an organization (simplified version)."""
    try:
        # For now, return empty list but with success structure
        print(f"📋 Getting documents for organization {organization_id}")
        
        return {
            "success": True,
            "documents": []  # Empty for now, will be populated when full service is available
        }
        
    except Exception as e:
        print(f"❌ Error getting documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/organizations/{organization_id}/reference-documents/{document_id}")
async def delete_reference_document(organization_id: str, document_id: str):
    """Delete a reference document (simplified version)."""
    try:
        print(f"🗑️  Simulated delete document {document_id} for organization {organization_id}")
        
        return {
            "success": True,
            "message": "Document deletion simulated successfully!"
        }
        
    except Exception as e:
        print(f"❌ Error in delete simulation: {e}")
        raise HTTPException(status_code=500, detail=str(e))