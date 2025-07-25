import requests
import json
from .base_agents import KnowledgeAugmentedPromptAgent, RoutingAgent, DirectPromptAgent
from langfuse.openai import AzureOpenAI
import os
from dotenv import load_dotenv
import numpy as np
try:
    from .vivavis import search_documents, generate_answer, format_search_results
except ImportError:
    # Fallback for different import scenarios
    import sys
    sys.path.append(os.path.dirname(__file__))
    from vivavis import search_documents, generate_answer, format_search_results

# Load environment variables from .env file
load_dotenv()

# Load Azure OpenAI configuration from environment variables
azure_endpoint = os.getenv("AZURE_GPT_ENDPOINT")
azure_api_key = os.getenv("AZURE_GPT_KEY")
openai_api_key = azure_api_key  # For backwards compatibility

# VIVAVIS Company Knowledge Base
sgop_world_company_info = """
Smartfox ist unser digitaler Bibliothekar der speziell dazu angestellt wurde, um die Art und Weise, wie Mitarbeiter auf Informationen zugreifen, grundlegend zu verändern.
Er ist die schnittstelle zur SGOP World, dem Wikipedia der Netzebene 7 und unserer Hauseigenen Wissensdatenbank rund um die Grid Transformation.
SGOP World ist eine intelligente Wissensplattform, die für den modernen Netzbetrieb entwickelt wurde. Ihre Kernfunktion besteht darin, die Art und Weise, wie Mitarbeiter auf Informationen zugreifen, grundlegend zu verändern. Dies wird durch eine fortschrittliche Augmented RAG (Retrieval-Augmented Generation) Architektur realisiert, die weit über eine herkömmliche Suche hinausgeht. Im Hintergrund arbeitet ein Multi-Agent-System: Spezialisierte KI-Agenten, jeder mit Expertise in einem anderen Fachbereich wie Regulatorik oder Technik, kollaborieren, um die bestmögliche Antwort auf komplexe Anfragen zu formulieren. Der Nutzer interagiert dabei nahtlos mit Smartfox, dem zentralen Assistenten, der als intelligente Schnittstelle zu dieser leistungsstarken Technologie dient und präzise, kontextbezogene Antworten liefert.
Die Plattform fungiert als eine zentrale und stets aktuelle Wissensbasis, die ein breites Spektrum an Themen abdeckt. Sie bündelt alle notwendigen Betriebsunterlagen wie Schritt-für-Schritt-Anleitungen und Funktionsvideos, weiterführende technische Spezifikationen, Handlungsempfehlungen für Projekte und praxisnahe Einblicke aus erfolgreichen Kundenimplementierungen. Ein wesentlicher Bestandteil sind zudem die regulatorischen Anforderungen, die laufend aktualisiert werden, um die Einhaltung der Compliance sicherzustellen. Der Smartfox Assistent ermöglicht den direkten Dialog mit dieser Wissensbasis, während die intelligente Vernetzung der Dokumente die Beantwortung komplexer, quellenübergreifender Fragestellungen ermöglicht.
In der Praxis löst SGOP World alltägliche Herausforderungen für verschiedenste Anwender. Ein Mitarbeiter, der wissen möchte, wie ein Anschlussgesuch zu erstellen ist, erhält eine sofortige Anleitung samt Videos und den passenden Formularen. Ein Verteilnetzbetreiber kann rechtliche Unsicherheiten, beispielsweise zur Verbrauchsregulierung, in Sekundenschnelle klären, da die Plattform verständliche Antworten mit direkten Verweisen auf die Gesetzestexte liefert. Ebenso findet ein Netztechniker auf der Suche nach einer spezifischen technischen Vorgabe sofort die exakte Passage, inklusive relevanter Diagramme oder Tabellen, ohne langwierig ganze Handbücher durchsuchen zu müssen.
Der klare Mehrwert der SGOP World liegt in der signifikanten Effizienzsteigerung und der Beschleunigung von betrieblichen Prozessen. Durch die Bereitstellung fundierter Informationen auf Knopfdruck werden Entscheidungsprozesse beschleunigt und die Einhaltung komplexer Vorschriften vereinfacht. Gleichzeitig sichert die Plattform wertvolles Unternehmenswissen zentral und dauerhaft. Dank der intuitiven Bedienung ist sie ohne lange Einarbeitung nutzbar und führt so zu einer schnellen und nachhaltigen Verbesserung der täglichen Arbeit im Netzbetrieb.

VIVAVIS AG is a leading technology company specializing in smart grid solutions and energy management systems. 
The company develops SGOP (Smart Grid Operations Platform) which helps utility companies manage their electrical networks efficiently.
VIVAVIS offers solutions for network control, data management, and energy optimization.
Key products include SmartControl, SmartDisplay, SmartPreview, and SmartBase.
The company operates in DACH region (Germany, Austria, Switzerland) and provides comprehensive support for energy transition.
VIVAVIS focuses on IT security, compliance with industry standards like BDEW Whitepaper, and offers 24/7 support services.
The company has expertise in network optimization, flexibility management, and integration with existing utility infrastructure.
"""

