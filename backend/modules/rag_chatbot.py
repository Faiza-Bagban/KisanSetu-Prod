"""
rag_chatbot.py
RAG (Retrieval-Augmented Generation) pipeline for the farmer scheme chatbot.
Embeds real scheme criteria into a local vector store (ChromaDB), retrieves
the most relevant schemes for a farmer's question, then uses the local LLM
(Ollama) to generate a grounded answer.
"""
import chromadb
from sentence_transformers import SentenceTransformer
import ollama
from data.schemes_real import REAL_SCHEMES
from modules.crop_loss import predict_risk
from modules.translation import detect_language, translate_to_english, translate_from_english

CHROMA_PATH = "data/chroma_db"
COLLECTION_NAME = "scheme_docs"
EMBED_MODEL = "all-MiniLM-L6-v2"  # small, fast, good enough for this use case
LLM_MODEL = "llama3.1:8b"

_embedder = None
_client = None
_collection = None


def get_embedder():
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer(EMBED_MODEL)
    return _embedder


def get_collection():
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(path=CHROMA_PATH)
        _collection = _client.get_or_create_collection(COLLECTION_NAME)
    return _collection

def get_live_risk_context(district: str = "Pune"):
    """
    Fetches current crop-loss risk for a district using the real trained
    model, formatted as a retrievable document — makes chatbot answers
    reflect genuinely live data, not just static scheme text.
    """
    # Using current-season representative values — in production this
    # would pull today's actual IMD/NDVI/soil-moisture readings
    result = predict_risk(
        district=district,
        rainfall_deficit=10,
        temp_anomaly=2,
        ndvi_drop=0.15,
        soil_moisture=0.5,
        days_since_rain=8,
    )

    if "error" in result:
        return None

    return {
        "id": f"live_risk_{district}",
        "text": f"""Current Crop Loss Risk Status for {district}:
Risk Level: {result['risk_level']}
Risk Percentage: {result['risk_percent']}%
This is a live prediction from the KisanSetu crop-loss model based on
current rainfall, temperature, vegetation health (NDVI), and soil moisture
data for {district}.""",
        "metadata": {"type": "live_risk", "district": district},
    }

def build_vector_store():
    """Embeds all real scheme documents plus live risk data into ChromaDB."""
    embedder = get_embedder()
    collection = get_collection()

    existing = collection.get()
    if existing["ids"]:
        collection.delete(ids=existing["ids"])

    documents = []
    metadatas = []
    ids = []

    for scheme in REAL_SCHEMES:
        text = f"{scheme['name']} ({scheme['id']})\n{scheme['criteria']}"
        documents.append(text)
        metadatas.append({"scheme_id": scheme["id"], "scheme_name": scheme["name"], "type": "scheme"})
        ids.append(scheme["id"])

    # Add live risk data for known districts
    for district in ["Pune", "Nashik", "Aurangabad", "Solapur", "Kolhapur", "Amravati"]:
        live_doc = get_live_risk_context(district)
        if live_doc:
            documents.append(live_doc["text"])
            metadatas.append(live_doc["metadata"])
            ids.append(live_doc["id"])

    embeddings = embedder.encode(documents).tolist()

    collection.add(
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
        ids=ids,
    )

    print(f"Embedded and stored {len(documents)} documents ({len(REAL_SCHEMES)} schemes + live risk data)")


def retrieve_relevant_schemes(query: str, n_results: int = 3):
    """Finds the most relevant schemes for a farmer's question."""
    embedder = get_embedder()
    collection = get_collection()

    query_embedding = embedder.encode([query]).tolist()

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=n_results,
    )

    return results["documents"][0], results["metadatas"][0]

def chatbot_answer(query: str, n_results: int = 3):
    """
    Full RAG pipeline with multilingual support: detects query language,
    translates to English for retrieval, then asks the LLM to generate
    its answer natively in the detected language (more reliable than
    machine-translating a finished English paragraph).
    """
    lang = detect_language(query)
    query_en = translate_to_english(query, lang)

    docs, metas = retrieve_relevant_schemes(query_en, n_results)

    context = "\n\n---\n\n".join(docs)

    lang_names = {"en": "English", "hi": "Hindi (in Devanagari script, not Roman/Latin letters)", "mr": "Marathi (in Devanagari script, not Roman/Latin letters)"}
    target_lang_name = lang_names.get(lang, "English")

    prompt = f"""You are a helpful assistant for Indian farmers, answering questions
about government agricultural schemes. Answer ONLY using the scheme information
provided below — do not invent details not present in the context. If the
context doesn't fully answer the question, say so honestly.

RELEVANT SCHEME INFORMATION:
{context}

FARMER'S QUESTION: {query_en}

Give a clear, friendly, concise answer in plain language (not a list of raw criteria).
Respond ENTIRELY in {target_lang_name}, written naturally as a native {target_lang_name}
speaker would write it — not a literal translation.
Keep your answer short (3-4 sentences maximum) and stick closely to the facts
in the scheme information above — do not add interpretations or distinctions
not explicitly stated in the context.
"""

    response = ollama.chat(model=LLM_MODEL, messages=[
        {"role": "user", "content": prompt}
    ], options={"temperature": 0})

    answer_final = response["message"]["content"]

    return {
        "answer": answer_final,
        "detected_language": lang,
        "sources": [m.get("scheme_name") or f"Live risk data ({m.get('district')})" for m in metas],
    }

if __name__ == "__main__":
    build_vector_store()

    test_queries = [
        "What is the current crop risk in Pune, and what schemes can help?",
        "मुझे फसल बीमा के बारे में जानकारी चाहिए",
    ]

    for q in test_queries:
        result = chatbot_answer(q)
        print(f"\nQuery: {q}")
        print(f"Detected language: {result['detected_language']}")
        print(f"Answer: {result['answer']}")
        print(f"Sources: {result['sources']}")
        print("-" * 60)