import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatChipsModule } from '@angular/material/chips';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatSnackBarModule, MatSnackBar } from '@angular/material/snack-bar';
import { MatTableModule } from '@angular/material/table';
import { MatIconModule } from '@angular/material/icon';
import { MatDialogModule, MatDialog } from '@angular/material/dialog';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { ActivatedRoute } from '@angular/router';
import { firstValueFrom } from 'rxjs';

import { ReferenceDocumentService } from '../../services/reference-document.service';

interface DocumentType {
  value: string;
  label: string;
}

interface ReferenceDocument {
  id: string;
  filename: string;
  original_name: string;
  document_type: string;
  industry_tags: string;
  capability_tags: string;
  upload_date: string;
  confidence_level: string;
  description?: string;
  content_length: number;
  is_active: boolean;
}

@Component({
  selector: 'app-reference-documents',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    MatCardModule,
    MatButtonModule,
    MatInputModule,
    MatSelectModule,
    MatChipsModule,
    MatProgressBarModule,
    MatSnackBarModule,
    MatTableModule,
    MatIconModule,
    MatDialogModule,
    MatProgressSpinnerModule
  ],
  template: `
    <div class="reference-documents-container">
      <mat-card class="header-card">
        <mat-card-header>
          <mat-card-title>
            <mat-icon>folder_shared</mat-icon>
            Reference Document Library
          </mat-card-title>
          <mat-card-subtitle>
            Upload and manage company documents for AI-powered RFP responses
          </mat-card-subtitle>
        </mat-card-header>
      </mat-card>

      <!-- Upload Section -->
      <mat-card class="upload-card">
        <mat-card-header>
          <mat-card-title>Upload New Document</mat-card-title>
        </mat-card-header>
        <mat-card-content>
          <form [formGroup]="uploadForm" (ngSubmit)="uploadDocument()">
            <div class="upload-grid">
              <!-- File Upload -->
              <div class="file-upload-section">
                <input type="file" #fileInput (change)="onFileSelected($event)" 
                       accept=".pdf,.docx,.doc,.txt,.md,.xlsx,.xls" hidden>
                <button type="button" mat-stroked-button (click)="fileInput.click()" 
                        [disabled]="uploading">
                  <mat-icon>upload_file</mat-icon>
                  {{ selectedFile ? selectedFile.name : 'Choose File' }}
                </button>
                <div *ngIf="selectedFile" class="file-info">
                  Size: {{ formatFileSize(selectedFile.size) }}
                </div>
              </div>

              <!-- Document Type -->
              <mat-form-field>
                <mat-label>Document Type</mat-label>
                <mat-select formControlName="documentType" required>
                  <mat-option *ngFor="let type of documentTypes" [value]="type.value">
                    {{ type.label }}
                  </mat-option>
                </mat-select>
              </mat-form-field>

              <!-- Industry Tags -->
              <mat-form-field>
                <mat-label>Industry Tags</mat-label>
                <mat-select formControlName="industryTags" multiple>
                  <mat-option *ngFor="let tag of industryTags" [value]="tag.value">
                    {{ tag.label }}
                  </mat-option>
                </mat-select>
              </mat-form-field>

              <!-- Capability Tags -->
              <mat-form-field>
                <mat-label>Capability Tags</mat-label>
                <mat-select formControlName="capabilityTags" multiple>
                  <mat-option *ngFor="let tag of capabilityTags" [value]="tag.value">
                    {{ tag.label }}
                  </mat-option>
                </mat-select>
              </mat-form-field>

              <!-- Project Size -->
              <mat-form-field>
                <mat-label>Project Size</mat-label>
                <mat-select formControlName="projectSize">
                  <mat-option value="">Not Specified</mat-option>
                  <mat-option *ngFor="let size of projectSizes" [value]="size.value">
                    {{ size.label }}
                  </mat-option>
                </mat-select>
              </mat-form-field>

              <!-- Geographic Scope -->
              <mat-form-field>
                <mat-label>Geographic Scope</mat-label>
                <mat-select formControlName="geographicScope">
                  <mat-option value="">Not Specified</mat-option>
                  <mat-option *ngFor="let scope of geographicScopes" [value]="scope.value">
                    {{ scope.label }}
                  </mat-option>
                </mat-select>
              </mat-form-field>

              <!-- Confidence Level -->
              <mat-form-field>
                <mat-label>Confidence Level</mat-label>
                <mat-select formControlName="confidenceLevel">
                  <mat-option *ngFor="let level of confidenceLevels" [value]="level.value">
                    {{ level.label }}
                  </mat-option>
                </mat-select>
              </mat-form-field>

              <!-- Description -->
              <mat-form-field class="full-width">
                <mat-label>Description</mat-label>
                <textarea matInput formControlName="description" rows="3"
                          placeholder="Brief description of the document content"></textarea>
              </mat-form-field>

              <!-- Keywords -->
              <mat-form-field class="full-width">
                <mat-label>Keywords</mat-label>
                <input matInput formControlName="keywords" 
                       placeholder="Comma-separated keywords for better searchability">
              </mat-form-field>

              <!-- Custom Tags -->
              <mat-form-field class="full-width">
                <mat-label>Custom Tags</mat-label>
                <input matInput formControlName="customTags" 
                       placeholder="Comma-separated custom tags">
              </mat-form-field>
            </div>

            <div class="upload-actions">
              <button type="submit" mat-raised-button color="primary" 
                      [disabled]="!selectedFile || uploading || uploadForm.invalid">
                <mat-icon>cloud_upload</mat-icon>
                {{ uploading ? 'Uploading...' : 'Upload Document' }}
              </button>
            </div>

            <mat-progress-bar *ngIf="uploading" mode="indeterminate"></mat-progress-bar>
          </form>
        </mat-card-content>
      </mat-card>

      <!-- Documents List -->
      <mat-card class="documents-card">
        <mat-card-header>
          <mat-card-title>Uploaded Documents ({{ documents.length }})</mat-card-title>
          <div class="spacer"></div>
          <button mat-icon-button (click)="loadDocuments()" [disabled]="loading">
            <mat-icon>refresh</mat-icon>
          </button>
        </mat-card-header>
        <mat-card-content>
          <div *ngIf="loading" class="loading-container">
            <mat-spinner diameter="40"></mat-spinner>
            <p>Loading documents...</p>
          </div>

          <div *ngIf="!loading && documents.length === 0" class="empty-state">
            <mat-icon>folder_open</mat-icon>
            <h3>No documents uploaded yet</h3>
            <p>Upload your first reference document to get started</p>
          </div>

          <div *ngIf="!loading && documents.length > 0" class="documents-table">
            <table mat-table [dataSource]="documents" class="documents-table">
              <!-- Filename Column -->
              <ng-container matColumnDef="filename">
                <th mat-header-cell *matHeaderCellDef>Document</th>
                <td mat-cell *matCellDef="let doc">
                  <div class="file-info">
                    <mat-icon class="file-icon">description</mat-icon>
                    <div>
                      <div class="filename">{{ doc.original_name }}</div>
                      <div class="file-meta">{{ formatFileSize(doc.content_length) }}</div>
                    </div>
                  </div>
                </td>
              </ng-container>

              <!-- Type Column -->
              <ng-container matColumnDef="type">
                <th mat-header-cell *matHeaderCellDef>Type</th>
                <td mat-cell *matCellDef="let doc">
                  <mat-chip>{{ formatDocumentType(doc.document_type) }}</mat-chip>
                </td>
              </ng-container>

              <!-- Tags Column -->
              <ng-container matColumnDef="tags">
                <th mat-header-cell *matHeaderCellDef>Tags</th>
                <td mat-cell *matCellDef="let doc">
                  <div class="tags-container">
                    <mat-chip *ngFor="let tag of getDocumentTags(doc)" class="tag-chip">
                      {{ formatTag(tag) }}
                    </mat-chip>
                  </div>
                </td>
              </ng-container>

              <!-- Upload Date Column -->
              <ng-container matColumnDef="uploadDate">
                <th mat-header-cell *matHeaderCellDef>Uploaded</th>
                <td mat-cell *matCellDef="let doc">
                  {{ formatDate(doc.upload_date) }}
                </td>
              </ng-container>

              <!-- Confidence Column -->
              <ng-container matColumnDef="confidence">
                <th mat-header-cell *matHeaderCellDef>Confidence</th>
                <td mat-cell *matCellDef="let doc">
                  <mat-chip [class]="'confidence-' + doc.confidence_level">
                    {{ doc.confidence_level.toUpperCase() }}
                  </mat-chip>
                </td>
              </ng-container>

              <!-- Actions Column -->
              <ng-container matColumnDef="actions">
                <th mat-header-cell *matHeaderCellDef>Actions</th>
                <td mat-cell *matCellDef="let doc">
                  <button mat-icon-button color="warn" (click)="deleteDocument(doc)" 
                          [disabled]="deleting.has(doc.id)">
                    <mat-icon>delete</mat-icon>
                  </button>
                </td>
              </ng-container>

              <tr mat-header-row *matHeaderRowDef="displayedColumns"></tr>
              <tr mat-row *matRowDef="let row; columns: displayedColumns;"></tr>
            </table>
          </div>
        </mat-card-content>
      </mat-card>
    </div>
  `,
  styleUrls: ['./reference-documents.component.scss']
})
export class ReferenceDocumentsComponent implements OnInit {
  uploadForm: FormGroup;
  selectedFile: File | null = null;
  uploading = false;
  loading = false;
  deleting = new Set<string>();
  
