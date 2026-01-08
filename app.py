from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# Manus API configuration
MANUS_API_KEY = os.environ.get('MANUS_API_KEY', 'sk-lSp-jE07La22H2-5hGB93f9MnHBx2ShRwnoNM0fEKnOdgpAGvS0eLr5HPiOGNt2EMg2vxZe_EOQFgl6C')
MANUS_API_BASE = 'https://api.manus.ai/v1'

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy"}), 200

@app.route('/create-task', methods=['POST'])
def create_task():
    """
    Step 1: Receives a message from Make.com and creates a Manus task.
    Returns the task_id immediately (within 30 seconds).
    """
    try:
        # Get the message from Make.com
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({"error": "Missing 'message' field in request"}), 400
        
        message = data['message']
        
        if not message or message.strip() == '':
            return jsonify({"error": "Message cannot be empty"}), 400
        
        # Create Manus task
        create_response = requests.post(
            f'{MANUS_API_BASE}/tasks',
            headers={
                'API_KEY': MANUS_API_KEY,
                'Content-Type': 'application/json'
            },
            json={
                'prompt': message,
                'agentProfile': 'manus-1.6'
            },
            timeout=25
        )
        
        if create_response.status_code != 200:
            return jsonify({
                "error": "Failed to create Manus task",
                "details": create_response.text
            }), 500
        
        task_data = create_response.json()
        task_id = task_data.get('task_id')
        
        if not task_id:
            return jsonify({
                "error": "No task_id in Manus response",
                "details": task_data
            }), 500
        
        # Return task_id immediately
        return jsonify({
            "success": True,
            "task_id": task_id,
            "message": "Task created successfully. Use /get-result endpoint to retrieve the response."
        }), 200
    
    except Exception as e:
        return jsonify({
            "error": "Internal server error",
            "details": str(e)
        }), 500

@app.route('/get-result', methods=['POST'])
def get_result():
    """
    Step 2: Retrieves the result of a Manus task by task_id.
    Make.com should call this after waiting 60 seconds.
    """
    try:
        # Get the task_id from Make.com
        data = request.get_json()
        
        if not data or 'task_id' not in data:
            return jsonify({"error": "Missing 'task_id' field in request"}), 400
        
        task_id = data['task_id']
        
        if not task_id or task_id.strip() == '':
            return jsonify({"error": "task_id cannot be empty"}), 400
        
        # Get task status and result
        status_response = requests.get(
            f'{MANUS_API_BASE}/tasks/{task_id}',
            headers={'API_KEY': MANUS_API_KEY},
            timeout=25
        )
        
        if status_response.status_code != 200:
            return jsonify({
                "error": "Failed to get task status",
                "details": status_response.text
            }), 500
        
        status_data = status_response.json()
        task_status = status_data.get('status')
        
        if task_status == 'completed':
            # Extract the response text
            output = status_data.get('output', [])
            if output and len(output) > 0:
                last_message = output[-1]
                content = last_message.get('content', [])
                if content and len(content) > 0:
                    text_content = content[0].get('text', '')
                    return jsonify({
                        "success": True,
                        "status": "completed",
                        "response": text_content,
                        "task_id": task_id
                    }), 200
            
            return jsonify({
                "success": True,
                "status": "completed",
                "response": "Task completed but no response text found",
                "task_id": task_id
            }), 200
        
        elif task_status == 'failed':
            return jsonify({
                "success": False,
                "status": "failed",
                "error": "Manus task failed",
                "task_id": task_id
            }), 200
        
        else:
            # Task is still processing
            return jsonify({
                "success": False,
                "status": task_status,
                "message": "Task is still processing. Please try again in a few seconds.",
                "task_id": task_id
            }), 200
    
    except Exception as e:
        return jsonify({
            "error": "Internal server error",
            "details": str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
