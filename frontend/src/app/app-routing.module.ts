import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { OrganizationsComponent } from './components/organizations/organizations.component';
import { CreateOrganizationComponent } from './components/organizations/create-organization/create-organization.component';
import { ProjectsComponent } from './components/projects/projects.component';
import { CreateProjectComponent } from './components/projects/create-project/create-project.component';
import { ProjectDetailComponent } from './components/projects/project-detail/project-detail.component';
import { QuestionListComponent } from './components/questions/question-list/question-list.component';
import { ReferenceDocumentsComponent } from './components/reference-documents/reference-documents.component';

const routes: Routes = [
  { path: '', redirectTo: '/organizations', pathMatch: 'full' },
  { path: 'organizations', component: OrganizationsComponent },
  { path: 'organizations/create', component: CreateOrganizationComponent },
  { path: 'organizations/:orgId/reference-documents', component: ReferenceDocumentsComponent },
  { path: 'projects', component: ProjectsComponent },
  { path: 'projects/create', component: CreateProjectComponent },
  { path: 'projects/:id', component: ProjectDetailComponent },
  { path: 'projects/:id/questions', component: QuestionListComponent },
  { path: '**', redirectTo: '/organizations' },
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule],
})
export class AppRoutingModule {}
