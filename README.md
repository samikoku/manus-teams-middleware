# Manus AI Middleware for Microsoft Teams

This Flask application acts as a middleware bridge between Make.com and the Manus AI API, handling the complexity of task creation, polling, and response retrieval.

## Features

- Receives webhook calls from Make.com with Teams message content
- Creates Manus AI tasks with proper API authentication
- Polls for task completion with timeout handling
- Returns formatted responses ready for Teams
- Secure API key storage via environment variables

## Deployment

### Environment Variables Required

```
MANUS_API_KEY=sk-lSp-jE07La22H2-5hGB93f9MnHBx2ShRwnoNM0fEKnOdgpAGvS0eLr5HPiOGNt2EMg2vxZe_EOQFgl6C
PORT=5000
```

### Deploy to Render.com (Free Tier)

1. Create a new Web Service
2. Connect this repository
3. Set environment variables in the Render dashboard
4. Deploy

The service will be available at: `https://your-app-name.onrender.com`

## API Endpoints

### POST /process-message

Processes a message through Manus AI and returns the response.

**Request Body:**
```json
{
  "message": "Your question here"
}
```

**Response:**
```json
{
  "success": true,
  "response": "AI response text",
  "task_id": "task_id_string"
}
```

### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy"
}
```

## Make.com Integration

Replace your current HTTP modules with a single HTTP module:

1. **Method:** POST
2. **URL:** `https://your-app-name.onrender.com/process-message`
3. **Headers:** `Content-Type: application/json`
4. **Body:** 
```json
{
  "message": "{{5.bodyPlainTextContent}}"
}
```
5. **Parse Response:** Yes
6. **Use:** `{{response}}` in your Teams reply

## Testing

Test locally:
```bash
python3.11 app.py
```

Test the endpoint:
```bash
curl -X POST http://localhost:5000/process-message \
  -H "Content-Type: application/json" \
  -d '{"message": "What are NAKACHI Consulting services?"}'
```

## Performance

- Average response time: 50-60 seconds for Knowledge Base queries
- Timeout: 180 seconds
- Polling interval: 5 seconds
