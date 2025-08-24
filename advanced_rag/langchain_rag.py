"""
Advanced RAG Implementation using Langchain
Step 3: Integrate Langchain with vector store
"""
import os
import sys
sys.path.append('..')

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings
from typing import List, Dict, Any
import json
from config_advanced import *
from vector_store import VectorStoreManager

class AdvancedRAGSystem:
    def __init__(self):
        self.vector_manager = VectorStoreManager()
        self.llm = None
        self.embeddings = None
        self.vectorstore = None
        self.retriever = None
        self.rag_chain = None
        self.setup_langchain_components()
    
    def setup_langchain_components(self):
        """Initialize all Langchain components"""
        print("🔧 Setting up Langchain components...")
        
        # Initialize LLM
        self.llm = ChatGoogleGenerativeAI(
            model=LLM_MODEL,
            google_api_key=GOOGLE_API_KEY,
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS
        )
        print("✅ LLM initialized")
        
        # Initialize embeddings
        self.embeddings = SentenceTransformerEmbeddings(
            model_name=EMBEDDING_MODEL
        )
        print("✅ Embeddings initialized")
        
        # Connect to existing vector store
        self.setup_vectorstore()
        
        # Create RAG chain
        self.create_rag_chain()
    
    def setup_vectorstore(self):
        """Setup Langchain vector store from existing ChromaDB"""
        print("🔗 Connecting to vector store...")
        
        try:
            # Connect to existing ChromaDB
            self.vectorstore = Chroma(
                persist_directory=VECTOR_DB_PATH,
                embedding_function=self.embeddings,
                collection_name="survey_responses"
            )
            
            # Create retriever
            self.retriever = self.vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 5}
            )
            
            print(f"✅ Connected to vector store with {self.vectorstore._collection.count()} documents")
            
        except Exception as e:
            print(f"❌ Failed to connect to vector store: {str(e)}")
            print("💡 Try running vector_store.py first to populate the database")
            raise
    
    def create_rag_chain(self):
        """Create the RAG chain with prompt template"""
        print("⛓️ Creating RAG chain...")
        
        # Define the prompt template
        prompt_template = """You are an expert analyst for social impact programs. Your role is to analyze survey data and provide evidence-based insights about youth development programs.

Context from survey responses:
{context}

Question: {question}

Instructions:
1. Analyze the provided survey responses carefully
2. Identify key themes and patterns in the evidence
3. Provide specific quotes and examples from the responses
4. Structure your answer using the "Quantify then Qualify" methodology:
   - Start with quantitative summary (how many responses, what patterns)
   - Follow with qualitative insights (themes, quotes, stories)
5. Be honest about limitations in the data
6. Focus on actionable insights for program improvement

Answer:"""

        prompt = ChatPromptTemplate.from_template(prompt_template)
        
        # Create the RAG chain
        def format_docs(docs):
            formatted = []
            for i, doc in enumerate(docs, 1):
                metadata = doc.metadata
                org = metadata.get('charity_name', 'Unknown')
                age = metadata.get('age_group', 'Unknown')
                question = metadata.get('question_text', 'Unknown')
                
                formatted.append(f"""
Response {i} (Organization: {org}, Age Group: {age}):
Question: {question}
Response: {doc.page_content}
""")
            return "\n".join(formatted)
        
        self.rag_chain = (
            {"context": self.retriever | format_docs, "question": RunnablePassthrough()}
            | prompt
            | self.llm
            | StrOutputParser()
        )
        
        print("✅ RAG chain created successfully")
    
    def query(self, question: str) -> Dict[str, Any]:
        """Process a query using the advanced RAG system"""
        print(f"🤔 Processing query: '{question}'")
        
        try:
            # Get relevant documents first (for metadata)
            relevant_docs = self.retriever.get_relevant_documents(question)
            
            # Generate answer using RAG chain
            answer = self.rag_chain.invoke(question)
            
            # Format response
            response = {
                'question': question,
                'answer': answer,
                'source_documents': [
                    {
                        'text': doc.page_content,
                        'metadata': doc.metadata,
                        'organization': doc.metadata.get('charity_name', 'Unknown'),
                        'age_group': doc.metadata.get('age_group', 'Unknown'),
                        'question_text': doc.metadata.get('question_text', 'Unknown')
                    }
                    for doc in relevant_docs
                ],
                'evidence_count': len(relevant_docs),
                'system_type': 'advanced_langchain_rag'
            }
            
            print(f"✅ Generated answer with {len(relevant_docs)} source documents")
            return response
            
        except Exception as e:
            print(f"❌ Query processing failed: {str(e)}")
            return {
                'question': question,
                'answer': f"Error processing query: {str(e)}",
                'source_documents': [],
                'evidence_count': 0,
                'system_type': 'advanced_langchain_rag',
                'error': str(e)
            }
    
    def test_advanced_queries(self):
        """Test the advanced RAG system with complex queries"""
        print("\n🧪 Testing Advanced RAG Queries")
        print("=" * 50)
        
        test_queries = [
            "How do creative programs like filmmaking build confidence in young people?",
            "What evidence shows that these programs help participants make social connections?",
            "Compare the impact on different age groups - what patterns emerge?",
            "What specific challenges do participants mention overcoming?",
            "How do participants describe their future aspirations after the program?",
            "What role does teamwork play in the program experience?",
            "Are there any negative experiences or areas for improvement mentioned?"
        ]
        
        results = []
        
        for query in test_queries:
            print(f"\n{'='*60}")
            print(f"Query: {query}")
            print('='*60)
            
            result = self.query(query)
            results.append(result)
            
            print(f"Evidence Count: {result['evidence_count']}")
            print(f"Answer Length: {len(result['answer'])} characters")
            print("\nAnswer Preview:")
            print(result['answer'][:300] + "..." if len(result['answer']) > 300 else result['answer'])
            
            if result['source_documents']:
                print(f"\nSource Organizations: {set(doc['organization'] for doc in result['source_documents'])}")
        
        return results
    
    def compare_with_simple_system(self, query: str):
        """Compare results with the simple system"""
        print(f"\n🔄 Comparing Systems for: '{query}'")
        print("-" * 50)
        
        # Get advanced result
        advanced_result = self.query(query)
        
        # Get simple result (import here to avoid conflicts)
        try:
            from simple_rag_system import SimpleRAGSystem
            simple_system = SimpleRAGSystem()
            simple_result = simple_system.process_query(query)
            
            print("ADVANCED SYSTEM:")
            print(f"  Evidence: {advanced_result['evidence_count']} documents")
            print(f"  Answer: {len(advanced_result['answer'])} chars")
            print(f"  Organizations: {set(doc['organization'] for doc in advanced_result['source_documents'])}")
            
            print("\nSIMPLE SYSTEM:")
            print(f"  Evidence: {simple_result['evidence_count']} documents")
            print(f"  Answer: {len(simple_result['answer'])} chars")
            print(f"  Organizations: {set(ev.get('charity_name', 'Unknown') for ev in simple_result['source_evidence'])}")
            
            return {
                'query': query,
                'advanced': advanced_result,
                'simple': simple_result
            }
            
        except Exception as e:
            print(f"❌ Comparison failed: {str(e)}")
            return None

if __name__ == "__main__":
    # Initialize and test the advanced RAG system
    print("🚀 ADVANCED RAG SYSTEM TEST")
    print("=" * 50)
    
    try:
        rag = AdvancedRAGSystem()
        
        # Run tests
        results = rag.test_advanced_queries()
        
        # Compare with simple system on a few queries
        comparison_queries = [
            "How do programs build confidence?",
            "What helps young people make friends?",
            "Show me evidence of creative engagement"
        ]
        
        print(f"\n{'='*70}")
        print("SYSTEM COMPARISON")
        print('='*70)
        
        for query in comparison_queries:
            rag.compare_with_simple_system(query)
        
        print("\n✅ Advanced RAG system testing complete!")
        
    except Exception as e:
        print(f"❌ Advanced RAG system failed: {str(e)}")
        print("\n💡 Make sure to:")
        print("1. Install requirements: pip install -r requirements_advanced.txt")
        print("2. Populate vector store: python vector_store.py")
        print("3. Check your .env file has all required API keys")