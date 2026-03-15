# Production Deployment Guide (Option 1)

This guide provides the manual steps needed to complete the deployment of WellnessWay to Google Cloud Run and Cloudflare Pages.

## STEP 1: Google Cloud Platform (Backend)

1.  **Create a GCP Project**: Go to [GCP Console](https://console.cloud.google.com/) and create a new project.
2.  **Enable APIs**: Enable the following:
    - Cloud Run API
    - Artifact Registry API
    - Cloud Build API
3.  **Create Artifact Registry**:
    - Repository name: `wellness-way-repo`
    - Format: Docker
    - Region: `us-central1`
4.  **Service Account**:
    - Create a Service Account (e.g., `github-deployer`).
    - Grant Roles: `Cloud Run Admin`, `Storage Admin`, `Artifact Registry Writer`, `Service Account User`.
    - Create and download a **JSON Key**.

## STEP 2: Cloudflare (Frontend)

1.  **Create Pages Project**: 
    - Log in to your [Cloudflare Dashboard](https://dash.cloudflare.com/).
    - Go to **Workers & Pages** -> **Create application** -> **Pages** -> **Connect to Git**.
    - Select your GitHub repo.
2.  **Build Settings**:
    - Framework preset: `Vite` (or `None` if Vite is not detected).
    - Build command: `npm run build`
    - Build output directory: `dist`
    - Root directory: `/frontend`
3.  **Environment Variables**:
    - Add `VITE_API_URL`: Use your Cloud Run service URL once it's deployed.

## STEP 3: GitHub Secrets

Add these secrets to your GitHub repository (**Settings** -> **Secrets and variables** -> **Actions**):

| Secret Name | Description |
| :--- | :--- |
| `GCP_PROJECT_ID` | Your GCP Project ID |
| `GCP_SA_KEY` | The contents of your Service Account JSON Key |
| `DATABASE_URL` | Your Supabase connection string |
| `SUPABASE_URL` | Supabase URL |
| `SUPABASE_ANON_KEY` | Supabase Anonymous Key |
| `GROQ_API_KEY` | Groq AI API Key |
| `OPENAI_API_KEY` | OpenAI API Key |

## STEP 4: Trigger Deployment

1.  Go to the **Actions** tab in your GitHub repository.
2.  Select **Build and Deploy to Cloud Run**.
3.  Click **Run workflow**.

---

## Post-Deployment
- Once the backend is live, update the `VITE_API_URL` in Cloudflare Pages and redeploy the frontend.