class GeneralQueryAgent:
    """Agent that handles general queries by calling the existing chat_stream endpoint"""
    
    def __init__(self):
        self.name = "General Query Agent"
    
    def respond(self, prompt, request_data=None):
        try:
            if not request_data:
                return f"[General Query Agent] No request data provided for: {prompt}"
            
            print(f"🔄 General Query Agent making HTTP request to chat_stream...")
            
            # Prepare the payload for the chat_stream endpoint
            payload = {
                "prompt": prompt,
                "language": request_data.get("language", "de"),
                "profile": request_data.get("profile", "STAFF"),
                "personaId": request_data.get("persona_id", 1),
                "slide": request_data.get("slide", {"id": "general", "title": "General Query"}),
                "category": request_data.get("category", {"name": "general"}),
                "framework_mode": request_data.get("framework_mode", False),
                "chatHistory": request_data.get("chat_history", [])
            }
            
            # Get the authorization header directly from the original request
            authorization_header = request_data.get("authorization_header")
            
            headers = {
                "Content-Type": "application/json"
            }
            
            # Add authorization header if available
            if authorization_header:
                headers["Authorization"] = authorization_header
                print(f"🔑 Using Authorization header: {authorization_header[:20]}...")
            else:
                print("⚠️ No Authorization header found in request data")
            
            # Make HTTP request to the chat_stream endpoint
            url = "http://localhost:5000/chat/chat_stream"
            
            print(f"📡 Calling {url} with payload...")
            response = requests.post(url, json=payload, headers=headers, stream=True)
            
            if response.status_code == 200:
                # Collect streaming response
                content_parts = []
                for line in response.iter_lines():
                    if line:
                        try:
                            chunk_data = json.loads(line.decode('utf-8'))
                            if chunk_data.get("type") == "content" and chunk_data.get("content"):
                                content_parts.append(chunk_data["content"])
                        except json.JSONDecodeError:
                            continue
                
                final_content = "".join(content_parts).strip()
                if final_content:
                    return f"[General Query Agent - RAG Pipeline] {final_content}"
                else:
                    return "[General Query Agent] RAG pipeline completed but no content generated"
            else:
                return f"[General Query Agent] Error from chat_stream: HTTP {response.status_code} - {response.text}"
                
        except requests.exceptions.RequestException as e:
            print(f"❌ General Query Agent HTTP error: {str(e)}")
            return f"[General Query Agent] HTTP request failed: {str(e)}"
        except Exception as e:
            print(f"❌ General Query Agent error: {str(e)}")
            return f"[General Query Agent] Error accessing RAG pipeline: {str(e)}"

