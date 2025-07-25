import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatSnackBarModule, MatSnackBar } from '@angular/material/snack-bar';
import { MatCardModule } from '@angular/material/card';
import { MatListModule } from '@angular/material/list';
import { ProjectService } from '../../../services/project.service';
import { Document } from '../../../models';

@Component({
  selector: 'app-document-upload',
  standalone: true,
  imports: [
    CommonModule,
    MatButtonModule,
    MatIconModule,
    MatProgressBarModule,
    MatSnackBarModule,
    MatCardModule,
    MatListModule
  ],
  template: `
    <mat-card class="upload-card">
      <mat-card-header>
        <mat-card-title>
          <mat-icon>cloud_upload</mat-icon>
          Upload RFP Documents
        </mat-card-title>
        <mat-card-subtitle>
          Upload PDF, Word, or text documents for AI processing
        </mat-card-subtitle>
      </mat-card-header>
      
      <mat-card-content>
        <!-- File Drop Zone -->
        <div 
          class="drop-zone"
          [class.dragover]="isDragOver"
          (dragover)="onDragOver($event)"
          (dragleave)="onDragLeave($event)"
          (drop)="onFileDrop($event)"
          (click)="fileInput.click()"
        >
          <mat-icon class="upload-icon">cloud_upload</mat-icon>
          <p class="drop-text">
            <strong>Click to upload</strong> or drag and drop files here
          </p>
          <p class="file-types">
            Supports: PDF, DOCX, TXT, MD (Max 100MB)
          </p>
        </div>
        
        <!-- Hidden File Input -->
        <input
          #fileInput
          type="file"
          multiple
          accept=".pdf,.docx,.txt,.md"
          (change)="onFileSelect($event)"
          style="display: none;"
        />
        
        <!-- Upload Progress -->
        <div *ngIf="uploadFiles.length > 0" class="upload-progress">
          <h4>Uploading Files</h4>
          <div *ngFor="let file of uploadFiles" class="file-progress">
            <div class="file-info">
              <mat-icon>description</mat-icon>
              <span class="file-name">{{ file.name }}</span>
              <span class="file-size">({{ formatFileSize(file.size) }})</span>
            </div>
            <mat-progress-bar 
              mode="determinate" 
              [value]="file.progress"
              [color]="file.status === 'error' ? 'warn' : 'primary'"
            ></mat-progress-bar>
            <div class="status-text">
              <span [class]="'status-' + file.status">
                {{ getStatusText(file) }}
              </span>
            </div>
          </div>
        </div>
        
        <!-- Uploaded Documents List -->
        <div *ngIf="documents.length > 0" class="documents-list">
          <h4>Uploaded Documents</h4>
          <mat-list>
            <mat-list-item *ngFor="let doc of documents">
              <mat-icon matListItemIcon [class]="'status-' + doc.status">
                {{ getDocumentIcon(doc) }}
              </mat-icon>
              <div matListItemTitle>{{ doc.name }}</div>
              <div matListItemLine>
                {{ doc.file_type }} • {{ formatFileSize(doc.file_size) }} • 
                {{ doc.status | titlecase }}
              </div>
              <div matListItemMeta>
                <button 
                  mat-icon-button 
                  [disabled]="doc.status === 'processing'"
                  (click)="removeDocument(doc)"
                >
                  <mat-icon>delete</mat-icon>
                </button>
              </div>
            </mat-list-item>
          </mat-list>
        </div>
      </mat-card-content>
      
      <mat-card-actions>
        <button 
          mat-raised-button 
          color="primary" 
          (click)="fileInput.click()"
          [disabled]="isUploading"
        >
          <mat-icon>add</mat-icon>
          Add More Files
        </button>
        
        <button 
          mat-raised-button 
          color="accent"
          (click)="processDocuments()"
          [disabled]="!hasProcessableDocuments || isProcessing"
        >
          <mat-icon>psychology</mat-icon>
          {{ isProcessing ? 'Processing...' : 'Extract Questions' }}
        </button>
      </mat-card-actions>
    </mat-card>
  `,
  styles: [`
    .upload-card {
      max-width: 800px;
      margin: 0 auto;
    }
    
    .drop-zone {
      border: 2px dashed #ccc;
      border-radius: 8px;
      padding: 40px;
      text-align: center;
      cursor: pointer;
      transition: all 0.3s ease;
      margin: 20px 0;
    }
    
    .drop-zone:hover, .drop-zone.dragover {
      border-color: #1976d2;
      background-color: #f5f5f5;
    }
    
    .upload-icon {
      font-size: 48px;
      width: 48px;
      height: 48px;
      color: #666;
      margin-bottom: 16px;
    }
    
    .drop-text {
      font-size: 16px;
      margin: 8px 0;
      color: #333;
    }
    
    .file-types {
      font-size: 12px;
      color: #666;
      margin: 0;
    }
    
    .upload-progress {
      margin: 20px 0;
    }
    
    .file-progress {
      margin: 16px 0;
      padding: 12px;
      border: 1px solid #e0e0e0;
      border-radius: 4px;
    }
    
    .file-info {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 8px;
    }
    
    .file-name {
      font-weight: 500;
      flex: 1;
    }
    
    .file-size {
      color: #666;
      font-size: 12px;
    }
    
    .status-text {
      margin-top: 4px;
      font-size: 12px;
    }
    
    .status-uploading { color: #1976d2; }
    .status-success { color: #4caf50; }
    .status-error { color: #f44336; }
    .status-processing { color: #ff9800; }
    .status-processed { color: #4caf50; }
    
    .documents-list {
      margin-top: 24px;
    }
    
    .documents-list h4 {
      margin-bottom: 12px;
      color: #333;
    }
    
    mat-card-actions {
      display: flex;
      gap: 12px;
    }
  `]
})
export class DocumentUploadComponent {
  @Input() projectId!: string;
  @Output() documentsChanged = new EventEmitter<Document[]>();
  @Output() questionsExtracted = new EventEmitter<any>();