  organizationId: string = '';
  documents: ReferenceDocument[] = [];
  
  documentTypes: DocumentType[] = [];
  industryTags: DocumentType[] = [];
  capabilityTags: DocumentType[] = [];
  projectSizes: DocumentType[] = [];
  geographicScopes: DocumentType[] = [];
  confidenceLevels: DocumentType[] = [];
  
  displayedColumns: string[] = ['filename', 'type', 'tags', 'uploadDate', 'confidence', 'actions'];

  constructor(
    private fb: FormBuilder,
    private route: ActivatedRoute,
    private referenceDocumentService: ReferenceDocumentService,
    private snackBar: MatSnackBar
  ) {
    this.uploadForm = this.fb.group({
      documentType: ['', Validators.required],
      industryTags: [[]],
      capabilityTags: [[]],
      projectSize: [''],
      geographicScope: [''],
      confidenceLevel: ['medium'],
      description: [''],
      keywords: [''],
      customTags: ['']
    });
  }

  ngOnInit() {
    // Get organization ID from route or service
    this.organizationId = this.route.snapshot.params['orgId'] || '1'; // Default for now
    
    this.loadDocumentTypes();
    this.loadDocuments();
  }

  async loadDocumentTypes() {
    try {
      const types = await firstValueFrom(this.referenceDocumentService.getDocumentTypes());
      if (types) {
        this.documentTypes = types.document_types;
        this.industryTags = types.industry_tags;
        this.capabilityTags = types.capability_tags;
        this.projectSizes = types.project_sizes;
        this.geographicScopes = types.geographic_scopes;
        this.confidenceLevels = types.confidence_levels;
      }
    } catch (error) {
      console.error('Error loading document types:', error);
      
      // Fallback: Provide hardcoded options if API fails
      this.documentTypes = [
        { value: 'company_profile', label: 'Company Profile' },
        { value: 'case_study', label: 'Case Study' },
        { value: 'technical_specs', label: 'Technical Specs' },
        { value: 'certifications', label: 'Certifications' },
        { value: 'team_bios', label: 'Team Bios' },
        { value: 'pricing_templates', label: 'Pricing Templates' },
        { value: 'methodology', label: 'Methodology' },
        { value: 'partnerships', label: 'Partnerships' },
        { value: 'awards', label: 'Awards' },
        { value: 'other', label: 'Other' }
      ];
      
      this.industryTags = [
        { value: 'healthcare', label: 'Healthcare' },
        { value: 'finance', label: 'Finance' },
        { value: 'technology', label: 'Technology' },
        { value: 'manufacturing', label: 'Manufacturing' },
        { value: 'government', label: 'Government' },
        { value: 'education', label: 'Education' },
        { value: 'retail', label: 'Retail' },
        { value: 'energy', label: 'Energy' },
        { value: 'other', label: 'Other' }
      ];
      
      this.capabilityTags = [
        { value: 'cloud_migration', label: 'Cloud Migration' },
        { value: 'data_analytics', label: 'Data Analytics' },
        { value: 'cybersecurity', label: 'Cybersecurity' },
        { value: 'ai_ml', label: 'AI/ML' },
        { value: 'integration', label: 'Integration' },
        { value: 'mobile_development', label: 'Mobile Development' },
        { value: 'web_development', label: 'Web Development' },
        { value: 'consulting', label: 'Consulting' },
        { value: 'other', label: 'Other' }
      ];
      
      this.projectSizes = [
        { value: 'small', label: 'Small' },
        { value: 'medium', label: 'Medium' },
        { value: 'large', label: 'Large' },
        { value: 'enterprise', label: 'Enterprise' }
      ];
      
      this.geographicScopes = [
        { value: 'local', label: 'Local' },
        { value: 'regional', label: 'Regional' },
        { value: 'national', label: 'National' },
        { value: 'international', label: 'International' }
      ];
      
      this.confidenceLevels = [
        { value: 'high', label: 'High' },
        { value: 'medium', label: 'Medium' },
        { value: 'low', label: 'Low' }
      ];
      
      this.snackBar.open('Using default document types (API not available)', 'Close', { duration: 3000 });
    }
  }

