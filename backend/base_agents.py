from openai import OpenAI
from langfuse.openai import AzureOpenAI
import numpy as np
import pandas as pd
import re
import csv
import uuid
from datetime import datetime
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Load Azure OpenAI configuration from environment variables
azure_endpoint = os.getenv("AZURE_GPT_ENDPOINT")
azure_api_key = os.getenv("AZURE_GPT_KEY")
openai_api_key = azure_api_key  # For backwards compatibility


#-------------------------------------------------------------------
# DirectPromptAgent class definition
#-------------------------------------------------------------------
class DirectPromptAgent:
    
    def __init__(self, openai_api_key):
        # Initialize the agent
        self.openai_api_key = openai_api_key

    def respond(self, prompt):
        # Generate a response using Azure OpenAI API
        client = AzureOpenAI(
            azure_endpoint=azure_endpoint,
            api_version="2025-01-01-preview", 
            api_key=azure_api_key
        )
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )
        return response.choices[0].message.content


#-------------------------------------------------------------------
# AugmentedPromptAgent class definition
#-------------------------------------------------------------------
class AugmentedPromptAgent:
    def __init__(self, openai_api_key, persona):
        """Initialize the agent with given attributes."""
        self.persona = persona
        self.openai_api_key = openai_api_key

    def respond(self, input_text):
        """Generate a response using Azure OpenAI API."""
        client = AzureOpenAI(
            azure_endpoint=azure_endpoint,
            api_version="2025-01-01-preview", 
            api_key=azure_api_key
        )

        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": f"You are {self.persona} now please forget all previous descriptions."},
                {"role": "user", "content": input_text}
            ],
            temperature=0
        )

        return response.choices[0].message.content


#-------------------------------------------------------------------
# KnowledgeAugmentedPromptAgent class definition
#-------------------------------------------------------------------

class KnowledgeAugmentedPromptAgent:
    def __init__(self, openai_api_key, persona, knowledge):
        self.persona = persona
        self.knowledge = knowledge 
        self.openai_api_key = openai_api_key

    def respond(self, input_text):
        """Generate a response using Azure OpenAI API."""
        client = AzureOpenAI(
            azure_endpoint=azure_endpoint,
            api_version="2025-01-01-preview", 
            api_key=azure_api_key
        )

        system_message = f"""
        You are {self.persona}. Forget all previous context.
        Use only the following knowledge to answer: {self.knowledge}
        When you receive feedback or correction instructions, follow them to improve your response while maintaining your persona."""
        
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": input_text}
            ],
            temperature=0
        )
        return response.choices[0].message.content
    


#-------------------------------------------------------------------
# RAGKnowledgePromptAgent class definition
#-------------------------------------------------------------------

