import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import {
  FormBuilder,
  FormGroup,
  Validators,
  ReactiveFormsModule,
} from '@angular/forms';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSnackBarModule, MatSnackBar } from '@angular/material/snack-bar';
import { ProjectService } from '../../../services/project.service';
import { OrganizationService } from '../../../services/organization.service';
import { ProjectCreate, Organization } from '../../../models';

@Component({
  selector: 'app-create-project',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatInputModule,
    MatFormFieldModule,
    MatSnackBarModule,
  ],
  templateUrl: './create-project.component.html',
  styleUrls: ['./create-project.component.scss'],
})
export class CreateProjectComponent {
  projectForm: FormGroup;
  loading = false;
  currentOrganization: Organization | null = null;

  constructor(
    private formBuilder: FormBuilder,
    private projectService: ProjectService,
    private organizationService: OrganizationService,
    private router: Router,
    private snackBar: MatSnackBar
  ) {
    this.projectForm = this.formBuilder.group({
      name: ['', [Validators.required, Validators.minLength(3)]],
      description: [''],
    });

    // Get current organization
    this.currentOrganization = this.organizationService.getCurrentOrganization();
    if (!this.currentOrganization) {
      this.snackBar.open('Please select an organization first', 'Close', {
        duration: 3000,
      });
      this.router.navigate(['/organizations']);
    }
  }

  onSubmit(): void {
    if (this.projectForm.valid && this.currentOrganization) {
      this.loading = true;
      const formData = this.projectForm.value;

      const createRequest: ProjectCreate = {
        name: formData.name,
        description: formData.description || undefined,
        organization_id: this.currentOrganization.id,
      };

      this.projectService.createProject(createRequest).subscribe({
        next: (project) => {
          this.snackBar.open('Project created successfully!', 'Close', {
            duration: 3000,
          });
          this.router.navigate(['/projects']);
        },
        error: (error) => {
          console.error('Error creating project:', error);
          this.snackBar.open(
            'Failed to create project. Please try again.',
            'Close',
            {
              duration: 5000,
            }
          );
          this.loading = false;
        },
      });
    } else {
      this.markFormGroupTouched();
    }
  }

  onCancel(): void {
    this.router.navigate(['/projects']);
  }

  private markFormGroupTouched(): void {
    Object.keys(this.projectForm.controls).forEach((key) => {
      const control = this.projectForm.get(key);
      control?.markAsTouched();
    });
  }

  getErrorMessage(fieldName: string): string {
    const control = this.projectForm.get(fieldName);
    if (control?.hasError('required')) {
      return `${
        fieldName.charAt(0).toUpperCase() + fieldName.slice(1)
      } is required`;
    }
    if (control?.hasError('minlength')) {
      return `${
        fieldName.charAt(0).toUpperCase() + fieldName.slice(1)
      } must be at least 3 characters`;
    }
    return '';
  }
}