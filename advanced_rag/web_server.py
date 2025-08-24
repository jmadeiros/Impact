"""
Web Server for Advanced RAG System
Provides web chat interface and API endpoints
"""
import os
import sys
sys.path.append('..')

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, List
import uvicorn
import json
from datetime import datetime

# Import our conversational RAG system
from conversational_rag import ConversationalRAGSystem

# Initialize FastAPI app
app = FastAPI(
    title="Advanced RAG System - Impact Intelligence",
    description="Conversational interface for youth program survey insights",
    version="1.0.0"
)

# Global RAG system instance
rag_system = None
chat_history = []

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"

class ChatResponse(BaseModel):
    message: str
    evidence_count: int
    organizations: List[str]
    age_groups: List[str]
    genders: List[str]
    timestamp: str
    session_id: str

@app.on_event("startup")
async def startup_event():
    """Initialize the RAG system on startup"""
    global rag_system
    try:
        print("🚀 Initializing Advanced RAG System...")
        rag_system = ConversationalRAGSystem()
        print("✅ Advanced RAG System ready!")
    except Exception as e:
        print(f"❌ Failed to initialize RAG system: {str(e)}")
        print("💡 Make sure vector store is populated and API keys are set")

@app.get("/", response_class=HTMLResponse)
async def get_chat_interface():
    """Serve the main chat interface"""
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Advanced RAG - Impact Intelligence</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        
        .chat-container {
            width: 90%;
            max-width: 800px;
            height: 80vh;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        
        .chat-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            text-align: center;
        }
        
        .chat-header h1 {
            font-size: 24px;
            margin-bottom: 5px;
        }
        
        .chat-header p {
            opacity: 0.9;
            font-size: 14px;
        }
        
        .chat-messages {
            flex: 1;
            padding: 20px;
            overflow-y: auto;
            background: #f8f9fa;
        }
        
        .message {
            margin-bottom: 20px;
            display: flex;
            align-items: flex-start;
        }
        
        .message.user {
            justify-content: flex-end;
        }
        
        .message-content {
            max-width: 70%;
            padding: 15px 20px;
            border-radius: 20px;
            line-height: 1.5;
        }
        
        .message.user .message-content {
            background: #667eea;
            color: white;
            border-bottom-right-radius: 5px;
        }
        
        .message.assistant .message-content {
            background: white;
            border: 1px solid #e9ecef;
            border-bottom-left-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        }
        
        .message-meta {
            font-size: 12px;
            color: #6c757d;
            margin-top: 5px;
            padding: 0 20px;
        }
        
        .evidence-badge {
            display: inline-block;
            background: #28a745;
            color: white;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 11px;
            margin-right: 5px;
        }
        
        .chat-input {
            padding: 20px;
            background: white;
            border-top: 1px solid #e9ecef;
        }
        
        .input-group {
            display: flex;
            gap: 10px;
        }
        
        .input-group input {
            flex: 1;
            padding: 15px 20px;
            border: 2px solid #e9ecef;
            border-radius: 25px;
            font-size: 16px;
            outline: none;
            transition: border-color 0.3s;
        }
        
        .input-group input:focus {
            border-color: #667eea;
        }
        
        .input-group button {
            padding: 15px 25px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            font-size: 16px;
            transition: background 0.3s;
        }
        
        .input-group button:hover {
            background: #5a6fd8;
        }
        
        .input-group button:disabled {
            background: #ccc;
            cursor: not-allowed;
        }
        
        .loading {
            display: none;
            text-align: center;
            padding: 20px;
            color: #6c757d;
        }
        
        .loading.show {
            display: block;
        }
        
        .suggestions {
            padding: 10px 20px;
            background: #f8f9fa;
            border-top: 1px solid #e9ecef;
        }
        
        .suggestions h4 {
            font-size: 14px;
            color: #6c757d;
            margin-bottom: 10px;
        }
        
        .suggestion-buttons {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }
        
        .suggestion-btn {
            padding: 8px 15px;
            background: white;
            border: 1px solid #dee2e6;
            border-radius: 15px;
            cursor: pointer;
            font-size: 13px;
            transition: all 0.3s;
        }
        
        .suggestion-btn:hover {
            background: #667eea;
            color: white;
            border-color: #667eea;
        }
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="chat-header">
            <h1>🎯 Advanced RAG - Impact Intelligence</h1>
            <p>Ask questions about youth program survey data and get evidence-based insights</p>
        </div>
        
        <div class="chat-messages" id="chatMessages">
            <div class="message assistant">
                <div class="message-content">
                    👋 Hi! I'm your Advanced RAG assistant. I can help you understand insights from youth program survey data using semantic search and AI analysis.
                    <br><br>
                    Try asking me questions like:
                    <ul style="margin-top: 10px; padding-left: 20px;">
                        <li>"How do programs build confidence in young people?"</li>
                        <li>"What helps teenagers make friends?"</li>
                        <li>"Which creative activities are most effective?"</li>
                    </ul>
                </div>
            </div>
        </div>
        
        <div class="loading" id="loading">
            <div>🤔 Analyzing survey data with semantic search...</div>
        </div>
        
        <div class="suggestions">
            <h4>💡 Try these questions:</h4>
            <div class="suggestion-buttons">
                <button class="suggestion-btn" onclick="askQuestion('How do programs build confidence?')">Build Confidence</button>
                <button class="suggestion-btn" onclick="askQuestion('What helps young people make friends?')">Make Friends</button>
                <button class="suggestion-btn" onclick="askQuestion('Which creative activities work best?')">Creative Activities</button>
                <button class="suggestion-btn" onclick="askQuestion('How do programs help with school stress?')">School Stress</button>
                <button class="suggestion-btn" onclick="askQuestion('What challenges do participants face?')">Challenges</button>
                <button class="suggestion-btn" onclick="askQuestion('Compare organizations')">Compare Organizations</button>
            </div>
        </div>
        
        <div class="chat-input">
            <div class="input-group">
                <input type="text" id="messageInput" placeholder="Ask a question about youth program impacts..." onkeypress="handleKeyPress(event)">
                <button onclick="sendMessage()" id="sendButton">Send</button>
            </div>
        </div>
    </div>
    
    <script>
        async function sendMessage() {
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            
            if (!message) return;
            
            // Add user message to chat
            addMessage(message, 'user');
            input.value = '';
            
            // Show loading
            showLoading(true);
            
            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        message: message,
                        session_id: 'web_session'
                    })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    // Add assistant response
                    addMessage(data.message, 'assistant', {
                        evidence_count: data.evidence_count,
                        organizations: data.organizations,
                        age_groups: data.age_groups,
                        genders: data.genders
                    });
                } else {
                    addMessage('Sorry, I encountered an error processing your question. Please try again.', 'assistant');
                }
            } catch (error) {
                addMessage('Sorry, I\\'m having trouble connecting. Please check your connection and try again.', 'assistant');
            }
            
            showLoading(false);
        }
        
        function addMessage(content, sender, meta = null) {
            const messagesContainer = document.getElementById('chatMessages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${sender}`;
            
            let metaHtml = '';
            if (meta) {
                metaHtml = `
                    <div class="message-meta">
                        <span class="evidence-badge">${meta.evidence_count} evidence</span>
                        Organizations: ${meta.organizations.join(', ')}<br>
                        Age Groups: ${meta.age_groups.join(', ')} | Genders: ${meta.genders.join(', ')}
                    </div>
                `;
            }
            
            messageDiv.innerHTML = `
                <div class="message-content">${content}</div>
                ${metaHtml}
            `;
            
            messagesContainer.appendChild(messageDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
        
        function showLoading(show) {
            const loading = document.getElementById('loading');
            const sendButton = document.getElementById('sendButton');
            
            if (show) {
                loading.classList.add('show');
                sendButton.disabled = true;
            } else {
                loading.classList.remove('show');
                sendButton.disabled = false;
            }
        }
        
        function askQuestion(question) {
            document.getElementById('messageInput').value = question;
            sendMessage();
        }
        
        function handleKeyPress(event) {
            if (event.key === 'Enter') {
                sendMessage();
            }
        }
        
        // Focus input on load
        document.getElementById('messageInput').focus();
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Process chat message and return response"""
    if rag_system is None:
        raise HTTPException(status_code=503, detail="RAG system not initialized")
    
    try:
        # Process the message
        result = rag_system.chat(request.message)
        
        # Extract organizations, age groups, and genders
        organizations = list(set(doc['organization'] for doc in result['source_documents']))
        age_groups = list(set(doc['age_group'] for doc in result['source_documents']))
        genders = list(set(doc['gender'] for doc in result['source_documents']))
        
        # Store in chat history
        chat_entry = {
            'timestamp': datetime.now().isoformat(),
            'session_id': request.session_id,
            'question': request.message,
            'answer': result['answer'],
            'evidence_count': result['evidence_count'],
            'organizations': organizations,
            'age_groups': age_groups,
            'genders': genders
        }
        chat_history.append(chat_entry)
        
        return ChatResponse(
            message=result['answer'],
            evidence_count=result['evidence_count'],
            organizations=organizations,
            age_groups=age_groups,
            genders=genders,
            timestamp=datetime.now().isoformat(),
            session_id=request.session_id
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    if rag_system is None:
        raise HTTPException(status_code=503, detail="RAG system not initialized")
    
    return {
        "status": "healthy",
        "system": "advanced_rag",
        "chat_history_count": len(chat_history)
    }

@app.get("/history")
async def get_chat_history():
    """Get chat history"""
    return {
        "history": chat_history[-10:],  # Return last 10 conversations
        "total_conversations": len(chat_history)
    }

if __name__ == "__main__":
    print("🌐 Starting Advanced RAG Web Interface")
    print("=" * 60)
    print("Features:")
    print("• Interactive chat interface with semantic search")
    print("• Real-time evidence-based responses")
    print("• Source attribution and metadata")
    print("• Suggested questions for exploration")
    print("=" * 60)
    print("\\n🚀 Server will be available at: http://localhost:8002")
    print("💡 Try asking: 'How do programs build confidence in young people?'")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8002,
        reload=False
    )