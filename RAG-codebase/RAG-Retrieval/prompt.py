class PromptBuilder:

    SYSTEM_INSTRUCTION = """
You are a helpful question-answering assistant.

Answer the user's question using ONLY the provided context.

Rules:
1. Do not use information outside the provided context.
2. If the context does not contain enough information, say:
   "I don't have enough information in the provided documents."
3. Do not invent facts.
4. Give a concise and accurate answer.
5. When possible, mention the source document and page number.
"""

    @classmethod
    def build(
        cls,
        question: str,
        documents: list[dict]
    ) -> str:
        context_parts = []
        for document in documents:
            source = document.get("source") or document.get(
                "document_id",
                "unknown"
            )
            page = document.get("page_number")
            metadata = f"Source: {source}"
            if page:
                metadata += f", Page: {page}"
            context_parts.append(
                f"""
{metadata}
{document["content"]}
"""
            )

        context = "\n\n---\n\n".join(context_parts)
        return f"""
{cls.SYSTEM_INSTRUCTION}

CONTEXT:
{context}
QUESTION:
{question}
ANSWER:
"""