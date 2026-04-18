#updating the flask application to support actual UI's streaming responses
# but in end point it will give response at once
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from trainapp import user_input

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes by default

# In-memory storage for API keys (use a database in production)
api_keys = os.getenv("SECURE_API_KEY")

# Route to handle chatbot queries with API key validation
@app.route('/chatbot', methods=['POST'])
def chatbot():
    api_key = request.headers.get('x-api-key')
    #if api_key not in api_keys:
    #    return jsonify({'error': 'Invalid API key'}), 403

    data = request.json
    user_question = data.get('question')
    chat_history = data.get('chat_history')
    
    
    response = user_input(user_question, chat_history)  # this is code when for loop sleep timer is not in count
    # Collecting all words from the generator and form a complete response this is for streaming responses 
    # response = " ".join(word for word in user_input(user_question, chat_history))
    return jsonify({'response': response})

if __name__ == '__main__':
    host = os.getenv('FLASK_RUN_HOST')
    port = int(os.getenv('FLASK_RUN_PORT'))
    app.run(debug=True, host=host, port=port)
