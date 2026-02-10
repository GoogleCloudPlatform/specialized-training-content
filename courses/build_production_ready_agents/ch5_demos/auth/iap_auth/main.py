import os

from flask import Flask, jsonify, render_template_string, request

app = Flask(__name__)

# Modern HTML Frontend served directly by Flask
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>IAP Echo Service</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 1rem;
        }
        
        .container {
            background: white;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            padding: 2.5rem;
            max-width: 500px;
            width: 100%;
        }
        
        .header {
            text-align: center;
            margin-bottom: 2rem;
        }
        
        .header h1 {
            color: #333;
            font-size: 1.75rem;
            margin-bottom: 0.5rem;
            font-weight: 600;
        }
        
        .header p {
            color: #666;
            font-size: 0.95rem;
        }
        
        .user-badge {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1rem 1.5rem;
            border-radius: 12px;
            margin-bottom: 2rem;
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }
        
        .user-badge::before {
            content: "👤";
            font-size: 1.5rem;
        }
        
        .user-badge .label {
            font-size: 0.75rem;
            opacity: 0.9;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .user-badge .email {
            font-size: 1rem;
            font-weight: 500;
        }
        
        .divider {
            height: 1px;
            background: linear-gradient(to right, transparent, #e0e0e0, transparent);
            margin: 2rem 0;
        }
        
        .input-group {
            margin-bottom: 1.5rem;
        }
        
        .input-group label {
            display: block;
            color: #555;
            font-size: 0.9rem;
            font-weight: 500;
            margin-bottom: 0.5rem;
        }
        
        #msg {
            width: 100%;
            padding: 0.875rem 1rem;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 1rem;
            transition: all 0.3s ease;
            font-family: inherit;
        }
        
        #msg:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        button {
            width: 100%;
            padding: 1rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
        }
        
        button:active {
            transform: translateY(0);
        }
        
        #response {
            margin-top: 1.5rem;
            padding: 1rem;
            background: #f8f9fa;
            border-left: 4px solid #667eea;
            border-radius: 8px;
            min-height: 60px;
            display: none;
        }
        
        #response.show {
            display: block;
            animation: slideIn 0.3s ease;
        }
        
        #response .response-label {
            font-size: 0.75rem;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 0.5rem;
        }
        
        #response .response-text {
            color: #333;
            font-size: 1.1rem;
            font-weight: 500;
            word-wrap: break-word;
        }
        
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(-10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .security-badge {
            text-align: center;
            margin-top: 2rem;
            padding-top: 1.5rem;
            border-top: 1px solid #e0e0e0;
        }
        
        .security-badge span {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            color: #4caf50;
            font-size: 0.85rem;
            font-weight: 500;
        }
        
        .security-badge span::before {
            content: "🔒";
            font-size: 1rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛡️ IAP Echo Service</h1>
            <p>Identity-Aware Proxy Protected Application</p>
        </div>
        
        <div class="user-badge">
            <div>
                <div class="label">Authenticated as</div>
                <div class="email" id="user-info">Loading...</div>
            </div>
        </div>
        
        <div class="divider"></div>
        
        <div class="input-group">
            <label for="msg">Your Message</label>
            <input type="text" id="msg" placeholder="Type something to echo back..." 
                   onkeypress="if(event.key==='Enter') sendEcho()">
        </div>
        
        <button onclick="sendEcho()">Send Echo</button>
        
        <div id="response">
            <div class="response-label">Server Response</div>
            <div class="response-text" id="response-text"></div>
        </div>
        
        <div class="security-badge">
            <span>Secured by Google Cloud IAP</span>
        </div>
    </div>

    <script>
        // Fetch user info from IAP-injected headers
        fetch('/me')
            .then(r => r.json())
            .then(data => {
                document.getElementById('user-info').textContent = data.email;
            })
            .catch(err => {
                document.getElementById('user-info').textContent = 'Error loading user';
                console.error('Error:', err);
            });

        // Send echo request (IAP session cookie is automatically sent)
        async function sendEcho() {
            const msgInput = document.getElementById('msg');
            const msg = msgInput.value.trim();
            
            if (!msg) {
                alert('Please enter a message');
                return;
            }
            
            try {
                const res = await fetch('/echo', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: msg })
                });
                
                const data = await res.json();
                const responseDiv = document.getElementById('response');
                const responseText = document.getElementById('response-text');
                
                responseText.textContent = data.reply;
                responseDiv.classList.add('show');
                
                // Optional: Clear input after successful send
                // msgInput.value = '';
            } catch (error) {
                alert('Error sending message: ' + error.message);
                console.error('Error:', error);
            }
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/me')
def whoami():
    # IAP adds these headers automatically
    email = request.headers.get('X-Goog-Authenticated-User-Email', 'Unknown')
    # The header format is usually "accounts.google.com:email@example.com"
    clean_email = email.split(':')[-1] if ':' in email else email
    return jsonify({"email": clean_email})

@app.route('/echo', methods=['POST'])
def echo():
    data = request.get_json()
    return jsonify({"reply": f"Echo: {data.get('message')}"})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))