from flask import Flask, request, jsonify
import requests
import time
import os

app = Flask(__name__)

# Manus API configuration
MANUS_API_KEY = os.environ.get('MANUS_API_KEY', 'sk-lSp-jE07La22H2-5hGB93f9MnHBx2ShRwnoNM0fEKnOdgpAGvS0eLr5HPiOGNt2EMg2vxZe_EOQFgl6C')
MANUS_API_BASE = 'https://api.manus.ai/v1'

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy"}), 200

@app.route('/process-message', methods=['POST'])
def process_message():
    """
    Receives a message from Make.com, sends it to Manus API,
    waits for completion, and returns the response.
    """
    try:
        # Get the message from Make.com
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({"error": "Missing 'message' field in request"}), 400
        
        message = data['message']
        
        if not message or message.strip() == '':
            return jsonify({"error": "Message cannot be empty"}), 400
        
        # Step 1: Create Manus task
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
            timeout=30
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
        
        # Step 2: Wait for task completion (poll every 5 seconds, max 2 minutes)
        max_wait_time = 120  # 2 minutes
        poll_interval = 5  # 5 seconds
        elapsed_time = 0
        
        while elapsed_time < max_wait_time:
            time.sleep(poll_interval)
            elapsed_time += poll_interval
            
            # Get task status
            status_response = requests.get(
                f'{MANUS_API_BASE}/tasks/{task_id}',
                headers={'API_KEY': MANUS_API_KEY},
                timeout=30
            )
            
            if status_response.status_code != 200:
                continue  # Retry on error
            
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
                            "response": text_content,
                            "task_id": task_id
                        }), 200
                
                return jsonify({
                    "success": True,
                    "response": "Task completed but no response text found",
                    "task_id": task_id
                }), 200
            
            elif task_status == 'failed':
                return jsonify({
                    "error": "Manus task failed",
                    "task_id": task_id
                }), 500
        
        # Timeout
        return jsonify({
            "error": "Task did not complete within 2 minutes",
            "task_id": task_id
        }), 504
    
    except Exception as e:
        return jsonify({
            "error": "Internal server error",
            "details": str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
