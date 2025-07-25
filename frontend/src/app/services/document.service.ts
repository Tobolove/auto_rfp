import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders, HttpEventType } from '@angular/common/http';
import { Observable, BehaviorSubject } from 'rxjs';
import { map, tap } from 'rxjs/operators';
import { Document, ExtractQuestionsRequest, ExtractQuestionsResponse } from '../models';

export interface UploadProgress {
  documentId: string;
  progress: number;
  status: 'uploading' | 'processing' | 'completed' | 'error';
  message?: string;
}

@Injectable({
  providedIn: 'root'
})
export class DocumentService {
  private baseUrl = 'http://localhost:8000';
  private uploadProgressSubject = new BehaviorSubject<UploadProgress[]>([]);
  
  uploadProgress$ = this.uploadProgressSubject.asObservable();

  constructor(private http: HttpClient) {}

  /**
   * Upload a document to a project
   */
  uploadDocument(projectId: string, formData: FormData): Observable<Document> {
    const url = `${this.baseUrl}/projects/${projectId}/documents`;
    
    return this.http.post<Document>(url, formData, {
      reportProgress: true,
      observe: 'events'
    }).pipe(
      map(event => {
        if (event.type === HttpEventType.UploadProgress) {
          const progress = Math.round(100 * event.loaded / (event.total || 1));
          this.updateUploadProgress(projectId, progress, 'uploading');
        } else if (event.type === HttpEventType.Response) {
          this.updateUploadProgress(projectId, 100, 'completed');
          return event.body as Document;
        }
        return null;
      }),
      tap(result => {
        if (result) {
          this.updateUploadProgress(result.id, 100, 'completed');
        }
      })
    ) as Observable<Document>;
  }

  /**
   * Get all documents for a project
   */
  getProjectDocuments(projectId: string): Observable<Document[]> {
    const url = `${this.baseUrl}/projects/${projectId}/documents`;
    return this.http.get<Document[]>(url);
  }

  /**
   * Get a specific document by ID
   */
  getDocument(documentId: string): Observable<Document> {
    const url = `${this.baseUrl}/documents/${documentId}`;
    return this.http.get<Document>(url);
  }

  /**
   * Update document status
   */
  updateDocumentStatus(documentId: string, status: string): Observable<any> {
    const url = `${this.baseUrl}/documents/${documentId}/status`;
    const formData = new FormData();
    formData.append('status', status);
    
    return this.http.put(url, formData);
  }

  /**
   * Delete a document
   */
  deleteDocument(documentId: string): Observable<any> {
    const url = `${this.baseUrl}/documents/${documentId}`;
    return this.http.delete(url);
  }

  /**
   * Extract questions from a document using AI
   */
  extractQuestions(request: ExtractQuestionsRequest): Observable<ExtractQuestionsResponse> {
    const url = `${this.baseUrl}/ai/extract-questions`;
    return this.http.post<ExtractQuestionsResponse>(url, request).pipe(
      tap(() => {
        this.updateUploadProgress(request.document_id, 100, 'processing', 'Extracting questions...');
      })
    );
  }

  /**
   * Process multiple documents for question extraction
   */
  processDocuments(projectId: string, documentIds: string[]): Observable<any> {
    const requests = documentIds.map(documentId => 
      this.extractQuestions({
        document_id: documentId,
        document_name: '',
        content: '',
        project_id: projectId
      })
    );

    return new Observable(observer => {
      Promise.all(requests.map(req => req.toPromise()))
        .then(results => {
          observer.next(results);
          observer.complete();
        })
        .catch(error => observer.error(error));
    });
  }

  /**
   * Upload and process document in one step
   */
  uploadAndProcessDocument(
    projectId: string, 
    file: File, 
    extractQuestions: boolean = true
  ): Observable<{ document: Document; questions?: ExtractQuestionsResponse }> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('name', file.name);

