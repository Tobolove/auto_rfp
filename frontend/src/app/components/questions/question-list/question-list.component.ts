import { Component, Input, Output, EventEmitter, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatChipsModule } from '@angular/material/chips';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatBadgeModule } from '@angular/material/badge';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatTabsModule } from '@angular/material/tabs';
import { MatListModule } from '@angular/material/list';
import { Question, Section, QuestionWithAnswer } from '../../../models';
import { ProjectService } from '../../../services/project.service';
import { AIService } from '../../../services/ai.service';

@Component({
  selector: 'app-question-list',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatChipsModule,
    MatProgressSpinnerModule,
    MatExpansionModule,
    MatBadgeModule,
    MatTooltipModule,
    MatTabsModule,
    MatListModule
  ],
  template: `
    <div class="question-list-container">
      <div class="list-header">
        <h2>
          <mat-icon>quiz</mat-icon>
          RFP Questions
          <mat-chip-set *ngIf="questions.length > 0">
            <mat-chip>{{ questions.length }} Questions</mat-chip>
            <mat-chip [color]="completionRate >= 80 ? 'accent' : completionRate >= 50 ? 'primary' : 'warn'">
              {{ completionRate }}% Complete
            </mat-chip>
          </mat-chip-set>
        </h2>
        
        <div class="header-actions">
          <button 
            mat-raised-button 
            color="primary"
            (click)="generateAllAnswers()"
            [disabled]="isGeneratingAll || questions.length === 0"
          >
            <mat-icon>auto_awesome</mat-icon>
            {{ isGeneratingAll ? 'Generating...' : 'Generate All Answers' }}
          </button>
          
          <button 
            mat-stroked-button
            (click)="exportQuestions()"
            [disabled]="questions.length === 0"
          >
            <mat-icon>download</mat-icon>
            Export
          </button>
        </div>
      </div>

      <!-- Filter Tabs -->
      <mat-tab-group [(selectedIndex)]="selectedTabIndex" (selectedTabChange)="onTabChange($event)">
        <mat-tab label="All Questions">
          <ng-template matTabLabel>
            <span matBadge="{{ questions.length }}" matBadgeOverlap="false">All</span>
          </ng-template>
        </mat-tab>
        <mat-tab label="Unanswered">
          <ng-template matTabLabel>
            <span matBadge="{{ unansweredQuestions.length }}" matBadgeOverlap="false" matBadgeColor="warn">Unanswered</span>
          </ng-template>
        </mat-tab>
        <mat-tab label="Answered">
          <ng-template matTabLabel>
            <span matBadge="{{ answeredQuestions.length }}" matBadgeOverlap="false" matBadgeColor="accent">Answered</span>
          </ng-template>
        </mat-tab>
        <mat-tab label="By Section">
          <ng-template matTabLabel>
            <span matBadge="{{ sections.length }}" matBadgeOverlap="false">Sections</span>
          </ng-template>
        </mat-tab>
      </mat-tab-group>

      <!-- Questions Content -->
      <div class="questions-content">
        <!-- All Questions / Filtered Questions -->
        <div *ngIf="selectedTabIndex < 3" class="questions-grid">
          <mat-card 
            *ngFor="let questionWithAnswer of getFilteredQuestions(); trackBy: trackByQuestionId" 
            class="question-card"
            [class.answered]="questionWithAnswer.answer"
          >
            <mat-card-header>
              <mat-card-title class="question-title">
                {{ questionWithAnswer.question.text }}
              </mat-card-title>
              <mat-card-subtitle>
                <mat-chip-set>
                  <mat-chip *ngIf="questionWithAnswer.question.section_title">
                    {{ questionWithAnswer.question.section_title }}
                  </mat-chip>
                  <mat-chip *ngIf="questionWithAnswer.question.topic">
                    {{ questionWithAnswer.question.topic }}
                  </mat-chip>
                </mat-chip-set>
              </mat-card-subtitle>
            </mat-card-header>

            <mat-card-content>
              <!-- Answer Section -->
              <div *ngIf="questionWithAnswer.answer" class="answer-section">
                <h4>
                  <mat-icon color="accent">check_circle</mat-icon>
                  Answer
                  <mat-chip class="confidence-chip" 
                    [color]="getConfidenceColor(questionWithAnswer.answer.confidence)">
                    {{ (questionWithAnswer.answer.confidence * 100) | number:'1.0-0' }}% Confidence
                  </mat-chip>
                </h4>
                <div class="answer-text">{{ questionWithAnswer.answer.text }}</div>
                
                <!-- Sources -->
                <div *ngIf="questionWithAnswer.sources && questionWithAnswer.sources.length > 0" class="sources-section">
                  <h5>Sources:</h5>
                  <mat-chip-set>
                    <mat-chip 
                      *ngFor="let source of questionWithAnswer.sources" 
                      matTooltip="{{ source.text_content }}"
                    >
                      {{ source.file_name }} (p.{{ source.page_number }})
                    </mat-chip>
                  </mat-chip-set>
                </div>
              </div>

              <!-- No Answer -->
              <div *ngIf="!questionWithAnswer.answer" class="no-answer-section">
                <p class="no-answer-text">
                  <mat-icon color="warn">help_outline</mat-icon>
                  This question hasn't been answered yet.
                </p>
              </div>
            </mat-card-content>

            <mat-card-actions>
              <button 
                mat-raised-button 
                color="primary"
                (click)="generateAnswer(questionWithAnswer.question)"
                [disabled]="isGenerating[questionWithAnswer.question.id]"
              >
                <mat-icon *ngIf="!isGenerating[questionWithAnswer.question.id]">
                  {{ questionWithAnswer.answer ? 'refresh' : 'auto_awesome' }}
                </mat-icon>
                <mat-spinner 
                  *ngIf="isGenerating[questionWithAnswer.question.id]" 
                  diameter="16"
                ></mat-spinner>
                {{ questionWithAnswer.answer ? 'Regenerate' : 'Generate Answer' }}
              </button>
              
              <button 
                mat-button
                (click)="viewQuestion(questionWithAnswer.question)"
              >
                <mat-icon>visibility</mat-icon>
                View Details
              </button>
              
              <button 
                mat-button
                color="warn"
                *ngIf="questionWithAnswer.answer"
                (click)="deleteAnswer(questionWithAnswer.question.id, questionWithAnswer.answer.id)"
                matTooltip="Delete Answer"
              >
                <mat-icon>delete</mat-icon>
                Delete Answer
              </button>
            </mat-card-actions>
          </mat-card>
        </div>

        <!-- By Section View -->
        <div *ngIf="selectedTabIndex === 3" class="sections-view">
          <mat-accordion multi="true">
            <mat-expansion-panel *ngFor="let section of sections" class="section-panel">
              <mat-expansion-panel-header>
                <mat-panel-title>
                  <mat-icon>folder</mat-icon>
                  {{ section.title }}
                </mat-panel-title>
                <mat-panel-description>
                  {{ section.questions.length }} questions
                  <mat-chip 
                    [color]="getSectionCompletionColor(section)" 
                    class="completion-chip"
                  >
                    {{ getSectionCompletionRate(section) }}% Complete
                  </mat-chip>
                </mat-panel-description>
              </mat-expansion-panel-header>
              
              <div class="section-content">
                <p *ngIf="section.description" class="section-description">
                  {{ section.description }}
                </p>
                
                <mat-list>
                  <mat-list-item *ngFor="let question of section.questions">
                    <mat-icon matListItemIcon [color]="getQuestionStatusColor(question)">
                      {{ getQuestionStatusIcon(question) }}
                    </mat-icon>
                    <div matListItemTitle>{{ question.text }}</div>
                    <div matListItemLine *ngIf="question.topic">Topic: {{ question.topic }}</div>
                    <div matListItemMeta>
                      <button 
                        mat-icon-button 
                        (click)="generateAnswer(question)"
                        [disabled]="isGenerating[question.id]"
                        matTooltip="Generate Answer"
                      >
                        <mat-icon>auto_awesome</mat-icon>
                      </button>
                    </div>
                  </mat-list-item>
                </mat-list>
              </div>
            </mat-expansion-panel>
          </mat-accordion>
        </div>

        <!-- Empty State -->
        <div *ngIf="questions.length === 0" class="empty-state">
          <mat-icon class="empty-icon">quiz</mat-icon>
          <h3>No Questions Available</h3>
          <p>Upload and process RFP documents to extract questions automatically.</p>
        </div>

        <!-- Loading State -->
        <div *ngIf="isLoading" class="loading-state">
          <mat-spinner diameter="50"></mat-spinner>
          <p>Loading questions...</p>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .question-list-container {
      padding: 20px;
      max-width: 1200px;
      margin: 0 auto;
    }

    .list-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 24px;
      flex-wrap: wrap;
      gap: 16px;
    }

    .list-header h2 {
      display: flex;
      align-items: center;
      gap: 12px;
      margin: 0;
      flex: 1;
    }

    .header-actions {
      display: flex;
      gap: 12px;
    }

    .questions-content {
      margin-top: 24px;
    }

    .questions-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
      gap: 20px;
    }

    .question-card {
      transition: all 0.3s ease;
    }

    .question-card:hover {
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }

    .question-card.answered {
      border-left: 4px solid #4caf50;
    }

    .question-title {
      font-size: 16px;
      line-height: 1.4;
      margin-bottom: 8px;
    }

    .answer-section {
      margin-top: 16px;
      padding: 16px;
      background-color: #f5f5f5;
      border-radius: 8px;
    }

    .answer-section h4 {
      display: flex;
      align-items: center;
      gap: 8px;
      margin: 0 0 12px 0;
      color: #2e7d32;
    }

    .confidence-chip {
      margin-left: auto;
    }

    .answer-text {
      line-height: 1.6;
      margin-bottom: 12px;
      white-space: pre-wrap;
    }

    .sources-section h5 {
      margin: 12px 0 8px 0;
      color: #666;
      font-size: 14px;
    }

    .no-answer-section {
      padding: 16px;
      text-align: center;
      color: #666;
    }

    .no-answer-text {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      margin: 0;
    }

    .sections-view {
      margin-top: 16px;
    }

    .section-panel {
      margin-bottom: 16px;
    }

    .section-content {
      padding: 16px 0;
    }

    .section-description {
      font-style: italic;
      color: #666;
      margin-bottom: 16px;
    }

    .completion-chip {
      margin-left: 8px;
    }

    .empty-state, .loading-state {
      text-align: center;
      padding: 60px 20px;
      color: #666;
    }

    .empty-icon {
      font-size: 64px;
      width: 64px;
      height: 64px;
      margin-bottom: 16px;
      opacity: 0.5;
    }

    .loading-state mat-spinner {
      margin: 0 auto 16px auto;
    }

    @media (max-width: 768px) {
      .questions-grid {
        grid-template-columns: 1fr;
      }
      
      .list-header {
        flex-direction: column;
        align-items: stretch;
      }
      
      .header-actions {
        justify-content: stretch;
      }
      
      .header-actions button {
        flex: 1;
      }
    }
  `]
})
export class QuestionListComponent implements OnInit {
  @Input() projectId!: string;
  @Output() questionSelected = new EventEmitter<Question>();
  @Output() answerGenerated = new EventEmitter<any>();

