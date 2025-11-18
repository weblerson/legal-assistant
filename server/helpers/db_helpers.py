import os
import psycopg2


def get_db_connection_sync():
    # TODO: host is not on the environment
    return psycopg2.connect(
        host="postgres",
        database=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        port=5432
    )
# TODO: port is not too


def save_rating_sync(request_user_id: int, rating: int):
    query = """
    INSERT INTO users_rate_tb (request_user_id, rating)
    VALUES (%s, %s)
    ON CONFLICT (request_user_id)
    DO UPDATE SET
        rating = EXCLUDED.rating,
        updated_at = CURRENT_TIMESTAMP;
    """

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (request_user_id, rating))
        conn.commit()
