import os
from flask import Flask, jsonify, render_template_string
import redis

app = Flask(__name__)
redis_client = redis.Redis(host=os.getenv('REDIS_HOST', 'redis'), port=6379, db=0)

# HTML template for displaying messages
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Message Viewer</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f0f0f0;
        }
        .container {
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        .message-list {
            margin-top: 20px;
        }
        .message {
            background-color: #8026a7;
            padding: 15px;
            margin-bottom: 10px;
            border-radius: 4px;
            border-left: 4px solid #4CAF50;
        }
        .no-messages {
            color: #666;
            font-style: italic;
        }
        .refresh-button {
            background-color: #4CAF50;
            color: white;
            padding: 10px 15px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            margin-bottom: 20px;
        }
        .refresh-button:hover {
            background-color: #45a049;
        }
        .timestamp {
            color: #666;
            font-size: 0.8em;
            margin-top: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Message Viewer</h1>
        <button class="refresh-button" onclick="location.reload()">Refresh Messages</button>
        <div class="message-list">
            {% if messages %}
                {% for message in messages %}
                    <div class="message">
                        <div>{{ message }}</div>
                    </div>
                {% endfor %}
            {% else %}
                <div class="no-messages">No messages available</div>
            {% endif %}
        </div>
    </div>
</body>
</html>
'''

@app.route('/')
def index():
    # Get all messages from Redis
    messages = []
    while True:
        message = redis_client.rpop("messages")
        if not message:
            break
        messages.append(message.decode('utf-8'))
    
    # Reverse the messages so newest are at the top
    messages.reverse()
    
    return render_template_string(HTML_TEMPLATE, messages=messages)

@app.route('/health')
def health():
    return jsonify(status="healthy")

@app.route('/messages', methods=['GET'])
def get_messages():
    # API endpoint to get messages as JSON
    messages = []
    while True:
        message = redis_client.rpop("messages")
        if not message:
            break
        messages.append(message.decode('utf-8'))
    
    messages.reverse()
    return jsonify(messages=messages)

if __name__ == '__main__':
    app_port = int(os.getenv("APP_PORT", 5000))
    app.run(host='0.0.0.0', port=app_port)