  async loadDocuments() {
    this.loading = true;
    try {
      const response = await firstValueFrom(this.referenceDocumentService.getOrganizationDocuments(this.organizationId));
      if (response) {
        this.documents = response.documents;
      }
    } catch (error) {
      console.error('Error loading documents:', error);
      
      // For now, just show empty list when API is not available
      this.documents = [];
      this.snackBar.open('Documents API not available yet - upload feature coming soon!', 'Close', { duration: 3000 });
    } finally {
      this.loading = false;
    }
  }

  onFileSelected(event: any) {
    const file = event.target.files[0];
    if (file) {
      // Validate file size (50MB limit)
      if (file.size > 50 * 1024 * 1024) {
        this.snackBar.open('File too large. Maximum size is 50MB.', 'Close', { duration: 5000 });
        return;
      }
      
      this.selectedFile = file;
    }
  }

  async uploadDocument() {
    if (!this.selectedFile || this.uploadForm.invalid) {
      return;
    }

    this.uploading = true;
    try {
      const formData = new FormData();
      formData.append('file', this.selectedFile);
      
      const formValue = this.uploadForm.value;
      formData.append('document_type', formValue.documentType);
      formData.append('industry_tags', Array.isArray(formValue.industryTags) ? formValue.industryTags.join(',') : '');
      formData.append('capability_tags', Array.isArray(formValue.capabilityTags) ? formValue.capabilityTags.join(',') : '');
      formData.append('project_size', formValue.projectSize || '');
      formData.append('geographic_scope', formValue.geographicScope || '');
      formData.append('confidence_level', formValue.confidenceLevel);
      formData.append('custom_tags', formValue.customTags || '');
      formData.append('description', formValue.description || '');
      formData.append('keywords', formValue.keywords || '');

      const response = await firstValueFrom(this.referenceDocumentService.uploadDocument(this.organizationId, formData));
      
      if (response && response.success) {
        this.snackBar.open('Document uploaded successfully!', 'Close', { duration: 3000 });
        this.resetForm();
        this.loadDocuments();
      } else {
        this.snackBar.open(response?.message || 'Upload failed', 'Close', { duration: 5000 });
      }
    } catch (error) {
      this.snackBar.open('Upload failed. Please try again.', 'Close', { duration: 5000 });
    } finally {
      this.uploading = false;
    }
  }

