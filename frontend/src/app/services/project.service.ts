import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, BehaviorSubject } from 'rxjs';
import { map, tap } from 'rxjs/operators';
import {
  Project,
  ProjectCreate,
  Document,
  Question,
  ProjectStats,
  ProjectIndex,
  ApiResponse,
} from '../models';

@Injectable({
  providedIn: 'root',
})
export class ProjectService {
  private baseUrl = 'http://localhost:8000';
  private currentProjectSubject = new BehaviorSubject<Project | null>(null);
  public currentProject$ = this.currentProjectSubject.asObservable();

  constructor(private http: HttpClient) {}

  // Project CRUD operations
  createProject(project: ProjectCreate): Observable<Project> {
    return this.http.post<Project>(`${this.baseUrl}/projects`, project);
  }

  getProjects(organizationId?: string): Observable<Project[]> {
    let params = new HttpParams();
    if (organizationId) {
      params = params.set('organization_id', organizationId);
    }

    return this.http.get<Project[]>(`${this.baseUrl}/projects`, { params });
  }

  getProject(projectId: string, includeRelations = false): Observable<Project> {
    let params = new HttpParams();
    if (includeRelations) {
      params = params.set('include_relations', 'true');
    }

    const url = `${this.baseUrl}/projects/${projectId}`;
    console.log('ProjectService.getProject() - URL:', url);
    console.log('ProjectService.getProject() - baseUrl:', this.baseUrl);
    console.log('ProjectService.getProject() - projectId:', projectId);

    return this.http
      .get<Project>(url, { params })
      .pipe(tap((project) => this.setCurrentProject(project)));
  }

  updateProject(
    projectId: string,
    updates: Partial<Project>
  ): Observable<Project> {
    return this.http
      .put<Project>(`${this.baseUrl}/projects/${projectId}`, updates)
      .pipe(tap((project) => this.setCurrentProject(project)));
  }

  deleteProject(projectId: string): Observable<ApiResponse<any>> {
    return this.http
      .delete<ApiResponse<any>>(`${this.baseUrl}/projects/${projectId}`)
      .pipe(
        tap(() => {
          if (this.currentProjectSubject.value?.id === projectId) {
            this.setCurrentProject(null);
          }
        })
      );
  }

  getProjectStats(projectId: string): Observable<ProjectStats> {
    return this.http.get<ProjectStats>(
      `${this.baseUrl}/projects/${projectId}/stats`
    );
  }

  // Document management
  uploadDocument(
    projectId: string,
    file: File,
    name?: string
  ): Observable<Document> {
    const formData = new FormData();
    formData.append('file', file);
    if (name) {
      formData.append('name', name);
    }

    return this.http.post<Document>(
      `${this.baseUrl}/projects/${projectId}/documents`,
      formData
    );
  }

  getProjectDocuments(projectId: string): Observable<Document[]> {
    return this.http.get<Document[]>(
      `${this.baseUrl}/projects/${projectId}/documents`
    );
  }

  getDocument(documentId: string): Observable<Document> {
    return this.http.get<Document>(`${this.baseUrl}/documents/${documentId}`);
  }

  updateDocumentStatus(
    documentId: string,
    status: string
  ): Observable<ApiResponse<any>> {
    const formData = new FormData();
    formData.append('status', status);

    return this.http.put<ApiResponse<any>>(
      `${this.baseUrl}/documents/${documentId}/status`,
      formData
    );
  }

  deleteDocument(documentId: string): Observable<ApiResponse<any>> {
    return this.http.delete<ApiResponse<any>>(
      `${this.baseUrl}/documents/${documentId}`
    );
  }

  // Question management
  getProjectQuestions(projectId: string): Observable<Question[]> {
    return this.http.get<Question[]>(
      `${this.baseUrl}/projects/${projectId}/questions`
    );
  }

