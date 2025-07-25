import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBarModule, MatSnackBar } from '@angular/material/snack-bar';
import { MatChipsModule } from '@angular/material/chips';
import { Organization } from '../../models';
import { OrganizationService } from '../../services/organization.service';

@Component({
  selector: 'app-organizations',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatProgressSpinnerModule,
    MatSnackBarModule,
    MatChipsModule,
  ],
  templateUrl: './organizations.component.html',
  styleUrls: ['./organizations.component.scss'],
})
export class OrganizationsComponent implements OnInit {
  organizations: Organization[] = [];
  loading = false;
  userEmail = 'user@example.com'; // In production, get from auth service

  constructor(
    private organizationService: OrganizationService,
    private router: Router,
    private snackBar: MatSnackBar
  ) {}

  ngOnInit(): void {
    console.log('OrganizationsComponent.ngOnInit() called');
    this.loadOrganizations();
  }

  loadOrganizations(): void {
    this.loading = true;
    this.organizationService.getOrganizations(this.userEmail).subscribe({
      next: (organizations) => {
        this.organizations = organizations;
        this.loading = false;
      },
      error: (error) => {
        console.error('Error loading organizations:', error);
        this.snackBar.open('Failed to load organizations', 'Close', {
          duration: 3000,
        });
        this.loading = false;
      },
    });
  }

  selectOrganization(organization: Organization): void {
    this.organizationService.setCurrentOrganization(organization);
    this.router.navigate(['/projects']);
  }

  createNewOrganization(): void {
    this.router.navigate(['/organizations/create']);
  }

  editOrganization(organization: Organization): void {
    this.router.navigate(['/organizations', organization.id, 'edit']);
  }

  deleteOrganization(organization: Organization): void {
    if (confirm(`Are you sure you want to delete "${organization.name}"?`)) {
      this.organizationService.deleteOrganization(organization.id).subscribe({
        next: () => {
          this.snackBar.open('Organization deleted successfully', 'Close', {
            duration: 3000,
          });
          this.loadOrganizations();
        },
        error: (error) => {
          console.error('Error deleting organization:', error);
          this.snackBar.open('Failed to delete organization', 'Close', {
            duration: 3000,
          });
        },
      });
    }
  }

  isLlamaCloudConnected(organization: Organization): boolean {
    return !!(
      organization.llama_cloud_project_id &&
      organization.llama_cloud_connected_at
    );
  }

  formatDate(date: Date): string {
    return new Date(date).toLocaleDateString();
  }
}