  async deleteDocument(doc: ReferenceDocument) {
    if (!confirm(`Are you sure you want to delete "${doc.original_name}"?`)) {
      return;
    }

    this.deleting.add(doc.id);
    try {
      await firstValueFrom(this.referenceDocumentService.deleteDocument(this.organizationId, doc.id));
      this.snackBar.open('Document deleted successfully', 'Close', { duration: 3000 });
      this.loadDocuments();
    } catch (error) {
      this.snackBar.open('Failed to delete document', 'Close', { duration: 3000 });
    } finally {
      this.deleting.delete(doc.id);
    }
  }

  resetForm() {
    this.uploadForm.reset();
    this.selectedFile = null;
    this.uploadForm.patchValue({
      confidenceLevel: 'medium'
    });
  }

  formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  formatDocumentType(type: string): string {
    return type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  }

  formatTag(tag: string): string {
    return tag.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  }

  formatDate(dateString: string): string {
    return new Date(dateString).toLocaleDateString();
  }

  getDocumentTags(doc: ReferenceDocument): string[] {
    const tags: string[] = [];
    
    if (doc.industry_tags) {
      tags.push(...doc.industry_tags.split(',').filter(tag => tag.trim()));
    }
    
    if (doc.capability_tags) {
      tags.push(...doc.capability_tags.split(',').filter(tag => tag.trim()));
    }
    
    return tags.slice(0, 3); // Limit to 3 tags for display
  }
}