  uploadFiles: any[] = [];
  documents: Document[] = [];
  isDragOver = false;
  isUploading = false;
  isProcessing = false;

  constructor(
    private projectService: ProjectService,
    private snackBar: MatSnackBar
  ) {}

  ngOnInit() {
    this.loadDocuments();
  }

  onDragOver(event: DragEvent) {
    event.preventDefault();
    this.isDragOver = true;
  }

  onDragLeave(event: DragEvent) {
    event.preventDefault();
    this.isDragOver = false;
  }

  onFileDrop(event: DragEvent) {
    event.preventDefault();
    this.isDragOver = false;
    
    const files = Array.from(event.dataTransfer?.files || []);
    this.handleFiles(files);
  }

  onFileSelect(event: Event) {
    const input = event.target as HTMLInputElement;
    const files = Array.from(input.files || []);
    this.handleFiles(files);
    input.value = ''; // Reset input
  }

  handleFiles(files: File[]) {
    const validFiles = files.filter(file => this.validateFile(file));
    
    if (validFiles.length !== files.length) {
      this.snackBar.open(
        'Some files were skipped due to invalid format or size',
        'OK',
        { duration: 5000 }
      );
    }

    if (validFiles.length > 0) {
      this.uploadFiles.push(...validFiles.map(file => ({
        file,
        name: file.name,
        size: file.size,
        progress: 0,
        status: 'pending'
      })));
      
      this.startUpload();
    }
  }

  validateFile(file: File): boolean {
    const allowedTypes = [
      'application/pdf',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'text/plain',
      'text/markdown'
    ];
    
    const maxSize = 100 * 1024 * 1024; // 100MB
    
    if (!allowedTypes.includes(file.type) && !file.name.match(/\.(pdf|docx|txt|md)$/i)) {
      this.snackBar.open(
        `File type not supported: ${file.name}`,
        'OK',
        { duration: 3000 }
      );
      return false;
    }
    
    if (file.size > maxSize) {
      this.snackBar.open(
        `File too large: ${file.name} (max 100MB)`,
        'OK',
        { duration: 3000 }
      );
      return false;
    }
    
    return true;
  }

