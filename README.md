# 🧠 MadeWithNestle Chatbot – Backend

This is the FastAPI backend for the MadeWithNestle chatbot. It connects to an LLM API, a vector database, and a Neo4j graph database to provide intelligent responses.

---

## 🚀 Technologies Used

- Python 3.9+
- FastAPI
- spaCy (en_core_web_trf)
- Neo4j (Aura)
- Google Vertex AI Matching Engine
- Google Cloud Run
- Docker

---

## 🚀 Models Used

- **Embedding Model**: `Sentence Transformer all-MiniLM-L6-v2`
- **LLM**: `gemini-2.0-flash` (configurable via `config.json`)

---

## ⚙️ Setup and Running Locally

### Prerequisites
- Python 3.9+
- Docker (optional)
- Google Cloud SDK
- Neo4j Aura credentials

### Install Dependencies
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_trf
```

### Run Locally
```bash
uvicorn app.main:app --reload
```

### Run Using Docker
```bash
docker build -t fastapi-backend .
docker run -p 8000:8080 fastapi-backend
```

---

## ☁️ Deployment

### Authenticate and Configure
```bash
gcloud auth login
gcloud config set core/account ACCOUNT
gcloud config set project PROJECT
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable aiplatform.googleapis.com
```

### Build and Deploy
```bash
gcloud builds submit --tag gcr.io/PROJECT/fastapi-backend --verbosity=debug
gcloud run deploy fastapi-backend   --image gcr.io/PROJECT/fastapi-backend   --platform managed   --allow-unauthenticated   --region LOCATION   --memory 4Gi
```

---

## 🔐 Configuration Files

### `.env`
Used to store API keys and sensitive credentials:
```env
LLM_API_KEY=your_llm_key
NEO4J_URI=neo4j+s://your-uri.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
```

### `config.json`
Used for setting up GCP and vector DB configuration:
```json
{
  "project": "your-project",
  "location": "your-location",
  "bucket": "your-gcs-bucket",
  "index": "your-index-name",
  "deployed_index_id" : "your_index_id",
  "endpoint": "your-vector-search-endpoint",
  "blob" : "your_blob_name_where_raw_data_is_stored",
  "api_endpoint" : "your_vertex_ai_endpoint",
  "index_endpoint" : "your_index_endpoint",
  "llm": "your-llm",
  "credentials_path": "/path/to/gcp-service-account.json"
}
```

---

## 🚧 Known Limitations

- Available only in one region → may have slower response times
- Partial content scraping → not all information is available

---

## 📁 Project Structure

```
/backend
  ├── app/
  ├── .env
  ├── config.json
  ├── Dockerfile
  └── main.py
```

---
