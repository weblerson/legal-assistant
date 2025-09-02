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


@app.post("/query/")
async def query() -> Response:
    request_data = request.get_json()
    if not request_data or "query" not in request_data:
        logger.error("Missing 'query' in request data")
        logger.error(f"Request data: {request_data}")

        return jsonify({"error": "Missing 'query' in request data"}), 400

    logger.info(f"Received query: {request_data['query']}")

    session_service = await create_temporary_session_async(
        app_name=current_app.config["APP_NAME"],
        user_id="default_user",
    )
    logger.info("Temporary session created")

    runner = await create_runner_async(
        app_name=current_app.config["APP_NAME"],
        session_service=session_service,
        agent=await create_root_agent_async(),
    )
    logger.info("Runner created")

    user_query = request_data["query"]
    content = types.Content(role="user", parts=[types.Part(text=user_query)])

    async for event in runner.run_async(
        user_id="default_user",
        session_id="default_session",
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

"""
No caso dos sistemas invariantes de tempo discreto, a necessidade de alteração do
sinal de entrada pode ser um movimento de retardo ou um movimento de avanço
"""
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
