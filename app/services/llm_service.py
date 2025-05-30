import json
import os
from dotenv import load_dotenv
from fastapi import Request
from google.cloud import aiplatform_v1
from google import genai
from google import genai

load_dotenv()
# Load config
with open("config.json", "r") as f:
    config = json.load(f)


def build_rag_context(query,model,nlp,driver, id_to_text, k=10):
    # 1. Embed the query
    query_vector = model.encode([query])[0]

    try :

        # Configure Vector Search client
        client_options = {
        "api_endpoint": config["API_ENDPOINT"]
        }
        vector_search_client = aiplatform_v1.MatchServiceClient(
            client_options=client_options,
        )

        # Build FindNeighborsRequest object
        datapoint = aiplatform_v1.IndexDatapoint(
            feature_vector=query_vector.tolist()
        )

        query = aiplatform_v1.FindNeighborsRequest.Query(
            datapoint=datapoint,
            # The number of nearest neighbors to be retrieved
            neighbor_count=k
        )
        request = aiplatform_v1.FindNeighborsRequest(
        index_endpoint=config["INDEX_ENDPOINT"],
        deployed_index_id=config["DEPLOYED_INDEX_ID"],
        # Request can have multiple queries
        queries=[query],
        return_full_datapoint=True,
        )

        # Execute the request
        response = vector_search_client.find_neighbors(request)


    except Exception as e:
        print(f"Error during match: {e}")
        raise

    # 3. Extract texts from vector results
    matches = response.nearest_neighbors[0].neighbors  # Get neighbors for the first query
    context_texts = [id_to_text[neighbor.datapoint.datapoint_id] for neighbor in matches]
    
    # 4. Extract entities from context
    entities = set()
    for text in context_texts:
        doc = nlp(text)
        entities.update(ent.text for ent in doc.ents)
    
    # 5. Fetch related graph info from Neo4j
    related_info = []
    with driver.session() as session:
        for ent in entities:
            query = """
            MATCH (a:Entity {name: $name})-[r]->(b)
            RETURN a.name AS source, type(r) AS relation, b.name AS target
            """
            result = session.run(query, name=ent)
            for record in result:
                related_info.append(f"{record['source']} -[{record['relation']}]-> {record['target']}")
    
    # 6. Combine context text + graph info
    rag_context = "\n".join(related_info)

    return "\n".join(context_texts), rag_context



def generate_answer_with_vertex_ai(query, context_vertex_ai, rag_context):

    system_prompt = (
    "Using the information and entity-relationship details provided below, answer the query in natural language. "
    "If a relevant URL is present in the context, include it in your response."
    )

    prompt = (
    f"{system_prompt}\n\n"
    f"### Information:\n{context_vertex_ai}\n\n"
    f"### Related Entity-Relationships:\n{rag_context}\n\n"
    f"### Query:\n{query}\n"
    )

    client = genai.Client(api_key=os.getenv("GEMINI_KEY"))

    response = client.models.generate_content(
    model=config["LLM"],
    contents=prompt,
    )
    return response.text


async def get_chat_response(message: str, request : Request) -> str:
    context_vertex_ai, rag_context = build_rag_context(message,request.app.state.model,request.app.state.nlp,request.app.state.driver, request.app.state.bucket_data)
    answer = generate_answer_with_vertex_ai(message, context_vertex_ai, rag_context)

    print("Answer:", answer)
    return answer
