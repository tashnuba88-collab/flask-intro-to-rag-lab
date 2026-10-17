# Context-Aware RAG Endpoint with Flask

A small Flask API that answers employee questions using approved company documents. It follows a simplified RAG flow: query, retrieval, context, prompt, model response, source-backed JSON.

## Endpoints

`GET /api/health` returns `{"status": "ok"}`.

`POST /api/ask` takes JSON like `{"query": "How do I request software access?"}` and returns:

```json
{
  "query": "How do I request software access?",
  "answer": "...generated answer...",
  "sources": [
    {"id": "ops_software_access", "title": "Software Access Request Process"}
  ]
}
```

Other responses:

- `400` with an `error` message when the query is missing, blank, or not a string.
- `200` with a fallback answer and an empty `sources` list when no document matches. The model is not called in this case.
- `503` with an `error` message when the model service raises a `RuntimeError`.

## How it works

`lib/rag_service.py` does the retrieval work. It lowercases the query and each document, drops stopwords and one-letter tokens, and scores each document by how many query terms it shares. Query terms found in the title add 0.5 each. Documents scoring at least 1.0 are sorted high to low and the top two are kept. The selected documents are formatted into a context block, and the prompt tells the model to use only that context and not invent details.

`lib/app.py` runs the route. It validates the query, retrieves context, builds the prompt, calls `generate_response`, and returns the answer with each source's ID and title.

## Run it

```bash
pipenv install
pipenv shell
pytest
```

To run the app by hand (needs Ollama with `llama3.2` for real answers):

```bash
flask --app lib.app run --debug
curl -i http://127.0.0.1:5000/api/health
```

The tests mock the model call, so they pass without Ollama. The Pipfile lists Python 3.12 because 3.11 was not installed on my machine.

## Reflection

At the start 18 of the 19 tests failed because every function was still a placeholder. The test file was the most useful guide, since it showed exact strings the TODOs didn't spell out, like the "Source ID:" label and the "no relevant context" message. What I took from the lab is that retrieval decides which document the model sees, so the answer stays tied to approved text, and a query with no match gets a fallback without a model call. Keyword matching is crude. A question that uses different words than the document, like "developers" versus "developer", can miss, which is the kind of gap embeddings are meant to close.
