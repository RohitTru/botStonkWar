import os
from flask import Flask, jsonify, request, render_template_string
import redis

app = Flask(__name__)
redis_client = redis.Redis(host=os.getenv('REDIS_HOST', 'redis'), port=6379, db=0)

# HTML template for the form
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Message Sender</title>
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
        .form-group {
            margin-bottom: 15px;
        }
        textarea {
            width: 100%;
            padding: 8px;
            margin: 8px 0;
            border: 1px solid #ddd;
            border-radius: 4px;
            height: 100px;
            resize: vertical;
        }
        button {
            background-color: #4CAF50;
            color: white;
            padding: 10px 15px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        button:hover {
            background-color: #45a049;
        }
        .result {
            margin-top: 20px;
            padding: 10px;
            border-radius: 4px;
        }
        .success {
            background-color: #dff0d8;
            border: 1px solid #d6e9c6;
            color: #3c763d;
        }
        .error {
            background-color: #f2dede;
            border: 1px solid #ebccd1;
            color: #a94442;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Message Sender</h1>
        <form id="messageForm">
            <div class="form-group">
                <label for="message">Enter your message:</label>
                <textarea id="message" name="message" required></textarea>
            </div>
            <button type="submit">Send Message</button>
        </form>
        <div id="result" class="result" style="display: none;"></div>
    </div>

    <script>
        document.getElementById('messageForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const message = document.getElementById('message').value;
            const resultDiv = document.getElementById('result');

            try {
                const response = await fetch('/send-message', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ message }),
                });

                const data = await response.json();

                if (response.ok) {
                    resultDiv.className = 'result success';
                    resultDiv.textContent = 'Message sent successfully!';
                } else {
                    resultDiv.className = 'result error';
                    resultDiv.textContent = data.error || 'Failed to send message';
                }
            } catch (error) {
                resultDiv.className = 'result error';
                resultDiv.textContent = 'Error sending message';
            }

            resultDiv.style.display = 'block';

            setTimeout(() => {
                document.getElementById('message').value = '';
                resultDiv.style.display = 'none';
            }, 3000);
        });
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/health')
def health():
    return jsonify(status="healthy")

@app.route('/send-message', methods=['POST'])
def send_message():
    data = request.json
    message = data.get('message', '')
    if not message:
        return jsonify(error="Message is required"), 400

    # Store message in Redis
    redis_client.lpush("messages", message)

    return jsonify(
        status="success",
        message="Message sent successfully",
        sent_message=message
    )

if __name__ == '__main__':
    app_port = int(os.getenv("APP_PORT", 5001))
    app.run(host='0.0.0.0', port=app_port)