  async startUpload() {
    this.isUploading = true;
    
    for (const uploadFile of this.uploadFiles) {
      if (uploadFile.status !== 'pending') continue;
      
      try {
        uploadFile.status = 'uploading';
        
        const formData = new FormData();
        formData.append('file', uploadFile.file);
        formData.append('name', uploadFile.name);
        
        // Simulate progress updates
        const progressInterval = setInterval(() => {
          if (uploadFile.progress < 90) {
            uploadFile.progress += Math.random() * 30;
          }
        }, 500);
        
        const document = await this.projectService.uploadDocument(this.projectId, formData).toPromise();
        
        clearInterval(progressInterval);
        uploadFile.progress = 100;
        uploadFile.status = 'success';
        
        this.documents.push(document);
        this.documentsChanged.emit(this.documents);
        
        this.snackBar.open(
          `Uploaded: ${uploadFile.name}`,
          'OK',
          { duration: 3000 }
        );
        
      } catch (error) {
        uploadFile.status = 'error';
        uploadFile.progress = 0;
        
        this.snackBar.open(
          `Upload failed: ${uploadFile.name}`,
          'OK',
          { duration: 5000 }
        );
      }
    }
    
    this.isUploading = false;
    
    // Clear completed uploads after a delay
    setTimeout(() => {
      this.uploadFiles = this.uploadFiles.filter(f => f.status === 'error');
    }, 3000);
  }

  async loadDocuments() {
    try {
      this.documents = await this.projectService.getProjectDocuments(this.projectId).toPromise();
      this.documentsChanged.emit(this.documents);
    } catch (error) {
      console.error('Error loading documents:', error);
    }
  }

  async processDocuments() {
    if (!this.hasProcessableDocuments) return;
    
    this.isProcessing = true;
    
    try {
      const processableDocuments = this.documents.filter(
        doc => doc.status === 'uploaded' || doc.status === 'processed'
      );
      
      for (const document of processableDocuments) {
        // Update document status to processing
        document.status = 'processing';
        
        // Extract questions from document
        const extractRequest = {
          document_id: document.id,
          document_name: document.name,
          content: '', // Will be loaded on backend
          project_id: this.projectId
        };
        
        const result = await this.projectService.extractQuestions(extractRequest).toPromise();
        
        document.status = 'processed';
        document.processed_at = new Date();
        
        this.questionsExtracted.emit(result);
      }
      
      this.snackBar.open(
        'Questions extracted successfully!',
        'OK',
        { duration: 5000 }
      );
      
    } catch (error) {
      console.error('Error processing documents:', error);
      this.snackBar.open(
        'Error processing documents. Please try again.',
        'OK',
        { duration: 5000 }
      );
    } finally {
      this.isProcessing = false;
    }
  }

  async removeDocument(document: Document) {
    try {
      await this.projectService.deleteDocument(document.id).toPromise();
      this.documents = this.documents.filter(d => d.id !== document.id);
      this.documentsChanged.emit(this.documents);
      
      this.snackBar.open(
        `Removed: ${document.name}`,
        'OK',
        { duration: 3000 }
      );
    } catch (error) {
      this.snackBar.open(
        'Error removing document',
        'OK',
        { duration: 3000 }
      );
    }
  }

  get hasProcessableDocuments(): boolean {
    return this.documents.some(
      doc => doc.status === 'uploaded' || doc.status === 'processed'
    );
  }

  formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  getStatusText(file: any): string {
    switch (file.status) {
      case 'pending': return 'Waiting...';
      case 'uploading': return `Uploading... ${Math.round(file.progress)}%`;
      case 'success': return 'Upload complete';
      case 'error': return 'Upload failed';
      default: return '';
    }
  }

  getDocumentIcon(document: Document): string {
    switch (document.status) {
      case 'uploaded': return 'description';
      case 'processing': return 'hourglass_empty';
      case 'processed': return 'check_circle';
      case 'error': return 'error';
      default: return 'description';
    }
  }
}