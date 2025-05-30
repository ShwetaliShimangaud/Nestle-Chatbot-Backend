import json
import os
from dotenv import load_dotenv
import spacy
from neo4j import GraphDatabase, exceptions
from tqdm import tqdm

nlp = spacy.load("en_core_web_trf")

load_dotenv()
driver = GraphDatabase.driver(os.getenv('neo4j_uri'), auth=(os.getenv('neo4j_username'), os.getenv('neo4j_password')))

# Test connection
with driver.session() as session:
    result = session.run("RETURN 'Connected to Neo4j Aura!' AS message")
    print(result.single()["message"])



def load_all_scraped_data(folder):
    all_data = []
    for filename in os.listdir(folder):
        if filename.endswith(".json"):
            with open(os.path.join(folder, filename), 'r', encoding='utf-8') as f:
                data = json.load(f)
                all_data.extend(data)
    return all_data

def already_uploaded(source_id):
    with driver.session() as session:
        result = session.run(
            "MATCH (e:Entity) WHERE $source_id IN e.sources RETURN COUNT(e) > 0 AS exists",
            source_id=source_id
        )
        return result.single()["exists"]


def extract_and_store(text, source_id=None):
    doc = nlp(text)
    entities = [(ent.text.strip(), ent.label_) for ent in doc.ents]
    relations = []
    try:
        for sent in doc.sents:
            subj, verb, obj = None, None, None
            for tok in sent:
                if "subj" in tok.dep_:
                    subj = tok
                if "obj" in tok.dep_:
                    obj = tok
                if tok.pos_ == "VERB":
                    verb = tok
            if subj and verb and obj:
                relations.append((subj.text.strip(), verb.lemma_, obj.text.strip()))

        with driver.session() as session:
            for name, typ in entities:
                session.run(
                    "MERGE (n:Entity {name: $name}) "
                    "ON CREATE SET n.type = $type "
                    "SET n.sources = coalesce(n.sources, []) + $source_id",
                    name=name, type=typ, source_id=source_id,
                )

            for s, r, o in relations:
                session.run(
                    "MERGE (a:Entity {name: $s}) "
                    "MERGE (b:Entity {name: $o}) "
                    "MERGE (a)-[rel:RELATION {type: $r}]->(b) "
                    "SET rel.sources = coalesce(rel.sources, []) + $source_id",
                    s=s, o=o, r=r, source_id=source_id,
                )

    except exceptions.ClientError as e:
        if "WriteOnReadOnlyAccessDatabase" in str(e):
            print(f"Skipped write for {source_id}: database is read-only.")
        else:
            raise

data = load_all_scraped_data("scraped_data")
print(len(data))

for i, doc in tqdm(enumerate(data)):
    source_id = doc.get("url", f"doc_{i}")
    if already_uploaded(source_id):
        print("already uploaded", source_id)
        continue
    extract_and_store(doc.get("text", ""), source_id=source_id)
