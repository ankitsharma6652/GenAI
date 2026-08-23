import os
import json
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import CharacterTextSplitter


load_dotenv()

PROJECT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
DOCS_DIRECTORY = os.path.join(PROJECT_DIRECTORY, "docs")
PERSIST_DIRECTORY = os.path.join(
    PROJECT_DIRECTORY, "db", "chroma_groq_local_embeddings"
)
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
GROQ_MODEL = "openai/gpt-oss-120b"


def load_and_split_documents():
    if not os.path.isdir(DOCS_DIRECTORY):
        raise FileNotFoundError(f"Documents directory not found: {DOCS_DIRECTORY}")

    loader = DirectoryLoader(
        DOCS_DIRECTORY,
        glob="*.txt",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
    )
    documents = loader.load()
    if not documents:
        raise FileNotFoundError(f"No .txt files found in {DOCS_DIRECTORY}")

    splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    return splitter.split_documents(documents)


def get_vector_store():
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

    if os.path.isdir(PERSIST_DIRECTORY):
        return Chroma(
            persist_directory=PERSIST_DIRECTORY,
            embedding_function=embeddings,
            collection_metadata={"hnsw:space": "cosine"},
        )

    chunks = load_and_split_documents()
    return Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=PERSIST_DIRECTORY,
        collection_metadata={"hnsw:space": "cosine"},
    )


def ask_groq(question, context):
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY is not set in the environment or .env file")

    prompt = f"""Answer the question using only the provided context.
If the context does not contain the answer, say you do not know.

Context:
{context}

Question: {question}"""
    request = Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=json.dumps(
            {
                "model": GROQ_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1000,
            }
        ).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {groq_api_key}",
            "Content-Type": "application/json",
            "User-Agent": "genai-rag-example/1.0",
        },
        method="POST",
    )
    try:
        with urlopen(request) as response:
            result = json.load(response)
    except HTTPError as error:
        details = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"Groq request failed with HTTP {error.code}: {details}"
        ) from error
    return result["choices"][0]["message"]["content"]


def answer_question(question):
    vector_store = get_vector_store()
    documents = vector_store.similarity_search(question, k=4)
    context = "\n\n".join(document.page_content for document in documents)

    return ask_groq(question, context)


if __name__ == "__main__":
    question = "How much did Microsoft pay to acquire GitHub?"
    print(f"Question: {question}\n")
    print(f"Answer: {answer_question(question)}")
