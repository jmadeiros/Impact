# 🚀 Vercel Deployment Steps

## Prerequisites
- GitHub account connected to Vercel
- API keys for Google AI and Pinecone
- Survey data populated in Pinecone (we'll handle this)

## Step 1: Create GitHub Repository

1. Go to GitHub and create a new repository (e.g., `rag-survey-system`)
2. Make it public or private (your choice)
3. Don't initialize with README (we have our own)

## Step 2: Push Code to GitHub

From your `vercel-deployment` directory:

```bash
# Initialize git repository
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit: Vercel-optimized RAG system"

# Add your GitHub repository as origin
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git

# Push to GitHub
git push -u origin main
```

## Step 3: Connect to Vercel

1. Go to [vercel.com](https://vercel.com)
2. Click "New Project"
3. Import your GitHub repository
4. Vercel will automatically detect it's a Python project

## Step 4: Configure Environment Variables

In Vercel dashboard, add these environment variables:

### Required Variables:
```
GOOGLE_API_KEY = AIzaSyDEhe7LmWNe_ua2z0YqlOuMjpTbjpve1lU
PINECONE_API_KEY = pcsk_6BVaTz_K9J4jJeEF52GsBBGPNRGQ1uz6vuZ52ZHCfcKUASJ2KLr7Yt5mch3qo7QfHjH6Ls
PINECONE_ENVIRONMENT = gcp-starter
PINECONE_INDEX_NAME = rag-survey-responses
PINECONE_NAMESPACE = production
```

### Optional Variables:
```
VECTOR_STORE_TYPE = pinecone
EMBEDDING_MODEL = sentence-transformers/all-MiniLM-L6-v2
LLM_MODEL = gemini-1.5-flash
TEMPERATURE = 0.1
MAX_TOKENS = 1000
MAX_RESULTS = 5
TIMEOUT_SECONDS = 25
ENVIRONMENT = production
DEBUG = false
```

## Step 5: Deploy

1. Click "Deploy" in Vercel
2. Wait for build to complete
3. Test the deployment

## Step 6: Populate Vector Database

Before the system works, you need survey data in Pinecone:

```bash
# Run the data population script (we'll create this)
python3 scripts/populate_pinecone.py
```

## Step 7: Test Deployment

Test your endpoints:

```bash
# Replace YOUR_DEPLOYMENT_URL with your actual Vercel URL
curl https://YOUR_DEPLOYMENT_URL.vercel.app/api/health

curl -X POST https://YOUR_DEPLOYMENT_URL.vercel.app/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "How do programs build confidence?"}'
```

## Troubleshooting

### Build Fails
- Check that all dependencies are in `requirements.txt`
- Verify Python version compatibility
- Check Vercel build logs

### Runtime Errors
- Verify all environment variables are set
- Check that Pinecone index exists and has data
- Review function logs in Vercel dashboard

### API Errors
- Confirm API keys are valid
- Check Pinecone index name matches environment variable
- Verify vector database has survey data

---

**Ready to deploy!** Let me know when you've created the GitHub repository and I'll help with the next steps.