class DeepResearchAgent:
    """Agent that creates detailed research plans for complex, multifaceted queries"""
    
    def __init__(self, openai_api_key):
        self.openai_api_key = openai_api_key
        self.persona = "You are a research planning specialist who creates comprehensive research strategies."
        self.name = "Deep Research Agent"
    
    def respond(self, prompt, request_data=None):
        try:
            research_plan = self._create_research_plan(prompt)
            return f"[Deep Research Agent] Research Plan Created:\n\n{research_plan}\n\n[Note: This plan will be passed to the orchestrator agent for execution]"
        except Exception as e:
            return f"[Deep Research Agent] Error creating research plan: {str(e)}"
    
    def _create_research_plan(self, prompt):
        """Create a detailed research plan for complex queries"""
        plan = f"""
RESEARCH PLAN FOR: {prompt}

1. QUERY ANALYSIS:
   - Complexity Level: High (Multi-faceted query requiring deep research)
   - Key Topics Identified: [To be analyzed by orchestrator]
   - Research Scope: Comprehensive analysis required

2. RESEARCH PHASES:
   Phase 1: Initial Information Gathering
   - Search company documentation
   - Review technical specifications
   - Identify relevant standards and regulations
   
   Phase 2: Detailed Analysis
   - Cross-reference multiple sources
   - Analyze compliance requirements
   - Review implementation case studies
   
   Phase 3: Synthesis and Validation
   - Compile findings
   - Validate against current standards
   - Prepare comprehensive response

3. EXPECTED OUTPUTS:
   - Detailed technical analysis
   - Compliance information
   - Implementation recommendations
   - Supporting documentation references

4. ORCHESTRATOR INSTRUCTIONS:
   - Execute research phases sequentially
   - Validate findings at each step
   - Compile final comprehensive response
   - Include relevant document citations
"""
        return plan

class VivavisCompanyAgent:
    """Agent that handles queries about VIVAVIS company using RAG from the vivavis_basic_knowledge collection"""
    
    def __init__(self):
        self.name = "VIVAVIS Company Agent"
    
    def respond(self, prompt, request_data=None):
        try:
            print(f"🏢 VIVAVIS Company Agent processing query: {prompt[:50]}...")
            
            # Search for relevant documents in the VIVAVIS collection
            results = search_documents(prompt, k=5)
            
            if not results:
                return "[VIVAVIS Company Agent] Ich konnte keine relevanten Informationen über VIVAVIS in der Wissensdatenbank finden. Bitte versuchen Sie eine spezifischere Frage oder wenden Sie sich an den Support."
            
            print(f"📄 Found {len(results)} relevant documents in VIVAVIS collection")
            
            # Format the search results into context
            context = format_search_results(results)
            
            # Generate answer using the RAG pipeline
            answer = generate_answer(prompt, context)
            
            return f"[VIVAVIS Company Agent - RAG] {answer}"
            
        except Exception as e:
            print(f"❌ VIVAVIS Company Agent error: {str(e)}")
            return f"[VIVAVIS Company Agent] Fehler beim Abrufen der VIVAVIS-Informationen: {str(e)}. Bitte versuchen Sie es erneut oder wenden Sie sich an den Support."

class BasicAugmentedPromptAgent:
    """Agent that handles simple questions using company knowledge and basic information about SGOP World without RAG and vector search"""
    
    def __init__(self, openai_api_key, knowledge):
        self.agent = KnowledgeAugmentedPromptAgent(
            openai_api_key=openai_api_key,
            persona="You are a helpful SGOP World assistant who is called Smartfox Little Helper who answers simple questions politely and concisely.",
            knowledge=knowledge
        )
        self.name = "SGOP World Assistant"
    
    def respond(self, prompt, request_data=None):
        try:
            response = self.agent.respond(prompt)
            return f"[VIVAVIS Assistant] {response}"
        except Exception as e:
            return f"[VIVAVIS Assistant] I'm here to help with basic questions about our Platform SGOP World. Error: {str(e)}"

