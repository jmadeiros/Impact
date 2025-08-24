"""
Conversational RAG System - Chat-like responses
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

class ConversationalRAGSystem:
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
        print("🔧 Setting up Conversational RAG...")
        
        # Initialize LLM
        self.llm = ChatGoogleGenerativeAI(
            model=LLM_MODEL,
            google_api_key=GOOGLE_API_KEY,
            temperature=0.3,  # Slightly higher for more conversational tone
            max_tokens=1000
        )
        print("✅ LLM initialized")
        
        # Initialize embeddings
        self.embeddings = SentenceTransformerEmbeddings(
            model_name=EMBEDDING_MODEL
        )
        print("✅ Embeddings initialized")
        
        # Connect to existing vector store
        self.setup_vectorstore()
        
        # Create conversational RAG chain
        self.create_conversational_chain()
    
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
            raise
    
    def create_conversational_chain(self):
        """Create a conversational RAG chain"""
        print("💬 Creating conversational chain...")
        
        # Conversational prompt template
        prompt_template = """You are a friendly and knowledgeable assistant helping someone understand insights from youth program survey data. 

Based on the survey responses below, please answer the user's question in a natural, conversational way. Be helpful, engaging, and cite specific examples from the data.

Survey responses:
{context}

User question: {question}

Please provide a helpful, conversational response that:
- Directly answers their question
- Uses specific examples and quotes from the survey data
- Explains what the data shows in plain language
- Mentions which organizations, age groups, and genders the insights come from when relevant
- Analyzes gender differences when asked about them (gender data is available: Male/Female)
- Is warm and engaging, like you're having a conversation

Response:"""

        prompt = ChatPromptTemplate.from_template(prompt_template)
        
        # Create the RAG chain
        def format_docs(docs):
            formatted = []
            for i, doc in enumerate(docs, 1):
                metadata = doc.metadata
                org = metadata.get('charity_name', 'Unknown')
                age = metadata.get('age_group', 'Unknown')
                gender = metadata.get('gender', 'Unknown')
                question = metadata.get('question_text', 'Unknown')
                
                formatted.append(f"""
Survey Response {i}:
Organization: {org}
Age Group: {age}
Gender: {gender}
Question Asked: {question}
Response: {doc.page_content}
""")
            return "\n".join(formatted)
        
        self.rag_chain = (
            {"context": self.retriever | format_docs, "question": RunnablePassthrough()}
            | prompt
            | self.llm
            | StrOutputParser()
        )
        
        print("✅ Conversational chain created successfully")
    
    def chat(self, question: str) -> Dict[str, Any]:
        """Have a conversation about the survey data"""
        print(f"💬 User: {question}")
        
        try:
            # Get relevant documents first (for metadata)
            relevant_docs = self.retriever.get_relevant_documents(question)
            
            # Generate conversational answer
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
                        'gender': doc.metadata.get('gender', 'Unknown'),
                        'question_text': doc.metadata.get('question_text', 'Unknown')
                    }
                    for doc in relevant_docs
                ],
                'evidence_count': len(relevant_docs),
                'system_type': 'conversational_rag'
            }
            
            print(f"🤖 Assistant: {answer}")
            return response
            
        except Exception as e:
            print(f"❌ Chat failed: {str(e)}")
            return {
                'question': question,
                'answer': f"Sorry, I encountered an error: {str(e)}",
                'source_documents': [],
                'evidence_count': 0,
                'system_type': 'conversational_rag',
                'error': str(e)
            }

def demo_conversation():
    """Demo conversation with the system"""
    print("🚀 CONVERSATIONAL RAG DEMO")
    print("=" * 50)
    
    # Initialize system
    chat_system = ConversationalRAGSystem()
    
    # Demo questions
    questions = [
        "How do young people feel about school and their confidence?",
        "What creative activities help young people the most?",
        "Do these programs actually help with stress?",
        "What challenges do participants face?",
        "Which organizations seem most effective?"
    ]
    
    for question in questions:
        print(f"\n{'='*60}")
        response = chat_system.chat(question)
        print(f"\nEvidence from: {len(response['source_documents'])} responses")
        print(f"Organizations: {set(doc['organization'] for doc in response['source_documents'])}")
        print('='*60)

if __name__ == "__main__":
    demo_conversation()