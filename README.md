To set account : gcloud config set core/account shwetali.shimangaud.work@gmail.com

set credentials : gcloud auth login
gcloud config set project PROJECT_ID
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
enable vertex ai api

to run frontend : npm run dev
to run backend : uvicorn app.main:app --reload

Build the container image of backend : gcloud builds submit --tag gcr.io/nestle-chatbot-461219/fastapi-backend --verbosity=debug

deploy to cloud run : gcloud run deploy fastapi-backend --image gcr.io/nestle-chatbot-461219/fastapi-backend --platform managed --allow-unauthenticated --region northamerica-northeast1 --memory 2Gi

use port 8080 for cloud run in dockerfile because that's default. when running on local u can use any port


frontend:
npm run build
gcloud builds submit --tag gcr.io/nestle-chatbot-461219/react-frontend
gcloud run deploy react-frontend --image gcr.io/nestle-chatbot-461219/react-frontend --platform managed --allow-unauthenticated --region northamerica-northeast1


setup neo4j
download en_core_web_trf