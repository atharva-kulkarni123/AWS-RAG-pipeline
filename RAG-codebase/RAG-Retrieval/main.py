from rag_service import RAGService


def main():
    try:
        rag = RAGService()
    except Exception as error:
        print(f"\nUnable to start RAG service: {error}")
        return

    print("\nRAG Question Answering")
    print("======================")

    while True:
        print("\nQuestion: ", end="", flush=True)
        question = input().strip()
        if not question:
            print("Please enter a question.")
            continue

        if question.lower() in {
            "exit",
            "quit"
        }:
            break
        try:
            result = rag.answer(question)
            print("\nAnswer:")
            print(result["answer"])
            print("\nSources:")
            for source in result["sources"]:
                print(
                    f"- {source['document']} | "
                    f"{source['chunk']} | "
                    f"Page: {source['page']} | "
                    f"Similarity: "
                    f"{source['similarity']:.4f}"
                )
        except Exception as error:
            print(f"\nError: {error}")


if __name__ == "__main__":
    main()