class Reranker:

    def rerank(
        self,
        question: str,
        documents: list[dict],
        top_k: int
    ) -> list[dict]:

        ranked_documents = sorted(
            documents,
            key=lambda document: document["similarity"],
            reverse=True
        )

        return ranked_documents[:top_k]