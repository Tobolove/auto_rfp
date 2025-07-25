import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatTabsModule } from '@angular/material/tabs';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatChipsModule } from '@angular/material/chips';
import { MatSnackBarModule, MatSnackBar } from '@angular/material/snack-bar';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatBadgeModule } from '@angular/material/badge';
import { MatDividerModule } from '@angular/material/divider';
import { MatDialogModule, MatDialog } from '@angular/material/dialog';
import { Project, Document, Question, ProjectStats } from '../../../models';
import { ProjectService } from '../../../services/project.service';
import { OrganizationService } from '../../../services/organization.service';

@Component({
  selector: 'app-project-detail',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatTabsModule,
    MatProgressBarModule,
    MatChipsModule,
    MatSnackBarModule,
    MatProgressSpinnerModule,
    MatBadgeModule,
    MatDividerModule,
    MatDialogModule,
  ],
  templateUrl: './project-detail.component.html',
  styleUrls: ['./project-detail.component.scss'],
})
export class ProjectDetailComponent implements OnInit {
  projectId: string = '';
  project: Project | null = null;
  documents: Document[] = [];
  questions: Question[] = [];
  stats: ProjectStats | null = null;
  loading = true;
  selectedTabIndex = 0;
  extractingQuestions = false;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private projectService: ProjectService,
    private organizationService: OrganizationService,
    private snackBar: MatSnackBar,
    private dialog: MatDialog
  ) {}

  ngOnInit(): void {
    console.log('ProjectDetailComponent.ngOnInit() called');
    this.route.params.subscribe(params => {
      console.log('Route params:', params);
      this.projectId = params['id'];
      console.log('Project ID from route:', this.projectId);
      if (this.projectId) {
        this.loadProjectData();
      }
    });
  }

  loadProjectData(): void {
    this.loading = true;
    
    this.projectService.getProject(this.projectId, true).subscribe({
      next: (project) => {
        this.project = project;
        if (this.project) {
          this.projectService.setCurrentProject(this.project);
        }
        
        // Load related data
        this.loadDocuments();
        this.loadQuestions();
        this.loadStats();
        
        this.loading = false;
      },
      error: (error) => {
        console.error('Error loading project:', error);
        this.snackBar.open('Failed to load project', 'Close', { duration: 3000 });
        this.router.navigate(['/projects']);
        this.loading = false;
      }
    });
  }

  loadDocuments(): void {
    if (!this.projectId) return;
    
    this.projectService.getProjectDocuments(this.projectId).subscribe({
      next: (documents) => {
        this.documents = documents;
      },
      error: (error) => {
        console.error('Error loading documents:', error);
      }
    });
  }

  loadQuestions(): void {
    if (!this.projectId) return;
    
    this.projectService.getProjectQuestions(this.projectId).subscribe({
      next: (questions) => {
        this.questions = questions;
      },
      error: (error) => {
        console.error('Error loading questions:', error);
      }
    });
  }

  loadStats(): void {
    if (!this.projectId) return;
    
    this.projectService.getProjectStats(this.projectId).subscribe({
      next: (stats) => {
        this.stats = stats;
      },
      error: (error) => {
        console.error('Error loading stats:', error);
      }
    });
  }

  goBackToProjects(): void {
    this.router.navigate(['/projects']);
  }

  editProject(): void {
    this.router.navigate(['/projects', this.projectId, 'edit']);
  }

  deleteProject(): void {
    if (!this.project) return;
    
    if (confirm(`Are you sure you want to delete "${this.project.name}"?`)) {
      this.projectService.deleteProject(this.projectId).subscribe({
        next: () => {
          this.snackBar.open('Project deleted successfully', 'Close', {
            duration: 3000,
          });
          this.router.navigate(['/projects']);
        },
        error: (error) => {
          console.error('Error deleting project:', error);
          this.snackBar.open('Failed to delete project', 'Close', {
            duration: 3000,
          });
        },
      });
    }
  }

  uploadDocument(): void {
    // Create file input element
    const fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.accept = '.pdf,.docx,.xlsx,.xls,.txt,.md';
    fileInput.multiple = false;
    
    fileInput.onchange = async (event: any) => {
      const file = event.target.files[0];
      if (!file) return;
      
      // Validate file
      if (file.size > 100 * 1024 * 1024) { // 100MB limit
        this.snackBar.open('File too large. Maximum size is 100MB.', 'Close', { duration: 5000 });
        return;
      }
      
      try {
        // Show uploading message
        this.snackBar.open('Uploading document...', 'Close', { duration: 2000 });
        
        // Upload using ProjectService
        const document = await this.projectService.uploadDocument(
          this.projectId!,
          file,
          file.name
        ).toPromise();
        
        // Success message
        this.snackBar.open('Document uploaded successfully!', 'Close', { duration: 3000 });
        
        // Refresh documents list
        this.loadProjectData();
        
      } catch (error) {
        console.error('Upload failed:', error);
        this.snackBar.open('Upload failed. Please try again.', 'Close', { duration: 5000 });
      }
    };
    
    // Trigger file dialog
    fileInput.click();
  }

  viewQuestions(): void {
    this.router.navigate(['/projects', this.projectId, 'questions']);
  }

  extractQuestions(documentId: string): void {
    this.extractingQuestions = true;
    
    const request = {
      document_id: documentId,
      project_id: this.projectId
    };

    this.projectService.extractQuestions(request).subscribe({
      next: (response) => {
        this.extractingQuestions = false;
        this.snackBar.open(
          `Successfully extracted ${response.total_questions} questions from document!`, 
          'Close', 
          { duration: 3000 }
        );
        
        // Refresh questions list
        this.loadQuestions();
        
        // Navigate to questions view
        this.router.navigate(['/projects', this.projectId, 'questions']);
      },
      error: (error) => {
        this.extractingQuestions = false;
        console.error('Error extracting questions:', error);
        this.snackBar.open(
          'Failed to extract questions. Please try again.', 
          'Close', 
          { duration: 5000 }
        );
      }
    });
  }

  getCompletionPercentage(): number {
    return this.stats ? this.projectService.calculateCompletionPercentage(this.stats) : 0;
  }

  getStatusColor(): string {
    const completion = this.getCompletionPercentage();
    return this.projectService.getProjectStatusColor(completion);
  }

  getStatusText(): string {
    const completion = this.getCompletionPercentage();
    return this.projectService.getProjectStatusText(completion);
  }

  formatDate(date: Date | undefined): string {
    if (!date) return '';
    return new Date(date).toLocaleDateString();
  }

  formatFileSize(bytes: number): string {
    return this.projectService.formatFileSize(bytes);
  }

  getDocumentIcon(fileType: string): string {
    return this.projectService.getDocumentIcon(fileType);
  }
}