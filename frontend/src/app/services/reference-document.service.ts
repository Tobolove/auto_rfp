import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { environment } from '../../environments/environment';

export interface DocumentUploadResponse {
  success: boolean;
  document_id: string;
  message: string;
  metadata?: any;
  vector_id?: string;
}

export interface DocumentTypesResponse {
  document_types: Array<{ value: string; label: string }>;
  industry_tags: Array<{ value: string; label: string }>;
  capability_tags: Array<{ value: string; label: string }>;
  project_sizes: Array<{ value: string; label: string }>;
  geographic_scopes: Array<{ value: string; label: string }>;
  confidence_levels: Array<{ value: string; label: string }>;
}

export interface OrganizationDocumentsResponse {
  success: boolean;
  documents: Array<{
    id: string;
    filename: string;
    original_name: string;
    document_type: string;
    industry_tags: string;
    capability_tags: string;
    project_size?: string;
    geographic_scope?: string;
    organization_id: string;
    confidence_level: string;
    custom_tags: string;
    description?: string;
    keywords: string;
    file_path: string;
    content_length: number;
    upload_date: string;
    is_active: boolean;
    created_at: string;
    updated_at: string;
  }>;
}

export interface DeleteDocumentResponse {
  success: boolean;
  message: string;
}

export interface SearchTestResponse {
  success: boolean;
  query: string;
  results: any;
  total_chunks: number;
  error?: string;
}

@Injectable({
  providedIn: 'root'
})
export class ReferenceDocumentService {
  private baseUrl = environment.apiUrl || 'http://localhost:8000';

  constructor(private http: HttpClient) { }

  /**
   * Upload a reference document to the organization's knowledge base
   */
  uploadDocument(organizationId: string, formData: FormData): Observable<DocumentUploadResponse> {
    return this.http.post<DocumentUploadResponse>(
      `${this.baseUrl}/organizations/${organizationId}/reference-documents/upload`,
      formData
    );
  }

  /**
   * Get all reference documents for an organization
   */
  getOrganizationDocuments(
    organizationId: string, 
    documentType?: string, 
    isActive: boolean = true
  ): Observable<OrganizationDocumentsResponse> {
    let params = `?is_active=${isActive}`;
    if (documentType) {
      params += `&document_type=${encodeURIComponent(documentType)}`;
    }
    
    return this.http.get<OrganizationDocumentsResponse>(
      `${this.baseUrl}/organizations/${organizationId}/reference-documents${params}`
    );
  }

  /**
   * Delete a reference document
   */
  deleteDocument(organizationId: string, documentId: string): Observable<DeleteDocumentResponse> {
    return this.http.delete<DeleteDocumentResponse>(
      `${this.baseUrl}/organizations/${organizationId}/reference-documents/${documentId}`
    );
  }

  /**
   * Get available document types and tags
   */
  getDocumentTypes(): Observable<DocumentTypesResponse> {
    return this.http.get<DocumentTypesResponse>(
      `${this.baseUrl}/reference-documents/types`
    ).pipe(
      // Add error handling
      catchError(error => {
        console.error('API Error, using debug endpoint:', error);
        return this.http.get<DocumentTypesResponse>(
          `${this.baseUrl}/debug/reference-types`
        );
      })
    );
  }

  /**
   * Test search functionality for reference documents
   */
  testDocumentSearch(query: string, organizationId?: string): Observable<SearchTestResponse> {
    const body = {
      query: query,
      organization_id: organizationId || ''
    };
    
    return this.http.post<SearchTestResponse>(
      `${this.baseUrl}/reference-documents/test-search`,
      body
    );
  }

  /**
   * Get document statistics for an organization
   */
  getDocumentStats(organizationId: string): Observable<any> {
    return this.http.get<any>(
      `${this.baseUrl}/organizations/${organizationId}/reference-documents/stats`
    );
  }

  /**
   * Update document metadata
   */
  updateDocumentMetadata(
    organizationId: string, 
    documentId: string, 
    metadata: any
  ): Observable<any> {
    return this.http.put<any>(
      `${this.baseUrl}/organizations/${organizationId}/reference-documents/${documentId}`,
      metadata
    );
  }

  /**
   * Bulk delete documents
   */
  bulkDeleteDocuments(organizationId: string, documentIds: string[]): Observable<any> {
    return this.http.post<any>(
      `${this.baseUrl}/organizations/${organizationId}/reference-documents/bulk-delete`,
      { document_ids: documentIds }
    );
  }

  /**
   * Search documents by filters
   */
  searchDocuments(
    organizationId: string,
    filters: {
      document_types?: string[];
      industry_tags?: string[];
      capability_tags?: string[];
      project_sizes?: string[];
      geographic_scopes?: string[];
      confidence_levels?: string[];
      keywords?: string[];
      search_query?: string;
    }
  ): Observable<OrganizationDocumentsResponse> {
    return this.http.post<OrganizationDocumentsResponse>(
      `${this.baseUrl}/organizations/${organizationId}/reference-documents/search`,
      filters
    );
  }

  /**
   * Get document content preview
   */
  getDocumentPreview(organizationId: string, documentId: string): Observable<any> {
    return this.http.get<any>(
      `${this.baseUrl}/organizations/${organizationId}/reference-documents/${documentId}/preview`
    );
  }

  /**
   * Test RAG system with specific document filters
   */
  testRAGWithFilters(
    query: string,
    organizationId: string,
    filters?: {
      document_types?: string[];
      industry_tags?: string[];
      capability_tags?: string[];
    }
  ): Observable<any> {
    const body = {
      query: query,
      organization_id: organizationId,
      filters: filters || {}
    };
    
    return this.http.post<any>(
      `${this.baseUrl}/ai/test-rag-filtered`,
      body
    );
  }

  /**
   * Generate response using specific reference documents
   */
  generateResponseWithDocuments(
    question: string,
    organizationId: string,
    documentIds?: string[],
    filters?: any
  ): Observable<any> {
    const body = {
      question: question,
      organization_id: organizationId,
      document_ids: documentIds || [],
      filters: filters || {},
      use_reference_documents: true
    };
    
    return this.http.post<any>(
      `${this.baseUrl}/ai/generate-response-with-references`,
      body
    );
  }
}