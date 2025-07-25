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
import { OrganizationService } from '../../../services/organization.service';
import { OrganizationCreate } from '../../../models';

@Component({
  selector: 'app-create-organization',
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
  templateUrl: './create-organization.component.html',
  styleUrls: ['./create-organization.component.scss'],
})
export class CreateOrganizationComponent {
  organizationForm: FormGroup;
  loading = false;

  constructor(
    private formBuilder: FormBuilder,
    private organizationService: OrganizationService,
    private router: Router,
    private snackBar: MatSnackBar
  ) {
    this.organizationForm = this.formBuilder.group({
      name: ['', [Validators.required, Validators.minLength(3)]],
      slug: ['', [Validators.required, Validators.pattern(/^[a-z0-9-]+$/)]],
      description: [''],
    });
  }

  onNameChange(): void {
    const name = this.organizationForm.get('name')?.value;
    if (name) {
      const slug = name
        .toLowerCase()
        .replace(/[^a-z0-9\s-]/g, '')
        .replace(/\s+/g, '-')
        .replace(/-+/g, '-')
        .trim();
      this.organizationForm.get('slug')?.setValue(slug);
    }
  }

  onSubmit(): void {
    if (this.organizationForm.valid) {
      this.loading = true;
      const formData = this.organizationForm.value;

      const createRequest: OrganizationCreate = {
        name: formData.name,
        slug: formData.slug,
        description: formData.description || undefined,
      };

      this.organizationService
        .createOrganization(createRequest, 'user@example.com')
        .subscribe({
          next: (organization) => {
            this.snackBar.open('Organization created successfully!', 'Close', {
              duration: 3000,
            });
            this.router.navigate(['/organizations']);
          },
          error: (error) => {
            console.error('Error creating organization:', error);
            this.snackBar.open(
              'Failed to create organization. Please try again.',
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
    this.router.navigate(['/organizations']);
  }

  private markFormGroupTouched(): void {
    Object.keys(this.organizationForm.controls).forEach((key) => {
      const control = this.organizationForm.get(key);
      control?.markAsTouched();
    });
  }

  getErrorMessage(fieldName: string): string {
    const control = this.organizationForm.get(fieldName);
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
    if (control?.hasError('pattern')) {
      return 'Slug can only contain lowercase letters, numbers, and hyphens';
    }
    return '';
  }
}