# Enhanced RoutingAgent for the agentic workflow
class AgenticRoutingAgent(RoutingAgent):
    """Enhanced routing agent that handles the agentic workflow"""
    
    def __init__(self, openai_api_key, agents):
        super().__init__(openai_api_key, agents)
        self.name = "Agentic Routing Agent"
    
    def route(self, user_input, request_data=None):
        """Route user input to the most appropriate agent with request data"""
        try:
            input_emb = self.get_embedding(user_input)
            best_agent = None
            best_score = -1

            print(f"🧠 Analyzing query for routing: {user_input[:50]}...")

            for agent in self.agents:
                agent_emb = self.get_embedding(agent["description"])
                if agent_emb is None:
                    continue

                similarity = np.dot(input_emb, agent_emb) / (np.linalg.norm(input_emb) * np.linalg.norm(agent_emb))
                print(f"📊 Similarity with {agent['name']}: {similarity:.3f}")

                if similarity > best_score:
                    best_score = similarity
                    best_agent = agent

            if best_agent is None:
                return "[Routing Error] No suitable agent could be selected for this query."

            print(f"🎯 Selected agent: {best_agent['name']} (confidence: {best_score:.3f})")
            
            # Call the selected agent with both user_input and request_data
            if 'func_with_data' in best_agent:
                return best_agent["func_with_data"](user_input, request_data)
            else:
                return best_agent["func"](user_input)
                
        except Exception as e:
            return f"[Routing Error] Failed to route query: {str(e)}"

# Initialize the agents
general_query_agent = GeneralQueryAgent()
deep_research_agent = DeepResearchAgent(openai_api_key)
vivavis_company_agent = VivavisCompanyAgent()
sgop_world_assistant = BasicAugmentedPromptAgent(openai_api_key, sgop_world_company_info)

# Define the agent configurations for the agentic workflow
agentic_agents = [
    {
        "name": "General Query Agent",
        "description": "Handle standard questions about SGOP technical documentation, SGOP user guides, SGOP regulations and compliance, smart grid operations, network control, and general utility management topics that require RAG search from technical documentation, regulation, best practices and trends in grid level 7 'Netzebene 7'",
        "func": lambda x: general_query_agent.respond(x),
        "func_with_data": lambda x, data: general_query_agent.respond(x, data)
    },
    {
        "name": "Deep Research Agent", 
        "description": "Handle complex, multifaceted queries that require comprehensive analysis of our SGOP solution, multiple research phases, detailed technical investigation, or reports requiring extensive research, it connects different source of information and knowledge to get a deep understanding of the topic",
        "func": lambda x: deep_research_agent.respond(x),
        "func_with_data": lambda x, data: deep_research_agent.respond(x, data)
    },
    {
        "name": "VIVAVIS Company Agent",
        "description": "Handle questions specifically about VIVAVIS company information, company background, Vivavis products overview, Vivavis business information, company services, and general VIVAVIS corporate knowledge",
        "func": lambda x: vivavis_company_agent.respond(x),
        "func_with_data": lambda x, data: vivavis_company_agent.respond(x, data)
    },
    {
        "name": "SGOP World Assistant",
        "description": "Answers question about 'SGOP World'. Answer simple greetings, basic casual conversation, polite responses, and very simple questions about the functionality of SGOP World and all questions relating to Smartfox. that don't require technical documentation or company knowledge, like Hello, How are you, What is your name, etc.",
        "func": lambda x: sgop_world_assistant.respond(x),
        "func_with_data": lambda x, data: sgop_world_assistant.respond(x, data)
    }
]

# Create the agentic routing agent
agentic_routing_agent = AgenticRoutingAgent(openai_api_key, agentic_agents)

# Test function for development
def test_agentic_routing():
    """Test function to verify the agentic routing works correctly"""
    test_prompts = [
        "Hello, how are you?",  # Should go to Basic Company Assistant
        "What is SGOP and how does it work in detail with all technical specifications?",  # Should go to Deep Research Agent
        "Tell me about VIVAVIS company and their products",  # Should go to VIVAVIS Company Agent
        "How do I configure network parameters in SmartControl?"  # Should go to General Query Agent
    ]

    print("Testing Agentic Routing Agent:")
    print("=" * 60)

    for i, prompt in enumerate(test_prompts, 1):
        print(f"\nTest {i}: {prompt}")
        print("-" * 40)
        response = agentic_routing_agent.route(prompt)
        print(f"Response: {response}")
        print("-" * 40)

if __name__ == "__main__":
    test_agentic_routing()