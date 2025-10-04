# Changi Airport RAG Chatbot - API Documentation

## Base URL
```
http://localhost:8000
```

## Authentication
All endpoints are currently unauthenticated. For production use, consider adding API key authentication.

## Endpoints

### 1. Chat Endpoint

#### POST /chat
Send a message to the chatbot and get a response.

**Request:**
```http
POST /chat
Content-Type: application/json

{
  "question": "What are the operating hours for Jewel Changi?"
}
```

**Parameters:**
- `question` (string, required): The user's question

**Response:**
```json
{
  "answer": "Jewel Changi is open from 10:00 AM to 10:00 PM daily. However, individual store and restaurant hours may vary.",
  "sources": [
    {
      "url": "https://www.jewelchangiairport.com/en/plan-your-visit/opening-hours.html",
      "text_snippet": "Jewel Changi operating hours are from 10:00 AM to 10:00 PM daily..."
    }
  ]
}
```

### 2. Web Interface

#### GET /
Serves the chat web interface.

**Request:**
```http
GET /
```

**Response:**
HTML page with the chat interface.

### 3. Health Check

#### GET /health
Check if the API is running.

**Request:**
```http
GET /health
```

**Response:**
```json
{
  "status": "ok",
  "version": "1.0.0",
  "models": {
    "primary": "mistral",
    "fallback": "llama2",
    "embedding": "all-minilm"
  }
}
```

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Question cannot be empty"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error",
  "error": "Error details here"
}
```

## Rate Limiting
Currently, there is no rate limiting implemented. For production use, consider implementing rate limiting to prevent abuse.

## WebSocket Support
Not currently implemented, but could be added for real-time chat functionality.

## Testing the API

### Using cURL
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the operating hours?"}'
```

### Using Python
```python
import requests

response = requests.post(
    "http://localhost:8000/chat",
    json={"question": "What are the operating hours?"}
)
print(response.json())
```

## Versioning
API versioning is not currently implemented. All endpoints are under v1.

## Changelog
- 2025-07-28: Initial API release

## Future Improvements
1. Add authentication
2. Implement rate limiting
3. Add WebSocket support
4. Add API versioning
5. Add more detailed error codes and messages
