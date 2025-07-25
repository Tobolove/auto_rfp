import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, BehaviorSubject } from 'rxjs';
import { map, tap } from 'rxjs/operators';
import {
  Organization,
  OrganizationCreate,
  OrganizationMember,
  ApiResponse,
} from '../models';

@Injectable({
  providedIn: 'root',
})
export class OrganizationService {
  private baseUrl = 'http://localhost:8000';
  private currentOrganizationSubject = new BehaviorSubject<Organization | null>(
    null
  );
  public currentOrganization$ = this.currentOrganizationSubject.asObservable();

  constructor(private http: HttpClient) {}

  // Organization CRUD operations
  createOrganization(
    organization: OrganizationCreate,
    ownerEmail: string
  ): Observable<Organization> {
    const formData = new FormData();
    formData.append('name', organization.name);
    formData.append('slug', organization.slug);
    if (organization.description) {
      formData.append('description', organization.description);
    }
    formData.append('owner_email', ownerEmail);

    return this.http.post<Organization>(
      `${this.baseUrl}/organizations`,
      formData
    );
  }

  getOrganizations(userEmail?: string): Observable<Organization[]> {
    let params = new HttpParams();
    if (userEmail) {
      params = params.set('user_email', userEmail);
    }

    const url = `${this.baseUrl}/organizations`;
    console.log('OrganizationService.getOrganizations() - URL:', url);
    console.log('OrganizationService.getOrganizations() - userEmail:', userEmail);
    console.log('OrganizationService.getOrganizations() - params:', params.toString());

    return this.http.get<Organization[]>(url, {
      params,
    });
  }

  getOrganization(
    orgId: string,
    includeRelations = false
  ): Observable<Organization> {
    let params = new HttpParams();
    if (includeRelations) {
      params = params.set('include_relations', 'true');
    }

    return this.http
      .get<Organization>(`${this.baseUrl}/organizations/${orgId}`, { params })
      .pipe(tap((org) => this.setCurrentOrganization(org)));
  }

  updateOrganization(
    orgId: string,
    updates: Partial<Organization>
  ): Observable<Organization> {
    return this.http
      .put<Organization>(`${this.baseUrl}/organizations/${orgId}`, updates)
      .pipe(tap((org) => this.setCurrentOrganization(org)));
  }

  deleteOrganization(orgId: string): Observable<ApiResponse<any>> {
    return this.http
      .delete<ApiResponse<any>>(`${this.baseUrl}/organizations/${orgId}`)
      .pipe(
        tap(() => {
          if (this.currentOrganizationSubject.value?.id === orgId) {
            this.setCurrentOrganization(null);
          }
        })
      );
  }

  // Organization membership management
  addMemberToOrganization(
    orgId: string,
    userEmail: string,
    role: 'owner' | 'admin' | 'member' = 'member'
  ): Observable<ApiResponse<any>> {
    const formData = new FormData();
    formData.append('user_email', userEmail);
    formData.append('role', role);

    return this.http.post<ApiResponse<any>>(
      `${this.baseUrl}/organizations/${orgId}/members`,
      formData
    );
  }

  getOrganizationMembers(
    orgId: string
  ): Observable<{ members: OrganizationMember[] }> {
    return this.http.get<{ members: OrganizationMember[] }>(
      `${this.baseUrl}/organizations/${orgId}/members`
    );
  }

  updateMemberRole(
    orgId: string,
    userId: string,
    newRole: 'owner' | 'admin' | 'member'
  ): Observable<ApiResponse<any>> {
    const formData = new FormData();
    formData.append('new_role', newRole);

    return this.http.put<ApiResponse<any>>(
      `${this.baseUrl}/organizations/${orgId}/members/${userId}/role`,
      formData
    );
  }

  removeMemberFromOrganization(
    orgId: string,
    userId: string
  ): Observable<ApiResponse<any>> {
    return this.http.delete<ApiResponse<any>>(
      `${this.baseUrl}/organizations/${orgId}/members/${userId}`
    );
  }

  // LlamaCloud integration
  connectLlamaCloud(
    orgId: string,
    projectId: string,
    projectName: string,
    orgName?: string
  ): Observable<ApiResponse<Organization>> {
    const request = {
      organization_id: orgId,
      project_id: projectId,
      project_name: projectName,
      llama_cloud_org_name: orgName,
    };

    return this.http.post<ApiResponse<Organization>>(
      `${this.baseUrl}/organizations/${orgId}/llamacloud/connect`,
      request
    );
  }

  disconnectLlamaCloud(orgId: string): Observable<ApiResponse<Organization>> {
    return this.http.post<ApiResponse<Organization>>(
      `${this.baseUrl}/organizations/${orgId}/llamacloud/disconnect`,
      {}
    );
  }

  // Current organization management
  setCurrentOrganization(organization: Organization | null): void {
    this.currentOrganizationSubject.next(organization);
    if (organization) {
      localStorage.setItem('currentOrganization', JSON.stringify(organization));
    } else {
      localStorage.removeItem('currentOrganization');
    }
  }

  getCurrentOrganization(): Organization | null {
    const stored = localStorage.getItem('currentOrganization');
    if (stored && !this.currentOrganizationSubject.value) {
      const org = JSON.parse(stored);
      this.currentOrganizationSubject.next(org);
      return org;
    }
    return this.currentOrganizationSubject.value;
  }

  // Utility methods
  generateSlug(name: string): string {
    return name
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/(^-|-$)/g, '');
  }

  validateSlug(slug: string): Observable<boolean> {
    // Simple client-side validation for demo
    // In production, you'd want to check against the server
    const isValid = /^[a-z0-9-]+$/.test(slug) && slug.length >= 3;
    return new Observable((observer) => {
      observer.next(isValid);
      observer.complete();
    });
  }
}
