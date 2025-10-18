import base64
import os
import logging

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

    instantiate_database_session_service,
    create_session_async,
    retrieve_session_async,
)
from helpers.context_helpers import (
    ContextKey,
    get_context_var,
    set_context_var,
)

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


# TODO: implement session destruction
@app.post("/query/")
async def query() -> tuple[Response, int]:
    request_data = request.get_json()
    if not request_data:
        logger.error("Missing request data.")

        return jsonify({"error": "Missing request data."}), 400

    if "query" not in request_data:
        logger.error("Missing 'query' in request data")
        logger.error(f"Request data: {request_data}")

        return jsonify({"error": "Missing request data."}), 400

    if not request_data or "username" not in request_data:
        logger.error("Missing 'username' in request data")
        logger.error(f"Request data: {request_data}")

        return jsonify({"error": "Missing request data."}), 400

    logger.info(f"Received query: {request_data['query']}")

    request_username = request_data["username"]
    encoded_request_username = base64.b64encode(request_username.encode())

    session_id = f"session://{request_username}"
    encoded_session_id = base64.b64encode(session_id.encode())

    db_url: str = current_app.config["DB_URL"]
    app_name: str = current_app.config["APP_NAME"]
    user_id = encoded_request_username.decode()
    session_id = encoded_session_id.decode()
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

    user_query = request_data["query"]
    content = types.Content(role="user", parts=[types.Part(text=user_query)])

    try:
        async for event in runner.run_async(
            user_id=encoded_request_username.decode(),
            session_id=encoded_session_id.decode(),
            new_message=content,
        ):
            logger.info(f"Event received: {event}")

            if event.is_final_response():
                final_response = event.content.parts[0].text
                data = {
                    "response": final_response,
                }
                logger.info(f"Final model's response: {final_response}")

                return jsonify(data), 200

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

        # TODO: this should clean session and try again
        elif e.code == 429:
            response = {
                "response": "Limit quota exceeded",
            }

        logger.error(traceback.format_exc())

        return jsonify(response), 429


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
