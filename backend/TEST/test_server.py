#!/usr/bin/env python3
"""
Minimal FastAPI test server to check organization creation.
"""

import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import config_path

from fastapi import FastAPI, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional

from models import Organization, OrganizationCreate, User, UserCreate
from services.organization_service import organization_service

app = FastAPI(title="Test AutoRFP API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Test AutoRFP API is running", "status": "healthy"}

@app.post("/organizations", response_model=Organization, status_code=201)
async def create_organization(
    name: str = Form(...),
    slug: str = Form(...), 
    description: Optional[str] = Form(None),
    owner_email: str = Form(...)
):
    """Create a new organization with the specified user as owner."""
    try:
        # Create OrganizationCreate model from form data
        organization = OrganizationCreate(
            name=name,
            slug=slug,
            description=description
        )
        
        # Get or create user
        user = await organization_service.get_user_by_email(owner_email)
        if not user:
            user = await organization_service.create_user(UserCreate(email=owner_email))
        
        # Create organization
        org = await organization_service.create_organization(organization, user.id)
        return org
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/organizations")
async def get_organizations(user_email: Optional[str] = None):
    """Get all organizations, optionally filtered by user membership."""
    try:
        if user_email:
            orgs = await organization_service.get_organizations_for_user(user_email)
        else:
            orgs = await organization_service.get_all_organizations()
        return orgs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)