  questions: Question[] = [];
  questionsWithAnswers: QuestionWithAnswer[] = [];
  sections: Section[] = [];
  selectedTabIndex = 0;
  isLoading = false;
  isGenerating: { [key: string]: boolean } = {};
  isGeneratingAll = false;

  constructor(
    private projectService: ProjectService,
    private aiService: AIService,
    private route: ActivatedRoute
  ) {}

  ngOnInit() {
    // Get projectId from route params if not provided as Input
    if (!this.projectId) {
      this.route.params.subscribe(params => {
        this.projectId = params['id'];
        this.loadQuestions();
      });
    } else {
      this.loadQuestions();
    }
  }

  async loadQuestions() {
    if (!this.projectId) return;
    
    this.isLoading = true;
    
    try {
      // Load questions
      this.questions = await this.projectService.getProjectQuestions(this.projectId).toPromise() || [];
      
      // Load questions with answers
      await this.loadQuestionsWithAnswers();
      
      // Group questions by section
      this.groupQuestionsBySection();
      
    } catch (error) {
      console.error('Error loading questions:', error);
    } finally {
      this.isLoading = false;
    }
  }

  async loadQuestionsWithAnswers() {
    this.questionsWithAnswers = [];
    
    for (const question of this.questions) {
      try {
        const questionWithAnswer: QuestionWithAnswer = { question };
        
        // Try to load answer and sources
        const answerData = await this.projectService.getQuestionAnswer(question.id).toPromise();
        if (answerData) {
          questionWithAnswer.answer = answerData.answer;
          questionWithAnswer.sources = answerData.sources;
        }
        
        this.questionsWithAnswers.push(questionWithAnswer);
      } catch (error) {
        // Question has no answer yet
        this.questionsWithAnswers.push({ question });
      }
    }
  }

