import azure.functions as func
import logging
import json
import os
import uuid
from azure.identity import DefaultAzureCredential
from azure.cosmos import CosmosClient

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

# --- Cosmos DB client setup (managed identity, no connection string / keys) ---
COSMOS_ENDPOINT = os.environ.get("COSMOS_ENDPOINT")
DATABASE_NAME = "notesdb"
CONTAINER_NAME = "notes"

_credential = DefaultAzureCredential()
_client = CosmosClient(url=COSMOS_ENDPOINT, credential=_credential)
_database = _client.get_database_client(DATABASE_NAME)
_container = _database.get_container_client(CONTAINER_NAME)


@app.route(route="notes", methods=["POST"])
def create_note(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Processing create_note request")

    try:
        body = req.get_json()
    except ValueError:
        return func.HttpResponse(
            json.dumps({"error": "Request body must be valid JSON"}),
            status_code=400,
            mimetype="application/json",
        )

    text = body.get("text")
    if not text:
        return func.HttpResponse(
            json.dumps({"error": "Field 'text' is required"}),
            status_code=400,
            mimetype="application/json",
        )

    note_id = str(uuid.uuid4())
    item = {
        "id": note_id,
        "partitionKey": note_id,  # simple partitioning; see README for production notes
        "text": text,
    }

    try:
        _container.create_item(body=item)
    except Exception as e:
        logging.error(f"Cosmos DB write failed: {e}")
        return func.HttpResponse(
            json.dumps({"error": "Failed to save note"}),
            status_code=500,
            mimetype="application/json",
        )

    return func.HttpResponse(
        json.dumps({"id": note_id, "text": text}),
        status_code=201,
        mimetype="application/json",
    )


@app.route(route="notes/{id}", methods=["GET"])
def get_note(req: func.HttpRequest) -> func.HttpResponse:
    note_id = req.route_params.get("id")
    logging.info(f"Processing get_note request for id={note_id}")

    try:
        item = _container.read_item(item=note_id, partition_key=note_id)
    except Exception as e:
        logging.warning(f"Note not found or read failed: {e}")
        return func.HttpResponse(
            json.dumps({"error": "Note not found"}),
            status_code=404,
            mimetype="application/json",
        )

    return func.HttpResponse(
        json.dumps({"id": item["id"], "text": item["text"]}),
        status_code=200,
        mimetype="application/json",
    )
