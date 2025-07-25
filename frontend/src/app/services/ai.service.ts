import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject } from 'rxjs';
import {
  ExtractQuestionsRequest,
  ExtractQuestionsResponse,
  GenerateResponseRequest,
  GenerateResponseResponse,
  MultiStepResponse,
} from '../models';

@Injectable({
  providedIn: 'root',
})
export class AIService {
  private baseUrl = 'http://localhost:8000';
  private processingStepsSubject = new BehaviorSubject<any[]>([]);
  public processingSteps$ = this.processingStepsSubject.asObservable();

  constructor(private http: HttpClient) {}

  // Document processing
  extractQuestionsFromDocument(
    request: ExtractQuestionsRequest
  ): Observable<ExtractQuestionsResponse> {
    return this.http.post<ExtractQuestionsResponse>(
      `${this.baseUrl}/ai/extract-questions`,
      request
    );
  }

  // Response generation
  generateResponse(
    request: GenerateResponseRequest
  ): Observable<GenerateResponseResponse> {
    return this.http.post<GenerateResponseResponse>(
      `${this.baseUrl}/ai/generate-response`,
      request
    );
  }

  // Multi-step response generation
  generateMultiStepResponse(
    request: GenerateResponseRequest
  ): Observable<MultiStepResponse> {
    return this.http.post<MultiStepResponse>(
      `${this.baseUrl}/ai/multi-step-response`,
      request
    );
  }

  // Processing state management
  setProcessingSteps(steps: any[]): void {
    this.processingStepsSubject.next(steps);
  }

  getProcessingSteps(): any[] {
    return this.processingStepsSubject.value;
  }

  clearProcessingSteps(): void {
    this.processingStepsSubject.next([]);
  }

  // Utility methods for AI processing
  getStepIcon(stepType: string): string {
    switch (stepType) {
      case 'analyze_question':
        return 'psychology';
      case 'search_documents':
        return 'search';
      case 'extract_information':
        return 'fact_check';
      case 'synthesize_response':
        return 'auto_awesome';
      case 'validate_answer':
        return 'check_circle';
      default:
        return 'settings';
    }
  }

  getStepColor(status: string): string {
    switch (status) {
      case 'pending':
        return 'warn';
      case 'running':
        return 'accent';
      case 'completed':
        return 'primary';
      case 'failed':
        return 'warn';
      default:
        return 'basic';
    }
  }

  formatStepDuration(duration?: number): string {
    if (!duration) return '';
    return `${duration.toFixed(2)}s`;
  }

  calculateOverallProgress(steps: any[]): number {
    if (steps.length === 0) return 0;

    const completedSteps = steps.filter(
      (step) => step.status === 'completed'
    ).length;
    return (completedSteps / steps.length) * 100;
  }

  getConfidenceColor(confidence: number): string {
    if (confidence >= 0.8) return 'primary';
    if (confidence >= 0.6) return 'accent';
    return 'warn';
  }

  getConfidenceText(confidence: number): string {
    if (confidence >= 0.9) return 'Very High';
    if (confidence >= 0.8) return 'High';
    if (confidence >= 0.6) return 'Medium';
    if (confidence >= 0.4) return 'Low';
    return 'Very Low';
  }

  // Mock data generators for development/demo
  generateMockQuestionExtractionResult(
    documentName: string,
    projectId: string
  ): ExtractQuestionsResponse {
    const mockSections = [
      {
        id: 'section_technical',
        title: 'Technical Requirements',
        description: 'Questions related to technical capabilities',
        questions: [
          {
            id: '1',
            reference_id: 'Q1.1',
            text: 'Describe your technical infrastructure and security measures.',
            topic: 'Infrastructure',
            project_id: projectId,
            created_at: new Date(),
            updated_at: new Date(),
          },
          {
            id: '2',
            reference_id: 'Q1.2',
            text: 'What backup and disaster recovery procedures do you have in place?',
            topic: 'Business Continuity',
            project_id: projectId,
            created_at: new Date(),
            updated_at: new Date(),
          },
        ],
      },
      {
        id: 'section_experience',
        title: 'Company Experience',
        description: 'Questions about company background and qualifications',
        questions: [
          {
            id: '3',
            reference_id: 'Q2.1',
            text: 'Provide details about your relevant experience in this domain.',
            topic: 'Experience',
            project_id: projectId,
            created_at: new Date(),
            updated_at: new Date(),
          },
        ],
      },
    ];

    return {
      document_id: 'mock-doc-id',
      document_name: documentName,
      sections: mockSections,
      extracted_at: new Date(),
    };
  }

  generateMockResponseResult(question: string): GenerateResponseResponse {
    const mockResponse = `Based on your question: "${question}"

Our company provides comprehensive solutions that address your requirements:

• **Technical Excellence**: State-of-the-art infrastructure with 99.9% uptime SLA
• **Security First**: ISO 27001 certified with multi-layered security protocols  
• **Proven Experience**: 15+ years serving clients across various industries
• **Expert Team**: Certified professionals with deep domain expertise
• **Quality Assurance**: Rigorous testing and validation processes

We are committed to delivering exceptional results that exceed your expectations.`;

    return {
      success: true,
      response: mockResponse,
      sources: [
        {
          id: 1,
          fileName: 'company_capabilities.pdf',
          pageNumber: '3-5',
          relevance: 95,
          textContent: 'Technical infrastructure overview...',
        },
        {
          id: 2,
          fileName: 'security_protocols.docx',
          pageNumber: '12',
          relevance: 88,
          textContent: 'Security measures and compliance...',
        },
      ],
      metadata: {
        confidence: 0.92,
        generatedAt: new Date().toISOString(),
        indexesUsed: ['index-1', 'index-2'],
        note: 'Generated using company knowledge base',
      },
    };
  }

  // File processing utilities
  validateFileForProcessing(file: File): { valid: boolean; error?: string } {
    const maxSize = 50 * 1024 * 1024; // 50MB
    const allowedTypes = [
      'application/pdf',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      'application/vnd.openxmlformats-officedocument.presentationml.presentation',
      'text/plain',
    ];

    if (file.size > maxSize) {
      return { valid: false, error: 'File size exceeds 50MB limit' };
    }

    if (!allowedTypes.includes(file.type)) {
      return {
        valid: false,
        error:
          'Unsupported file type. Please upload PDF, Word, Excel, PowerPoint, or text files.',
      };
    }

    return { valid: true };
  }

  async readFileContent(file: File): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        resolve(e.target?.result as string);
      };
      reader.onerror = (e) => {
        reject(new Error('Failed to read file'));
      };
      reader.readAsText(file);
    });
  }
}
