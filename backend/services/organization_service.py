"""
Organization service for managing organizations and users.
"""
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from models import (
    Organization, OrganizationCreate, OrganizationUpdate,
    User, UserCreate, OrganizationUser, UserRole
)
from database_config import database, get_table_name

class OrganizationService:
    """Service for organization and user management operations."""
    
    def __init__(self):
        pass  # Database operations don't need instance variables
    
    # Organization operations
    async def create_organization(self, org_data: OrganizationCreate, owner_user_id: UUID) -> Organization:
        """Create a new organization with the specified user as owner."""
        org = Organization(
            **org_data.model_dump(),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Insert organization into database
        org_table = get_table_name("organizations")
        query = f"""
            INSERT INTO {org_table} (id, name, slug, description, created_at, updated_at)
            VALUES (:id, :name, :slug, :description, :created_at, :updated_at)
        """
        try:
            print(f"Database connected: {database.is_connected}")
            print(f"About to insert organization: {org.name}")
            await database.execute(query, {
                "id": str(org.id),
                "name": org.name,
                "slug": org.slug,
                "description": org.description,
                "created_at": org.created_at,
                "updated_at": org.updated_at
            })
            print(f"Successfully inserted organization: {org.name} with ID: {org.id}")
        except Exception as e:
            print(f"Error inserting organization: {e}")
            import traceback
            traceback.print_exc()
            raise
        
        # Add user as owner
        org_user = OrganizationUser(
            user_id=owner_user_id,
            organization_id=org.id,
            role=UserRole.OWNER,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Insert organization user relationship
        org_users_table = get_table_name("organization_users")
        user_query = f"""
            INSERT INTO {org_users_table} (id, user_id, organization_id, role, created_at, updated_at)
            VALUES (:id, :user_id, :organization_id, :role, :created_at, :updated_at)
        """
        await database.execute(user_query, {
            "id": str(org_user.id),
            "user_id": str(org_user.user_id),
            "organization_id": str(org_user.organization_id),
            "role": org_user.role.value,
            "created_at": org_user.created_at,
            "updated_at": org_user.updated_at
        })
        
        return org
    
    async def get_organizations(self, user_id: Optional[UUID] = None) -> List[Organization]:
        """Get all organizations, optionally filtered by user membership."""
        org_table = get_table_name("organizations")
        
        if user_id:
            # Get organizations where user is a member
            org_users_table = get_table_name("organization_users")
            query = f"""
                SELECT o.* FROM {org_table} o
                JOIN {org_users_table} ou ON o.id = ou.organization_id
                WHERE ou.user_id = :user_id
                ORDER BY o.created_at DESC
            """
            rows = await database.fetch_all(query, {"user_id": str(user_id)})
        else:
            # Get all organizations
            query = f"SELECT * FROM {org_table} ORDER BY created_at DESC"
            rows = await database.fetch_all(query)
        
        return [Organization(**dict(row)) for row in rows]
    
    async def get_organization(self, org_id: UUID, include_relations: bool = False) -> Optional[Organization]:
        """Get organization by ID."""
        org_table = get_table_name("organizations")
        query = f"SELECT * FROM {org_table} WHERE id = :org_id"
        row = await database.fetch_one(query, {"org_id": str(org_id)})
        
        if not row:
            return None
            
        return Organization(**dict(row))
    
    async def update_organization(self, org_id: UUID, update_data: OrganizationUpdate) -> Optional[Organization]:
        """Update organization."""
        org = await self.get_organization(org_id)
        if not org:
            return None
        
        # Update fields
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(org, field, value)
        
        org.updated_at = datetime.now()
        return org
    
    async def delete_organization(self, org_id: UUID) -> bool:
        """Delete organization and all related data."""
        org = await self.get_organization(org_id)
        if not org:
            return False
        
        # Remove organization users first (foreign key constraint)
        org_users_table = get_table_name("organization_users")
        await database.execute(
            f"DELETE FROM {org_users_table} WHERE organization_id = :org_id",
            {"org_id": str(org_id)}
        )
        
        # Remove organization
        org_table = get_table_name("organizations")
        await database.execute(
            f"DELETE FROM {org_table} WHERE id = :org_id",
            {"org_id": str(org_id)}
        )
        
        return True
    
    # User operations
    async def create_user(self, user_data: UserCreate) -> User:
        """Create a new user."""
        user = User(
            **user_data.model_dump(),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Insert user into database
        users_table = get_table_name("users")
        query = f"""
            INSERT INTO {users_table} (id, email, name, created_at, updated_at)
            VALUES (:id, :email, :name, :created_at, :updated_at)
        """
        await database.execute(query, {
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "created_at": user.created_at,
            "updated_at": user.updated_at
        })
        
        return user
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        users_table = get_table_name("users")
        query = f"SELECT * FROM {users_table} WHERE email = :email"
        row = await database.fetch_one(query, {"email": email})
        
        if not row:
            return None
            
        return User(**dict(row))
    
    async def get_user(self, user_id: UUID) -> Optional[User]:
        """Get user by ID."""
        users_table = get_table_name("users")
        query = f"SELECT * FROM {users_table} WHERE id = :user_id"
        row = await database.fetch_one(query, {"user_id": str(user_id)})
        
        if not row:
            return None
            
        return User(**dict(row))
    
    # Organization membership operations
    async def add_user_to_organization(
        self, 
        user_id: UUID, 
        org_id: UUID, 
        role: UserRole = UserRole.MEMBER
    ) -> OrganizationUser:
        """Add user to organization with specified role."""
        org_user = OrganizationUser(
            user_id=user_id,
            organization_id=org_id,
            role=role,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Insert into database
        org_users_table = get_table_name("organization_users")
        query = f"""
            INSERT INTO {org_users_table} (id, user_id, organization_id, role, created_at, updated_at)
            VALUES (:id, :user_id, :organization_id, :role, :created_at, :updated_at)
        """
        await database.execute(query, {
            "id": str(org_user.id),
            "user_id": str(org_user.user_id),
            "organization_id": str(org_user.organization_id),
            "role": org_user.role.value,
            "created_at": org_user.created_at,
            "updated_at": org_user.updated_at
        })
        
        return org_user
    
    async def get_organization_members(self, org_id: UUID) -> List[dict]:
        """Get all members of an organization with user details."""
        org_users_table = get_table_name("organization_users")
        users_table = get_table_name("users")
        
        query = f"""
            SELECT u.*, ou.role, ou.created_at as joined_at
            FROM {users_table} u
            JOIN {org_users_table} ou ON u.id = ou.user_id
            WHERE ou.organization_id = :org_id
            ORDER BY ou.created_at
        """
        rows = await database.fetch_all(query, {"org_id": str(org_id)})
        
        members = []
        for row in rows:
            row_dict = dict(row)
            user_data = {k: v for k, v in row_dict.items() if k not in ['role', 'joined_at']}
            user = User(**user_data)
            
            members.append({
                "user": user,
                "role": UserRole(row['role']),
                "joined_at": row['joined_at']
            })
        
        return members
    
    async def update_user_role(
        self, 
        user_id: UUID, 
        org_id: UUID, 
        new_role: UserRole
    ) -> Optional[OrganizationUser]:
        """Update user's role in organization."""
        org_users_table = get_table_name("organization_users")
        
        # Update the role in database
        update_query = f"""
            UPDATE {org_users_table} 
            SET role = :new_role, updated_at = :updated_at
            WHERE user_id = :user_id AND organization_id = :org_id
        """
        result = await database.execute(update_query, {
            "new_role": new_role.value,
            "updated_at": datetime.now(),
            "user_id": str(user_id),
            "org_id": str(org_id)
        })
        
        # Return updated record if successful
        if result:
            query = f"""
                SELECT * FROM {org_users_table} 
                WHERE user_id = :user_id AND organization_id = :org_id
            """
            row = await database.fetch_one(query, {
                "user_id": str(user_id),
                "org_id": str(org_id)
            })
            if row:
                row_dict = dict(row)
                row_dict['role'] = UserRole(row_dict['role'])
                return OrganizationUser(**row_dict)
        
        return None
    
    async def remove_user_from_organization(self, user_id: UUID, org_id: UUID) -> bool:
        """Remove user from organization."""
        org_users_table = get_table_name("organization_users")
        
        # Delete from database
        delete_query = f"""
            DELETE FROM {org_users_table} 
            WHERE user_id = :user_id AND organization_id = :org_id
        """
        result = await database.execute(delete_query, {
            "user_id": str(user_id),
            "org_id": str(org_id)
        })
        
        return result > 0
    
    # LlamaCloud integration
    async def connect_llamacloud(
        self, 
        org_id: UUID, 
        project_id: str, 
        project_name: str,
        org_name: Optional[str] = None
    ) -> Optional[Organization]:
        """Connect organization to LlamaCloud project."""
        org = await self.get_organization(org_id)
        if not org:
            return None
        
        org.llama_cloud_project_id = project_id
        org.llama_cloud_project_name = project_name
        org.llama_cloud_org_name = org_name
        org.llama_cloud_connected_at = datetime.now()
        org.updated_at = datetime.now()
        
        return org
    
    async def disconnect_llamacloud(self, org_id: UUID) -> Optional[Organization]:
        """Disconnect organization from LlamaCloud."""
        org = await self.get_organization(org_id)
        if not org:
            return None
        
        org.llama_cloud_project_id = None
        org.llama_cloud_project_name = None
        org.llama_cloud_org_name = None
        org.llama_cloud_connected_at = None
        org.updated_at = datetime.now()
        
        return org


# Global service instance
organization_service = OrganizationService()
