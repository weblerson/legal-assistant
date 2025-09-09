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

from agents.legal_dispatcher.agent import (
    create_root_agent_async,
    create_runner_async,
    create_temporary_session_async,
)
from helpers.context_helpers import get_context_var, set_context_var

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


# TODO: implement session destruction
@app.post("/query/")
async def query() -> Response:
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

    if not await get_context_var(encoded_session_id):
        session_service = await create_temporary_session_async(
            app_name=current_app.config["APP_NAME"],
            user_id=encoded_request_username.decode(),
            session_id=encoded_session_id.decode(),
        )
        await set_context_var(encoded_session_id, session_service)

        logger.info("Temporary session created")

    if await get_context_var("agent") is None:
        _agent = await create_root_agent_async()
        await set_context_var("agent", _agent)

    runner = await create_runner_async(
        app_name=current_app.config["APP_NAME"],
        session_service=await get_context_var(encoded_session_id),
        agent=await get_context_var("agent"),
    )
    logger.info("Runner created")

    user_query = request_data["query"]
    content = types.Content(role="user", parts=[types.Part(text=user_query)])

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


if __name__ == "__main__":
    with app.app_context():
        logger.info("Starting the server...")

        try:
            debug: bool = current_app.config["DEBUG"]
            host: str = current_app.config["HOST"]
            port: str = current_app.config["PORT"]

            app.run(debug=debug, host=host, port=port)

        except KeyboardInterrupt:
            logger.info("Server stopped by user")

        except ValueError as e:
            import traceback

            logger.error(f"Configuration error: {e}")
            logger.error(traceback.format_exc())