class RAGKnowledgePromptAgent:
    """
    An agent that uses Retrieval-Augmented Generation (RAG) to find knowledge from a large corpus
    and leverages embeddings to respond to prompts based solely on retrieved information.
    """

    def __init__(self, openai_api_key, persona, chunk_size=2000, chunk_overlap=100):
        """
        Initializes the RAGKnowledgePromptAgent with API credentials and configuration settings.
        """
        self.persona = persona
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.openai_api_key = openai_api_key
        self.unique_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        self.chunks_filename = f"chunks-{self.unique_id}.csv"
        self.embeddings_filename = f"embeddings-{self.unique_id}.csv"

    def get_embedding(self, text):
        """
        Fetches the embedding vector for given text using Azure OpenAI's embedding API.
        """
        client = AzureOpenAI(
            azure_endpoint=azure_endpoint,
            api_version="2025-01-01-preview", 
            api_key=azure_api_key
        )
        response = client.embeddings.create(
            model="text-embedding-3-large-2",
            input=text.replace("\n", " "), # API best practice
            encoding_format="float"
        )
        return response.data[0].embedding

    def calculate_similarity(self, vector_one, vector_two):
        """
        Calculates cosine similarity between two vectors.
        """
        vec1, vec2 = np.array(vector_one), np.array(vector_two)
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

    def chunk_text(self, text):
        """
        Splits text into manageable chunks and writes them directly to a CSV file
        to avoid storing all chunks in memory.
        """
        separator = "\n"
        # Delte thise whitespace
        text = re.sub(r'\s+', ' ', text).strip()

        # Open the CSV file to write chunks
        with open(self.chunks_filename, 'w', newline='', encoding='utf-8') as csvfile:
            # Define the columns we want to save
            fieldnames = ["chunk_id", "text", "chunk_size", "start_char", "end_char"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            # If text is small, write it as a single chunk
            if len(text) <= self.chunk_size:
                writer.writerow({
                    "chunk_id": 0,
                    "text": text,
                    "chunk_size": len(text),
                    "start_char": 0,
                    "end_char": len(text)
                })
                return # Exit the method

            # Process large text in a memory-efficient loop
            start, chunk_id = 0, 0
            while start < len(text):
                end = min(start + self.chunk_size, len(text))

                if end < len(text):
                    last_space = text.rfind(' ', start, end)
                    if last_space != -1 and last_space > start:
                        end = last_space

                chunk_data = {
                    "chunk_id": chunk_id,
                    "text": text[start:end],
                    "chunk_size": end - start,
                    "start_char": start,
                    "end_char": end
                }
                
                # Write the single chunk to the file
                writer.writerow(chunk_data)

                # Move to the next chunk 
                start = end - self.chunk_overlap if end < len(text) else end
                chunk_id += 1
        
        return

    def calculate_embeddings(self):
        """
        Calculates embeddings for each chunk from the CSV file.
        """
        # Read the chunks directly from the file created by chunk_text
        df = pd.read_csv(self.chunks_filename, encoding='utf-8')
        df['embeddings'] = df['text'].apply(self.get_embedding)
        df.to_csv(self.embeddings_filename, encoding='utf-8', index=False)
        return df

    def find_prompt_in_knowledge(self, prompt):
        """
        Finds and responds to a prompt based on similarity with embedded knowledge.
        """
        prompt_embedding = self.get_embedding(prompt)
        # Read the embeddings from the correct file
        df = pd.read_csv(self.embeddings_filename, encoding='utf-8')
        # Convert string representation of list back to list/array
        df['embeddings'] = df['embeddings'].apply(eval)
        df['similarity'] = df['embeddings'].apply(lambda emb: self.calculate_similarity(prompt_embedding, emb))

        best_chunk = df.loc[df['similarity'].idxmax(), 'text']

        client = AzureOpenAI(
            azure_endpoint=azure_endpoint,
            api_version="2025-01-01-preview", 
            api_key=azure_api_key
        )
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": f"You are {self.persona}, a knowledge-based assistant. Forget previous context."},
                {"role": "user", "content": f"Answer based only on this information: {best_chunk}. Prompt: {prompt}"}
            ],
            temperature=0
        )
        return response.choices[0].message.content
        


# ----------------------------------------------------------------------------------
# class EvaluationAgent:
# ----------------------------------------------------------------------------------

