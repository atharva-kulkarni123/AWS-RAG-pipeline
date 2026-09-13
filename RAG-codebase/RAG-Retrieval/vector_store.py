from psycopg import connect
from config import Config


class VectorStore:

    def __init__(self):
        self.connection_params = {
            "host": Config.DB_HOST,
            "port": Config.DB_PORT,
            "dbname": Config.DB_NAME,
            "user": Config.DB_USER,
            "password": Config.DB_PASSWORD,
        }

    def _get_connection(self):
        return connect(**self.connection_params)

    def similarity_search(
        self,
        query_embedding: list[float],
        top_k: int
    ) -> list[dict]:

        sql = """
            SELECT
                id,
                document_id,
                chunk_id,
                content,
                source,
                page_number,
                1 - (embedding <=> %s::vector) AS similarity
            FROM document_chunks
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> %s::vector
            LIMIT %s;
        """

        embedding_string = "[" + ",".join(
            str(value) for value in query_embedding
        ) + "]"

        with self._get_connection() as connection:
            with connection.cursor() as cursor:

                cursor.execute(
                    sql,
                    (
                        embedding_string,
                        embedding_string,
                        top_k
                    )
                )

                rows = cursor.fetchall()

        results = []

        for row in rows:
            results.append({
                "id": row[0],
                "document_id": row[1],
                "chunk_id": row[2],
                "content": row[3],
                "source": row[4],
                "page_number": row[5],
                "similarity": float(row[6])
            })

        return results