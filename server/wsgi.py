import os
import logging
import psycopg2

from dotenv import load_dotenv
from flask import (
    current_app,
    Flask,
    jsonify,
    request,
    Response,
)
from google.genai import types

from google.adk.agents import LlmAgent
from google.genai import errors as google_exceptions

from agents.legal_dispatcher.agent import (
    create_root_agent_async,
    create_runner_async,
    create_session_async,
    delete_session_async,
    instantiate_database_session_service,
    retrieve_session_async,
)
from helpers.context_helpers import (
    ContextKey,
    get_context_var,
    set_context_var,
)
from helpers.db_helpers import (
    get_db_connection_sync,
    save_rating_sync,
)
from helpers.sessions import (
    instantiate_redis_client,
    pop_user_id,
    retrieve_user_id,
    set_user_id,
)

from helpers.rag import instantiate_rag_object, retrieve_chunks

entrypoint = os.path.abspath(os.path.dirname(__file__))
logger = logging.getLogger("server_logs")
logger.setLevel(logging.INFO)

server_logs_path = os.path.join(entrypoint, "server_logs.log")
file_handler = logging.FileHandler(server_logs_path)
file_handler.setLevel(logging.INFO)

formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

logger.addHandler(file_handler)

load_dotenv()

app = Flask(__name__)
app.config.from_prefixed_env()

AGENT_KEY = ContextKey[LlmAgent]("agent")


@app.post("/query/")
async def query() -> tuple[Response, int]:
    request_data = request.get_json()
    if not request_data:
        logger.error("Missing request data.")

        return jsonify({"response": "Missing request data."}), 400

    if "query" not in request_data:
        logger.error("Missing 'query' in request data")
        logger.error(f"Request data: {request_data}")

        return jsonify({"response": "Missing request data."}), 400

    if not request_data or "username" not in request_data or "user_id" not in request_data:
        logger.error("Missing request data")
        logger.error(f"Request data: {request_data}")

        return jsonify({"response": "Missing request data."}), 400

    logger.info(f"Received query: {request_data['query']}")

    request_username = request_data["username"]
    request_user_id = request_data["user_id"]

    # TODO: put these arguments into the environment
    redis_host = os.environ["REDIS_HOST"]
    redis_port = os.environ["REDIS_PORT"]

    redis_client = await instantiate_redis_client(redis_host, int(redis_port))
    user_id_bytes = await retrieve_user_id(request_user_id, redis_client)
    if user_id_bytes is None:
        user_id_bytes = await set_user_id(
            request_user_id,
            request_username,
            redis_client,
        )

    user_id = user_id_bytes.decode("utf-8")
    if user_id.startswith("b'") and user_id.endswith("'"):
        user_id = user_id[2:-1]

    session_id = f"session://{user_id}"

    db_url: str = current_app.config["DB_URL"]
    app_name: str = current_app.config["APP_NAME"]
    database_session_service = await instantiate_database_session_service(
        db_url,
    )

    session = await retrieve_session_async(
        database_session_service,
        app_name,
        user_id,
        session_id,
    )
    if session is None:
        session = await create_session_async(
            database_session_service,
            app_name,
            user_id,
            session_id,
        )

    agent: LlmAgent | None = await get_context_var(AGENT_KEY)
    if agent is None:
        _agent = await create_root_agent_async()
        await set_context_var(AGENT_KEY, _agent)

        agent = _agent

    runner = await create_runner_async(
        app_name=app_name,
        session_service=database_session_service,
        agent=agent,
    )
    logger.info("Runner created")

    try:
        ragflow_api_key = os.environ["RAGFLOW_API_KEY"]
        ragflow_base_url = os.environ["RAGFLOW_BASE_URL"]
        law_dataset_name = os.environ["LAW_DATASET_NAME"]

        prompt_template = (
            "{user_query}\n\n"
            "Please, use the provided context below to provide "
            "a better response to the user.\n\n"
            "{chunks}"
        )

        user_query = request_data["query"]

        rag_object = await instantiate_rag_object(
            api_key=ragflow_api_key,
            base_url=ragflow_base_url,
        )
        chunks = await retrieve_chunks(
            law_dataset_name,
            user_query,
            rag_object,
        )

        formatted_chunks = ""
        for i, chunk in enumerate(chunks):
            formatted_text = f"Chunk #{i+1}\n{chunk.content}\n\n"
            formatted_chunks += formatted_text

        final_prompt = prompt_template.format(
            user_query=user_query,
            chunks=formatted_chunks,
        )

        content = types.Content(
            role="user",
            parts=[types.Part(text=final_prompt)]
        )
        logger.info(f"Final prompt:\n{final_prompt}")

        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=content,
        ):
            if event.is_final_response():
                final_response = event.content.parts[0].text
                data = {
                    "response": final_response,
                }
                logger.info(f"Final model's response: {final_response}")

                return jsonify(data), 200

        response = {"response": "No final response received from agent."}

        logger.warning("Runner finished without a final response event.")
        return jsonify(response), 500

    # TODO: invest in better error handling
    except google_exceptions.ServerError:
        import traceback

        response = {
            "response": "Internal Server Error",
        }
        logger.error(traceback.format_exc())

        return jsonify(response), 500

    except google_exceptions.ClientError as e:
        import traceback

        response = {
            "response": "Client error."
        }

        # TODO: this should try again
        if e.code == 400:
            response = {
                "response": "The request was invalid."
            }

            await pop_user_id(user_id, redis_client)

            await delete_session_async(
                database_session_service,
                app_name,
                user_id,
                session_id,
            )

        # TODO: this should clean session and try again
        elif e.code == 429:
            response = {
                "response": "Limit quota exceeded",
            }

            await pop_user_id(user_id, redis_client)

            await delete_session_async(
                database_session_service,
                app_name,
                user_id,
                session_id,
            )

        logger.error(traceback.format_exc())

        return jsonify(response), 429

    except Exception as e:
        import traceback

        # Catch-all for unexpected errors to ensure a tuple is always returned
        logger.error(f"Unexpected error: {e}")
        logger.error(traceback.format_exc())
        return jsonify({"response": f"An unexpected error occurred: {e}"}), 500


