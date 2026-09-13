from config import Config
from embeddings import EmbeddingService
from vector_store import VectorStore
from retriever import Retriever
from reranker import Reranker
from prompt import PromptBuilder
from llm import LLMService


class RAGService:

    def __init__(self):
        Config.validate()
        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStore()
        self.retriever = Retriever(
            embedding_service=self.embedding_service,
            vector_store=self.vector_store
        )
        self.reranker = Reranker()
        self.llm = LLMService()

    def answer(self, question: str) -> dict:
        retrieved_documents = self.retriever.retrieve(
            question
        )
        if not retrieved_documents:
            return {
                "question": question,
                "answer": (
                    "I don't have enough information "
                    "in the provided documents."
                ),
                "sources": []
            }

        reranked_documents = self.reranker.rerank(
            question=question,
            documents=retrieved_documents,
            top_k=Config.RERANK_TOP_K
        )

        prompt = PromptBuilder.build(
            question=question,
            documents=reranked_documents
        )

        answer = self.llm.generate(prompt)
        sources = [
            {
                "document": document["document_id"],
                "chunk": document["chunk_id"],
                "page": document["page_number"],
                "similarity": document["similarity"]
            }
            for document in reranked_documents
        ]

        return {
            "question": question,
            "answer": answer,
            "sources": sources
        }