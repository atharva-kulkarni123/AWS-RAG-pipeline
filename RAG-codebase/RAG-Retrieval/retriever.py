from config import Config


class Retriever:

    def __init__(self, embedding_service, vector_store):
        self.embedding_service = embedding_service
        self.vector_store = vector_store

    def retrieve(self, question: str) -> list[dict]:

        if not question or not question.strip():
            raise ValueError("Question cannot be empty")

        query_embedding = (
            self.embedding_service
            .generate_embedding(question)
        )

        results = self.vector_store.similarity_search(
            query_embedding=query_embedding,
            top_k=Config.TOP_K
        )

        filtered_results = [
            result
            for result in results
            if result["similarity"] >= Config.SIMILARITY_THRESHOLD
        ]

        if filtered_results:
            return filtered_results

        # Keep the nearest matches when the threshold is too strict for a
        # valid question, so the LLM can judge whether the context is useful.
        return results