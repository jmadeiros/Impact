# 🎯 Impact Intelligence Platform

An AI-powered platform that transforms youth program survey data into actionable insights through advanced conversational AI and semantic search.

## 🚀 Quick Start

### **Advanced RAG System (Recommended)**
```bash
cd advanced_rag
python3 start_web_interface.py
# Open http://localhost:8002
```

### **Simple RAG System**
```bash
python3 working_server.py
# API available at http://localhost:8000
```

## 📊 What This Does

- **Semantic Search**: Finds relevant survey responses by meaning, not keywords
- **Conversational AI**: Natural language chat about program effectiveness
- **Evidence-Based Insights**: Every answer backed by specific survey responses
- **Mixed Data Analysis**: Combines MCQ responses with story narratives
- **Professional Reporting**: Structured analysis for stakeholders

## 🏗️ System Architecture

### **Two Complete Systems:**

1. **Simple RAG** (`simple_rag_system.py`, `working_server.py`)
   - Fast, reliable keyword-based search
   - Direct database queries + Google AI
   - API endpoints for integration

2. **Advanced RAG** (`advanced_rag/` folder)
   - Semantic search with vector embeddings
   - Conversational web interface
   - ChromaDB + Langchain + Google Gemini

## 📈 Current Data

- **30 Survey Responses** from youth program participants
- **4 Organizations**: YCUK, I AM IN ME, Palace for Life, Symphony Studios
- **2 Age Groups**: 12-14 and 15-17 year olds
- **22 Searchable Documents** (after intelligent filtering)

## 🔧 Setup

### **Prerequisites**
- Python 3.12+
- Google AI API key
- Supabase account

### **Installation**
```bash
# Install dependencies
pip3 install -r requirements.txt
pip3 install -r advanced_rag/requirements_advanced.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# Set up advanced system
cd advanced_rag
python3 setup_advanced.py
```

## 📚 Documentation

- **[Quick Start Guide](advanced_rag/QUICK_START_GUIDE.md)** - Daily usage
- **[System Summary](advanced_rag/SYSTEM_SUMMARY.md)** - Technical details
- **[Project Overview](advanced_rag/PROJECT_OVERVIEW.md)** - Business value
- **[Scalability Analysis](advanced_rag/SCALABILITY_ANALYSIS.md)** - Scaling to 1000s

## 🎯 Key Features

### **Semantic Understanding**
Finds "mock exam failure" when asked about "confidence" - understands meaning, not just keywords.

### **Evidence Attribution**
Every insight backed by specific survey responses with full source attribution.

### **Conversational Interface**
Natural language chat: "How do programs build confidence in young people?"

### **Scalable Architecture**
Handles 1000s of responses with constant token usage and predictable costs.

## 💰 Costs

- **Current**: ~$0.00027 per query (extremely low)
- **At Scale**: ~$8/month for 1,000 queries/day
- **Scales with usage**, not data size

## 🚀 Example Queries

- "How do programs build confidence in young people?"
- "What helps teenagers make friends?"
- "Which creative activities work best?"
- "Compare impact across organizations"
- "Show me stories about overcoming challenges"

## 🔬 Technical Stack

- **AI**: Google Gemini 1.5 Flash
- **Embeddings**: Sentence Transformers (384D vectors)
- **Vector DB**: ChromaDB
- **Framework**: FastAPI + Langchain
- **Database**: Supabase PostgreSQL
- **Frontend**: Modern HTML/CSS/JS

## 📊 Performance

- **Response Time**: 2-5 seconds
- **Token Usage**: ~700 tokens per query
- **Accuracy**: Semantic search finds relevant content by meaning
- **Scalability**: Logarithmic scaling with database size

## 🎉 What Makes This Special

1. **True Semantic Search** - Beyond keyword matching
2. **Mixed Methods Integration** - Combines MCQ + story data
3. **Evidence-Based AI** - Transparent, trustworthy responses
4. **Production Ready** - Comprehensive testing and error handling
5. **Scalable Design** - Ready for 1000s of responses

---

**Built for impact measurement professionals who need both narrative insights and evidence-based analysis.** 🎯