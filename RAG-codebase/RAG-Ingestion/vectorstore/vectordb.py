import psycopg
from pgvector.psycopg import register_vector
from config import Config

class VectorDB:
    def __init__(self):
        self.connection = psycopg.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            dbname=Config.DB_NAME,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD
        )
        register_vector(self.connection)

    def document_exists(self, document_id):
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM document_chunks
                    WHERE document_id = %s
                )
                """,
                (document_id,)
            )
            return cursor.fetchone()[0]

    def insert_chunk(
        self,
        document_id,
        chunk_id,
        content,
        embedding,
        page_number,
        source
    ):

        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO document_chunks
                (
                    document_id,
                    chunk_id,
                    content,
                    embedding,
                    page_number,
                    source
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    document_id,
                    chunk_id,
                    content,
                    embedding,
                    page_number,
                    source
                )
            )

        self.connection.commit()
    def close(self):
        self.connection.close()