import os
import json
import base64
from flask import Flask, request


# Initialize Flask app
app = Flask(__name__)


@app.route('/', methods=['GET'])
def main():
    return 'OK', 200

# Route to receive messages from Pub/Sub
@app.route('/process', methods=['POST'])
def receive_message():
    envelope = request.get_json()
    if not envelope:
        return 'Bad Request: No message received', 400

    message = envelope.get('message')
    if not message:
        return 'Bad Request: Invalid message format', 400

    message_data = message.get('data')
    decoded_message_data = base64.b64decode(message_data).decode('utf-8')
    print(f'decoded_message_data: {decoded_message_data}')
        

    return 'OK', 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))