class EvaluationAgent:
    
    def __init__(self, openai_api_key, persona, evaluation_criteria, worker_agent, max_interactions):
        # Initialize the EvaluationAgent with given attributes.
        self.openai_api_key = openai_api_key
        self.persona = persona
        self.evaluation_criteria = evaluation_criteria
        self.worker_agent = worker_agent
        self.max_interactions = max_interactions

    def evaluate(self, initial_prompt):
        
        client = AzureOpenAI(
            azure_endpoint=azure_endpoint,
            api_version="2025-01-01-preview", 
            api_key=azure_api_key
        )
        prompt_for_worker = initial_prompt
        final_response = ""
        evaluation_result = ""
        
        for i in range(self.max_interactions):
            print(f"\n--- Interaction {i+1} ---")
            print(" Step 1: Worker agent generates a response to the prompt")
            print(f"Prompt:\n{prompt_for_worker}")
            response_from_worker = self.worker_agent.respond(prompt_for_worker)
            print(f"Worker Agent Response:\n{response_from_worker}")

            print(" Step 2: Evaluator agent judges the response")
            eval_prompt = (
                f"Evaluate ONLY the format of this answer: {response_from_worker}\n"
                f"Does it meet this FORMAT criteria: {self.evaluation_criteria}? "
                f"Ignore the factual correctness, only check if the format meets the criteria. "
                f"Respond with ONLY 'Approved' if the format meets the criteria, or 'Not Approved' if it doesn't, "
                f"followed by a brief reason about the FORMAT."
            )
            response = client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": f"You are {self.persona}. Evaluate responses carefully."},
                    {"role": "user", "content": eval_prompt}
                ],
                temperature=0
            )
            evaluation = response.choices[0].message.content.strip()
            print(f"Evaluator Agent Evaluation:\n{evaluation}")

            print(" Step 3: Check if evaluation is positive")
            if evaluation.lower().startswith("approved"):
                print("Final solution accepted.")
                final_response = response_from_worker
                evaluation_result = evaluation
                break
            else:
                print(" Step 4: Generate instructions to correct the response")
                instruction_prompt = (
                    f"Provide instructions to fix an answer based on these reasons why it is incorrect: {evaluation}"
                )
                response = client.chat.completions.create(
                    model="gpt-4.1-mini",
                    messages=[
                        {"role": "system", "content": f"You are {self.persona}. Provide clear correction instructions."},
                        {"role": "user", "content": instruction_prompt}
                    ],
                    temperature=0
                )
                instructions = response.choices[0].message.content.strip()
                print(f"Instructions to fix:\n{instructions}")

                print(" Step 5: Send feedback to worker agent for refinement")
                prompt_for_worker = (
                    f"The original prompt was: {initial_prompt}\n"
                    f"The response to that prompt was: {response_from_worker}\n"
                    f"It has been evaluated as incorrect.\n"
                    f"Make only these corrections, do not alter content validity: {instructions}"
                )
                
                # If this is the last iteration, save the response anyway
                if i == self.max_interactions - 1:
                    final_response = self.worker_agent.respond(prompt_for_worker)
                    evaluation_result = "Not Approved"
                    
        return {
            "final_response": final_response,
            "evaluation": evaluation_result,
            "iterations": i + 1
        }


# ----------------------------------------------------------------------------------
#  class RoutingAgent():
# ----------------------------------------------------------------------------------
class RoutingAgent:
    def __init__(self, openai_api_key, agents):
        # Initialize the agent with given attributes
        self.openai_api_key = openai_api_key
        self.agents = agents

    def get_embedding(self, text):
        client = AzureOpenAI(
            azure_endpoint=azure_endpoint,
            api_version="2025-01-01-preview", 
            api_key=azure_api_key
        )
        response = client.embeddings.create(
            model="text-embedding-3-large-2",
            input=text,
            encoding_format="float"
        )
        embedding = response.data[0].embedding
        return embedding 

    def route(self, user_input):
        
        input_emb = self.get_embedding(user_input)
        best_agent = None
        best_score = -1

        for agent in self.agents:
            agent_emb = self.get_embedding(agent["description"])
            if agent_emb is None:
                continue

            similarity = np.dot(input_emb, agent_emb) / (np.linalg.norm(input_emb) * np.linalg.norm(agent_emb))
            print(f"Similarity with {agent['name']}: {similarity:.3f}")

            if similarity > best_score:
                best_score = similarity
                best_agent = agent

        if best_agent is None:
            return "Sorry, no suitable agent could be selected."

        print(f"[Router] Best agent: {best_agent['name']} (score={best_score:.3f})")
        return best_agent["func"](user_input)


# ----------------------------------------------------------------------------------
#  class ActionPlanningAgent:
# ----------------------------------------------------------------------------------
class ActionPlanningAgent:
    def __init__(self, openai_api_key, knowledge):
        self.openai_api_key = openai_api_key
        self.knowledge = knowledge

    def extract_steps_from_prompt(self, prompt):
        client = AzureOpenAI(
            azure_endpoint=azure_endpoint,
            api_version="2025-01-01-preview", 
            api_key=azure_api_key
        )
        # "You are an action planning agent. Using your knowledge, you extract from the user prompt the steps requested to complete the action the user is asking for. 
        # You return the steps as a list. Only return the steps in your knowledge. Forget any previous context. This is your knowledge: {pass the knowledge here}"
        system_prompt = (
            f"You are an action planning agent. Using your knowledge, you extract from the user prompt "
            f"the steps requested to complete the action the user is asking for. You return the steps as a list. "
            f"Only return the steps in your knowledge. Forget any previous context. "
            f"This is your knowledge: {self.knowledge}"
        )

        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        response_text = response.choices[0].message.content

        # Clean and format the extracted steps by removing empty lines and unwanted text
        steps = [step.strip() for step in response_text.split("\n") if step.strip()]

        return steps