  groupQuestionsBySection() {
    const sectionMap = new Map<string, Question[]>();
    
    for (const question of this.questions) {
      const sectionTitle = question.section_title || 'Uncategorized';
      
      if (!sectionMap.has(sectionTitle)) {
        sectionMap.set(sectionTitle, []);
      }
      sectionMap.get(sectionTitle)!.push(question);
    }
    
    this.sections = Array.from(sectionMap.entries()).map(([title, questions]) => ({
      id: title.toLowerCase().replace(/\s+/g, '_'),
      title,
      description: `Questions from the ${title} section`,
      questions
    }));
  }

  async generateAnswer(question: Question) {
    this.isGenerating[question.id] = true;
    
    try {
      const request = {
        question: question.text,
        question_id: question.id,
        project_id: this.projectId,
        use_all_indexes: true
      };
      
      const response = await this.aiService.generateResponse(request).toPromise();
      
      // Reload the specific question with answer
      await this.loadQuestionsWithAnswers();
      
      this.answerGenerated.emit({
        question,
        response
      });
      
    } catch (error) {
      console.error('Error generating answer:', error);
    } finally {
      this.isGenerating[question.id] = false;
    }
  }

  async generateAllAnswers() {
    this.isGeneratingAll = true;
    
    try {
      const unanswered = this.unansweredQuestions;
      
      for (const questionWithAnswer of unanswered) {
        await this.generateAnswer(questionWithAnswer.question);
        
        // Small delay to avoid overwhelming the API
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
      
    } catch (error) {
      console.error('Error generating all answers:', error);
    } finally {
      this.isGeneratingAll = false;
    }
  }

  onTabChange(event: any) {
    this.selectedTabIndex = event.index;
  }

  getFilteredQuestions(): QuestionWithAnswer[] {
    switch (this.selectedTabIndex) {
      case 0: return this.questionsWithAnswers; // All
      case 1: return this.unansweredQuestions; // Unanswered
      case 2: return this.answeredQuestions; // Answered
      default: return this.questionsWithAnswers;
    }
  }

  get unansweredQuestions(): QuestionWithAnswer[] {
    return this.questionsWithAnswers.filter(qa => !qa.answer);
  }

  get answeredQuestions(): QuestionWithAnswer[] {
    return this.questionsWithAnswers.filter(qa => qa.answer);
  }

  get completionRate(): number {
    if (this.questions.length === 0) return 0;
    return Math.round((this.answeredQuestions.length / this.questions.length) * 100);
  }

  getSectionCompletionRate(section: Section): number {
    const answeredInSection = section.questions.filter(q => 
      this.questionsWithAnswers.find(qa => qa.question.id === q.id && qa.answer)
    ).length;
    
    return section.questions.length > 0 
      ? Math.round((answeredInSection / section.questions.length) * 100)
      : 0;
  }

  getSectionCompletionColor(section: Section): string {
    const rate = this.getSectionCompletionRate(section);
    if (rate >= 80) return 'accent';
    if (rate >= 50) return 'primary';
    return 'warn';
  }

  getConfidenceColor(confidence: number): string {
    if (confidence >= 0.8) return 'accent';
    if (confidence >= 0.6) return 'primary';
    return 'warn';
  }

  getQuestionStatusIcon(question: Question): string {
    const qa = this.questionsWithAnswers.find(qa => qa.question.id === question.id);
    return qa?.answer ? 'check_circle' : 'help_outline';
  }

  getQuestionStatusColor(question: Question): string {
    const qa = this.questionsWithAnswers.find(qa => qa.question.id === question.id);
    return qa?.answer ? 'accent' : 'warn';
  }

  viewQuestion(question: Question) {
    this.questionSelected.emit(question);
  }

  exportQuestions() {
    const dataStr = JSON.stringify({
      project_id: this.projectId,
      questions: this.questionsWithAnswers,
      export_date: new Date().toISOString(),
      completion_rate: this.completionRate
    }, null, 2);
    
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    const exportFileDefaultName = `rfp-questions-${this.projectId}.json`;
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  }

  trackByQuestionId(index: number, item: QuestionWithAnswer): string {
    return item.question.id;
  }

  async deleteAnswer(questionId: string, answerId: string) {
    if (!confirm('Are you sure you want to delete this answer? This action cannot be undone.')) {
      return;
    }

    try {
      await this.projectService.deleteAnswer(answerId).toPromise();
      
      // Update local data - remove answer from questionWithAnswer
      const questionWithAnswer = this.questionsWithAnswers.find(qa => qa.question.id === questionId);
      if (questionWithAnswer) {
        delete questionWithAnswer.answer;
        delete questionWithAnswer.sources;
      }
      
      console.log('Answer deleted successfully');
    } catch (error) {
      console.error('Error deleting answer:', error);
      alert('Failed to delete answer. Please try again.');
    }
  }
}