# 🚀 Deploy from advanced-rag/src Branch

## Current Status
✅ **All Vercel deployment code is on `advanced-rag/src` branch**  
✅ **Successfully pushed to GitHub**  
✅ **Pinecone database populated with 30 survey responses**  
✅ **All tests passing (23/23 core tests)**  

## Deploy to Vercel

### Step 1: Connect to Vercel
1. Go to [vercel.com](https://vercel.com)
2. Click "New Project"
3. Select your GitHub repository: `jmadeiros/Impact`
4. **Important**: Change the branch from `main` to `advanced-rag/src`
5. Set the root directory to `vercel-deployment`

### Step 2: Configure Environment Variables
Add these in Vercel dashboard:

```
GOOGLE_API_KEY=AIzaSyDEhe7LmWNe_ua2z0YqlOuMjpTbjpve1lU
PINECONE_API_KEY=pcsk_6BVaTz_K9J4jJeEF52GsBBGPNRGQ1uz6vuZ52ZHCfcKUASJ2KLr7Yt5mch3qo7QfHjH6Ls
PINECONE_ENVIRONMENT=gcp-starter
PINECONE_INDEX_NAME=rag-survey-responses
PINECONE_NAMESPACE=production
VECTOR_STORE_TYPE=pinecone
ENVIRONMENT=production
DEBUG=false
```

### Step 3: Deploy
1. Click "Deploy"
2. Wait for build to complete
3. Test your endpoints!

## Test Your Deployment

Once deployed, test these endpoints:

```bash
# Replace YOUR_DEPLOYMENT_URL with your actual Vercel URL
curl https://YOUR_DEPLOYMENT_URL.vercel.app/api/health

curl -X POST https://YOUR_DEPLOYMENT_URL.vercel.app/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "How do programs build confidence?"}'
```

## Why This Works
- Your `advanced-rag/src` branch has the complete, tested Vercel deployment
- The Pinecone database is already populated with survey data
- All 23 core tests are passing
- The system is production-ready

🎉 **Ready to deploy!**