@app.delete("/clear/")
async def clear_session():
    request_user_id = request.args.get("user_id")

    redis_host = os.environ["REDIS_HOST"]
    redis_port = os.environ["REDIS_PORT"]

    redis_client = await instantiate_redis_client(redis_host, int(redis_port))
    user_id_bytes = await retrieve_user_id(request_user_id, redis_client)
    if user_id_bytes is None:
        return jsonify(), 204

    user_id = user_id_bytes.decode("utf-8")
    if user_id.startswith("b'") and user_id.endswith("'"):
        user_id = user_id[2:-1]

    session_id = f"session://{user_id}"

    db_url: str = current_app.config["DB_URL"]
    app_name: str = current_app.config["APP_NAME"]
    database_session_service = await instantiate_database_session_service(
        db_url,
    )

    await pop_user_id(request_user_id, redis_client)

    await delete_session_async(
        database_session_service,
        app_name,
        user_id,
        session_id,
    )

    return jsonify(), 200


@app.post("/rate/")
async def rate_interaction():
    request_data = request.get_json()

    if not request_data or "request_user_id" not in request_data or "rating" not in request_data:
        logger.error(f"Invalid rating data: {request_data}")
        return jsonify({"error": "Missing user_id or rating"}), 400

    request_user_id = request_data["request_user_id"]
    rating = request_data["rating"]

    try:
        rating = int(rating)
    except ValueError:
        return jsonify({"error": "Rating must be an integer"}), 400

    logger.info(f"Received rating {rating} from user {request_user_id}")

    def _get_db_connection():
        # TODO: host is not on the environment
        return psycopg2.connect(
            host="postgres",
            database=os.environ["POSTGRES_DB"],
            user=os.environ["POSTGRES_USER"],
            password=os.environ["POSTGRES_PASSWORD"],
            port=5432
        )
        # TODO: port is not too

    upsert_query = """
    INSERT INTO users_rate_tb (request_user_id, rating)
    VALUES (%s, %s)
    ON CONFLICT (request_user_id)
    DO UPDATE SET
        rating = EXCLUDED.rating,
        updated_at = CURRENT_TIMESTAMP;
    """

    try:
        with _get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(upsert_query, (request_user_id, rating))
            conn.commit()

        return jsonify({"message": "Rating saved"}), 200

    except Exception as e:
        logger.error(f"Database error saving rating: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({"error": "Failed to save rating"}), 500


@app.get("/healthcheck/")
async def healthcheck():
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    with app.app_context():
        logger.info("Starting the server...")

        try:
            debug: bool = current_app.config["DEBUG"]
            host: str = current_app.config["HOST"]
            port: str = current_app.config["PORT"]

            app.run(
                debug=debug,
                host=host,
                port=int(port),
            )

        except KeyboardInterrupt:
            logger.info("Server stopped by user")

        except ValueError as e:
            import traceback

            logger.error(f"Configuration error: {e}")
            logger.error(traceback.format_exc())
