import os
import json
import re
from sentence_transformers import SentenceTransformer
import uuid
from google.cloud import storage
from google.cloud import aiplatform
from tqdm import tqdm


model = SentenceTransformer("all-MiniLM-L6-v2")  # You can swap with OpenAI if using their API
PROJECT_ID = "nestle-chatbot-461219"
LOCATION = "northamerica-northeast1"  # Matching Engine is available here
BUCKET_NAME = "nestle-chatbot"
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "nestle-chatbot-461219-7cab46b1a1f7.json"
INDEX_NAME = "nestle-chatbot-index"



def load_all_scraped_data(folder):
    all_data = []
    for filename in os.listdir(folder):
        if filename.endswith(".json"):
            with open(os.path.join(folder, filename), 'r', encoding='utf-8') as f:
                data = json.load(f)
                all_data.extend(data)
    return all_data


def clean_text(text):
    text = re.sub(r'\\[a-zA-Z0-9]+', ' ', text)  # Remove encoded unicode like \u00a0
    text = re.sub(r'\n+', ' ', text)  # Remove newline characters
    text = re.sub(r'\s+', ' ', text)  # Normalize multiple spaces
    text = re.sub(r'[^A-Za-z0-9.,:;!?&%$@\'"()/-]+', ' ', text)  # Remove unwanted symbols
    return text.strip()

def chunk_text(text, max_words=400):
    clean = clean_text(text)
    words = clean.split()
    return [" ".join(words[i:i+max_words]) for i in range(0, len(words), max_words-100)]

def generate_embeddings(data):
    embeddings = []
    for doc in tqdm(data):
        chunks = chunk_text(doc.get("text", ""))
        vectors = model.encode(chunks).tolist()
        for chunk, vector in zip(chunks, vectors):
            embeddings.append({
                "id": str(uuid.uuid4()),
                "text": chunk,
                "vector": vector,
                "metadata": {"source_url": doc["url"]}
            })
    return embeddings

def save_embeddings_to_jsonl(embeddings, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        for item in tqdm(embeddings):
            f.write(json.dumps({
                "id": item["id"],
                "embedding": item["vector"],
                "text" : item['text'],
                "metadata": item["metadata"]
            }) + '\n')



def upload_to_gcs(source_file_name, destination_blob_name):
    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(source_file_name)
    print(f"Uploaded {source_file_name} to gs://{BUCKET_NAME}/{destination_blob_name}")


def create_index():
    aiplatform.init(project=PROJECT_ID, location=LOCATION)
    index = aiplatform.MatchingEngineIndex.create_tree_ah_index(
    display_name=INDEX_NAME,
    dimensions=384,  # For MiniLM
    approximate_neighbors_count=100,
    distance_measure_type="DOT_PRODUCT_DISTANCE",  # or COSINE
    index_update_method="BATCH_UPDATE",
    description="Embeddings for madewithnestle chatbot"
    )

    return index

def create_endpoint_and_deploy_index():
    aiplatform.init(project=PROJECT_ID, location=LOCATION)
    indexes = aiplatform.MatchingEngineIndex.list()
    index = next(i for i in indexes if i.display_name == INDEX_NAME)

    endpoint = aiplatform.MatchingEngineIndexEndpoint.create(
        display_name="nestle-chatbot-endpoint",
        public_endpoint_enabled=True  # or False if VPC only
    )

    # Deploy the index
    endpoint.deploy_index(index=index,display_name="Nestle Chatbot Deployment", deployed_index_id="nestle_chatbot_deployment")


data = load_all_scraped_data("scraped_data")
print(len(data))
embeddings = generate_embeddings(data)
print(len(embeddings))
save_embeddings_to_jsonl(embeddings, "embeddings.jsonl")
upload_to_gcs("embeddings.jsonl", "embeddings/embeddings.json")
create_index()
create_endpoint_and_deploy_index()





