import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatChipsModule } from '@angular/material/chips';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { Project, Organization, ProjectStats } from '../../models';
import { ProjectService } from '../../services/project.service';
import { OrganizationService } from '../../services/organization.service';

@Component({
  selector: 'app-projects',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatChipsModule,
    MatProgressSpinnerModule,
    MatProgressBarModule,
  ],
  templateUrl: './projects.component.html',
  styleUrls: ['./projects.component.scss'],
})
export class ProjectsComponent implements OnInit {
  projects: Project[] = [];
  currentOrganization: Organization | null = null;
  projectStats: Map<string, ProjectStats> = new Map();
  loading = false;

  constructor(
    private projectService: ProjectService,
    private organizationService: OrganizationService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.organizationService.currentOrganization$.subscribe((org) => {
      this.currentOrganization = org;
      if (org) {
        this.loadProjects();
      }
    });

    // Check for stored current organization
    const storedOrg = this.organizationService.getCurrentOrganization();
    if (storedOrg) {
      this.currentOrganization = storedOrg;
      this.loadProjects();
    }
  }

  loadProjects(): void {
    if (!this.currentOrganization) return;

    this.loading = true;
    this.projectService.getProjects(this.currentOrganization.id).subscribe({
      next: (projects) => {
        this.projects = projects;
        this.loadProjectStats();
        this.loading = false;
      },
      error: (error) => {
        console.error('Error loading projects:', error);
        this.loading = false;
      },
    });
  }

  loadProjectStats(): void {
    this.projects.forEach((project) => {
      this.projectService.getProjectStats(project.id).subscribe({
        next: (stats) => {
          this.projectStats.set(project.id, stats);
        },
        error: (error) => {
          console.error(
            `Error loading stats for project ${project.id}:`,
            error
          );
        },
      });
    });
  }

  createNewProject(): void {
    this.router.navigate(['/projects/create']);
  }

  openProject(project: Project): void {
    this.projectService.setCurrentProject(project);
    this.router.navigate(['/projects', project.id]);
  }

  editProject(project: Project): void {
    this.router.navigate(['/projects', project.id, 'edit']);
  }

  deleteProject(project: Project): void {
    if (confirm(`Are you sure you want to delete "${project.name}"?`)) {
      this.projectService.deleteProject(project.id).subscribe({
        next: () => {
          this.loadProjects();
        },
        error: (error) => {
          console.error('Error deleting project:', error);
        },
      });
    }
  }

  getProjectStats(projectId: string): ProjectStats | null {
    return this.projectStats.get(projectId) || null;
  }

  getCompletionPercentage(projectId: string): number {
    const stats = this.getProjectStats(projectId);
    return stats ? this.projectService.calculateCompletionPercentage(stats) : 0;
  }

  getStatusColor(projectId: string): string {
    const completion = this.getCompletionPercentage(projectId);
    return this.projectService.getProjectStatusColor(completion);
  }

  getStatusText(projectId: string): string {
    const completion = this.getCompletionPercentage(projectId);
    return this.projectService.getProjectStatusText(completion);
  }

  formatDate(date: Date): string {
    return new Date(date).toLocaleDateString();
  }

  goToOrganizations(): void {
    this.router.navigate(['/organizations']);
  }
}
