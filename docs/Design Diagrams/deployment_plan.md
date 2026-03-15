# Deployment Plan: Stack Option 1 (Pro Stack)

This plan outlines the steps to deploy the WellnessWay application using a robust, zero-cost production stack.

## Proposed Changes

### 1. Backend Containerization
We will create a `Dockerfile` for the FastAPI backend. This is crucial for handling the ML dependencies (FAISS, NumPy) consistently in the cloud.

#### [NEW] [Dockerfile](file:///c:/Users/Charmi/OneDrive/Desktop/Meet%27s%20Projects/wellness_way/backend/Dockerfile)
- Use a slim Python 3.10 image.
- Install system dependencies for FAISS and NumPy.
- Expose port 8080 (standard for Cloud Run).

### 2. CI/CD Pipeline (GitHub Actions)
We will create a workflow to automate the build and deployment process.

#### [NEW] [google-cloud-run.yml](file:///c:/Users/Charmi/OneDrive/Desktop/Meet%27s%20Projects/wellness_way/.github/workflows/google-cloud-run.yml)
- **Trigger**: Manual trigger (`workflow_dispatch`) as per user request.
- **Jobs**:
    - **Build & Push**: Build the Docker image and push it to Google Artifact Registry.
    - **Deploy**: Update the Google Cloud Run service with the new image.

### 3. Frontend Deployment (Cloudflare Pages)
The React frontend will be hosted on Cloudflare Pages for its unlimited bandwidth and zero-cost edge delivery.

- **Action**: Setup Cloudflare Pages connected to the GitHub repository.
- **Build Command**: `npm run build`
- **Output Directory**: [dist](file:///c:/Users/Charmi/OneDrive/Desktop/Meet%27s%20Projects/wellness_way/backend/app/services/ml_diet_pipeline/canonicalization/service.py#116-121) (or [build](file:///c:/Users/Charmi/OneDrive/Desktop/Meet%27s%20Projects/wellness_way/backend/app/services/ml_diet_pipeline/canonicalization/service.py#76-115))

### 4. Configuration & Secrets
We will define the required environment variables to be stored in GCP Secrets Manager and GitHub Secrets.

- **Supabase**: `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `DATABASE_URL`
- **AI Engines**: `GROQ_API_KEY`, `OPENAI_API_KEY`
- **GCP**: `GCP_PROJECT_ID`, `GCP_SA_KEY`

---

## Verification Plan

### Automated Verification
- **GHA Log Check**: Verify that the GitHub Action completes without errors.
- **Health Check**: Ping the Cloud Run URL to ensure the API is live.

### Manual Verification
- **App Access**: Access the Cloudflare Pages URL and verify that the React app connects to the Cloud Run backend.
- **Diet Generation**: Run a meal generation request in the production environment to verify the ML pipeline.
