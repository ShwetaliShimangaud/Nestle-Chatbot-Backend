import json
import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer
import spacy
from starlette.middleware.base   import BaseHTTPMiddleware
from app.api import router as chat_router
from starlette.requests import Request
from google.cloud import storage
from contextlib import asynccontextmanager
from google.cloud import aiplatform


load_dotenv()

# Load config
with open("config.json", "r") as f:
    config = json.load(f)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # This runs once at startup
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = config["GOOGLE_APPLICATION_CREDENTIALS"]

    app.state.model = SentenceTransformer("all-MiniLM-L6-v2")
    app.state.nlp = spacy.load("en_core_web_trf")
    app.state.driver = GraphDatabase.driver(os.getenv('neo4j_uri'), auth=(os.getenv('neo4j_username'), os.getenv('neo4j_password')))

    aiplatform.init(project=config["PROJECT_ID"], location=config["LOCATION"])
    app.state.bucket_data = load_bucket_data()

    yield

    # Optional: cleanup logic here if needed during shutdown
    # e.g., app.state.bucket_data.close() if it's a resource


app = FastAPI(redirect_slashes=False, lifespan=lifespan)  

class HTTPSRedirectSchemeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # If X-Forwarded-Proto header is present and 'https', override scheme
        if request.headers.get("x-forwarded-proto", "") == "https":
            request.scope["scheme"] = "https"
        response = await call_next(request)
        return response

app.add_middleware(HTTPSRedirectSchemeMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    # allow_origins=["https://react-frontend-821842650532.northamerica-northeast1.run.app","http://localhost:5173", "http://localhost:8080"],  # Restrict to your frontend domain in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router, prefix="/api/chat", tags=["chat"])

def load_bucket_data():
    storage_client = storage.Client(project=config["PROJECT_ID"])
    bucket = storage_client.bucket(config["BUCKET_NAME"])
    blob = bucket.blob(config["BLOB_NAME"])
    jsonl_content = blob.download_as_text().splitlines()
    id_to_text = {json.loads(line)["id"]: json.loads(line)["text"] + " " + json.loads(line)['metadata']['source_url'] for line in jsonl_content}
    # print(id_to_text)
    return id_to_text