    return new Observable(observer => {
      // First upload the document
      this.uploadDocument(projectId, formData).subscribe({
        next: (document) => {
          if (!extractQuestions) {
            observer.next({ document });
            observer.complete();
            return;
          }

          // Then extract questions if requested
          this.updateUploadProgress(document.id, 50, 'processing', 'Extracting questions...');
          
          const extractRequest: ExtractQuestionsRequest = {
            document_id: document.id,
            document_name: document.name,
            content: '',
            project_id: projectId
          };

          this.extractQuestions(extractRequest).subscribe({
            next: (questions) => {
              this.updateUploadProgress(document.id, 100, 'completed', 'Processing complete');
              observer.next({ document, questions });
              observer.complete();
            },
            error: (error) => {
              this.updateUploadProgress(document.id, 100, 'error', 'Question extraction failed');
              // Still return the document even if question extraction fails
              observer.next({ document });
              observer.complete();
            }
          });
        },
        error: (error) => {
          this.updateUploadProgress(projectId, 0, 'error', 'Upload failed');
          observer.error(error);
        }
      });
    });
  }

  /**
   * Get supported file types and their descriptions
   */
  getSupportedFileTypes(): { [key: string]: string } {
    return {
      'pdf': 'PDF Documents',
      'docx': 'Microsoft Word Documents',
      'txt': 'Plain Text Files',
      'md': 'Markdown Files'
    };
  }

  /**
   * Validate file before upload
   */
  validateFile(file: File): { valid: boolean; error?: string } {
    const maxSize = 100 * 1024 * 1024; // 100MB
    const allowedExtensions = ['pdf', 'docx', 'txt', 'md'];
    
    // Check file size
    if (file.size > maxSize) {
      return {
        valid: false,
        error: `File size exceeds 100MB limit. Current size: ${this.formatFileSize(file.size)}`
      };
    }

    // Check file extension
    const extension = file.name.split('.').pop()?.toLowerCase();
    if (!extension || !allowedExtensions.includes(extension)) {
      return {
        valid: false,
        error: `File type not supported. Allowed types: ${allowedExtensions.join(', ')}`
      };
    }

    return { valid: true };
  }

  /**
   * Format file size for display
   */
  formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  /**
   * Get file type icon
   */
  getFileTypeIcon(fileName: string): string {
    const extension = fileName.split('.').pop()?.toLowerCase();
    
    switch (extension) {
      case 'pdf': return 'picture_as_pdf';
      case 'docx': return 'description';
      case 'txt': return 'text_snippet';
      case 'md': return 'code';
      default: return 'insert_drive_file';
    }
  }

  /**
   * Update upload progress tracking
   */
  private updateUploadProgress(
    documentId: string, 
    progress: number, 
    status: UploadProgress['status'],
    message?: string
  ): void {
    const currentProgress = this.uploadProgressSubject.value;
    const existingIndex = currentProgress.findIndex(p => p.documentId === documentId);
    
    const progressUpdate: UploadProgress = {
      documentId,
      progress,
      status,
      message
    };

    if (existingIndex >= 0) {
      currentProgress[existingIndex] = progressUpdate;
    } else {
      currentProgress.push(progressUpdate);
    }

    this.uploadProgressSubject.next([...currentProgress]);

    // Clean up completed/error progress after delay
    if (status === 'completed' || status === 'error') {
      setTimeout(() => {
        const updatedProgress = this.uploadProgressSubject.value.filter(
          p => p.documentId !== documentId
        );
        this.uploadProgressSubject.next(updatedProgress);
      }, 5000);
    }
  }

  /**
   * Clear all upload progress
   */
  clearUploadProgress(): void {
    this.uploadProgressSubject.next([]);
  }

  /**
   * Get upload progress for a specific document
   */
  getUploadProgress(documentId: string): UploadProgress | undefined {
    return this.uploadProgressSubject.value.find(p => p.documentId === documentId);
  }

  /**
   * Check if document is currently being processed
   */
  isDocumentProcessing(documentId: string): boolean {
    const progress = this.getUploadProgress(documentId);
    return progress?.status === 'uploading' || progress?.status === 'processing';
  }

  /**
   * Batch upload multiple files
   */
  batchUploadDocuments(
    projectId: string, 
    files: File[], 
    extractQuestions: boolean = true
  ): Observable<{ document: Document; questions?: ExtractQuestionsResponse }[]> {
    const uploads = files.map(file => 
      this.uploadAndProcessDocument(projectId, file, extractQuestions)
    );

    return new Observable(observer => {
      Promise.all(uploads.map(upload => upload.toPromise()))
        .then(results => {
          observer.next(results);
          observer.complete();
        })
        .catch(error => observer.error(error));
    });
  }

  /**
   * Get document processing statistics
   */
  getProcessingStats(projectId: string): Observable<any> {
    const url = `${this.baseUrl}/projects/${projectId}/stats`;
    return this.http.get(url);
  }

  /**
   * Reprocess a document (re-extract questions)
   */
  reprocessDocument(documentId: string, projectId: string): Observable<ExtractQuestionsResponse> {
    return this.extractQuestions({
      document_id: documentId,
      document_name: '',
      content: '',
      project_id: projectId
    });
  }
}