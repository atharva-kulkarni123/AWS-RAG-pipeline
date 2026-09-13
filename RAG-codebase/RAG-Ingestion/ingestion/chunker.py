from langchain_text_splitters import (
    RecursiveCharacterTextSplitter
)

class Chunker:
    def __init__(self):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )

    def create_chunks(self, pages):
        chunks = []
        chunk_counter = 0
        for page in pages:
            page_chunks = self.splitter.split_text(
                page["text"]
            )
            for chunk in page_chunks:
                chunks.append({
                    "chunk_id": f"chunk-{chunk_counter}",
                    "page_number": page["page_number"],
                    "text": chunk
                })
                chunk_counter += 1
        return chunks


"""
Flow of chunking: 

PDF
 ↓
Page 1
 ↓
1000 characters
 ↓
Chunk 0

Page 1
 ↓ 
1000 characters
 ↓
Chunk 1

"""