  getQuestionsBySection(
    projectId: string
  ): Observable<{ sections: Record<string, Question[]> }> {
    return this.http.get<{ sections: Record<string, Question[]> }>(
      `${this.baseUrl}/projects/${projectId}/questions/by-section`
    );
  }

  getQuestion(questionId: string): Observable<Question> {
    return this.http.get<Question>(`${this.baseUrl}/questions/${questionId}`);
  }

  getQuestionAnswer(questionId: string): Observable<any> {
    return this.http.get<any>(`${this.baseUrl}/questions/${questionId}/answer`);
  }

  getProjectAnswers(projectId: string): Observable<{ answers: any }> {
    return this.http.get<{ answers: any }>(
      `${this.baseUrl}/projects/${projectId}/answers`
    );
  }

  deleteAnswer(answerId: string): Observable<ApiResponse<any>> {
    return this.http.delete<ApiResponse<any>>(
      `${this.baseUrl}/answers/${answerId}`
    );
  }

  extractQuestions(request: { document_id: string; project_id: string }): Observable<any> {
    return this.http.post<any>(
      `${this.baseUrl}/ai/extract-questions`,
      request
    );
  }

  // Project Index management (LlamaCloud integration)
  addProjectIndex(
    projectId: string,
    indexId: string,
    indexName: string
  ): Observable<ApiResponse<ProjectIndex>> {
    const formData = new FormData();
    formData.append('index_id', indexId);
    formData.append('index_name', indexName);

    return this.http.post<ApiResponse<ProjectIndex>>(
      `${this.baseUrl}/projects/${projectId}/indexes`,
      formData
    );
  }

  getProjectIndexes(projectId: string): Observable<ProjectIndex[]> {
    return this.http.get<ProjectIndex[]>(
      `${this.baseUrl}/projects/${projectId}/indexes`
    );
  }

  removeProjectIndex(
    projectId: string,
    indexId: string
  ): Observable<ApiResponse<any>> {
    return this.http.delete<ApiResponse<any>>(
      `${this.baseUrl}/projects/${projectId}/indexes/${indexId}`
    );
  }

  // Current project management
  setCurrentProject(project: Project | null): void {
    this.currentProjectSubject.next(project);
    if (project) {
      localStorage.setItem('currentProject', JSON.stringify(project));
    } else {
      localStorage.removeItem('currentProject');
    }
  }

  getCurrentProject(): Project | null {
    const stored = localStorage.getItem('currentProject');
    if (stored && !this.currentProjectSubject.value) {
      const project = JSON.parse(stored);
      this.currentProjectSubject.next(project);
      return project;
    }
    return this.currentProjectSubject.value;
  }

  // Utility methods
  formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes';

    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  isDocumentProcessable(fileType: string): boolean {
    const supportedTypes = [
      'application/pdf',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      'application/vnd.openxmlformats-officedocument.presentationml.presentation',
      'text/plain',
    ];
    return supportedTypes.includes(fileType);
  }

  getDocumentIcon(fileType: string): string {
    switch (fileType) {
      case 'application/pdf':
        return 'picture_as_pdf';
      case 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
        return 'description';
      case 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':
        return 'table_chart';
      case 'application/vnd.openxmlformats-officedocument.presentationml.presentation':
        return 'slideshow';
      case 'text/plain':
        return 'text_snippet';
      default:
        return 'insert_drive_file';
    }
  }

  calculateCompletionPercentage(stats: ProjectStats): number {
    if (stats.total_questions === 0) return 0;
    return Math.round((stats.answered_questions / stats.total_questions) * 100);
  }

  getProjectStatusColor(completionRate: number): string {
    if (completionRate === 0) return 'warn';
    if (completionRate < 50) return 'accent';
    if (completionRate < 100) return 'primary';
    return 'primary';
  }

  getProjectStatusText(completionRate: number): string {
    if (completionRate === 0) return 'Not Started';
    if (completionRate < 50) return 'In Progress';
    if (completionRate < 100) return 'Almost Complete';
    return 'Complete';
  }
}
