import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
import os

class ChromaService:
    def __init__(self):
        self.client = chromadb.Client(
             chromadb.config.Settings(
                persist_directory="./chroma_db",
                is_persistent=True
            )
        )
        self.embedding_function = OpenAIEmbeddingFunction(
            model_name="text-embedding-3-small",
            api_base=os.getenv("OPENROUTER_BASE_URL"),
            api_key=os.getenv("OPENROUTER_API_KEY")
        )
        self.collection = self.client.get_or_create_collection(
            name="code_intel_memory",
            embedding_function=self.embedding_function
        )

    def store_function_summary(self, function_name: str, summary: str):
        print(f"Storing summary for: {function_name}")
        self.collection.add(
            documents=[summary],
            ids=[function_name],
            metadatas=[{"function": function_name}]
        )

    def query(self, question: str, top_k: int = 3):
        results = self.collection.query(
            query_texts=[question],
            n_results=top_k
        )
        print(f"Chroma query results for '{question}': {results}")
        return results["documents"][0]