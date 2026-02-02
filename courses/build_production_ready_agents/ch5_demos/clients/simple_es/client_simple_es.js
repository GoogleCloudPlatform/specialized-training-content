import { fetchEventSource } from 'https://cdn.jsdelivr.net/npm/@microsoft/fetch-event-source@2.0.1/+esm';

const API_BASE_URL = 'http://localhost:8000';
const USER_ID = 'web_user_001';

let currentSessionId = null;
let chatHistory = [];

// Initialize session when page loads
window.addEventListener('DOMContentLoaded', async () => {
    await createSession();
});

// Create a new session
async function createSession() {
    const response = await fetch(`${API_BASE_URL}/sessions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
            user_id: USER_ID,
            initial_state: {}
        })
    });
    
    const data = await response.json();
    currentSessionId = data.session_id;
    console.log('Session created:', currentSessionId);
    renderChat();
}

// Send message to agent
window.sendMessage = async function() {
    const input = document.getElementById('messageInput');
    const message = input.value.trim();
    
    if (!message) return;
    
    // Add user message to UI
    addMessage('user', message);
    input.value = '';
    
    // Create streaming message container
    let streamingText = '';
    const messageDiv = createStreamingMessage();
    
    // Use fetchEventSource for SSE with POST support
    await fetchEventSource(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
            user_id: USER_ID,
            session_id: currentSessionId,
            message: message
        }),
        
        onmessage(event) {
            const data = JSON.parse(event.data);
            
            if (data.type === 'response_chunk' && !data.is_final) {
                streamingText += data.text;
                updateStreamingMessage(messageDiv, streamingText);
            } else if (data.is_final) {
                finalizeMessage(messageDiv, streamingText);
            }
        },
        
        onerror(err) {
            console.error('SSE error:', err);
            throw err; // Stops reconnection attempts
        }
    });
}

// Add a message to chat history and render
function addMessage(role, content) {
    chatHistory.push({ role, content });
    renderChat();
}

// Create a streaming message element
function createStreamingMessage() {
    const chatArea = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message agent streaming';
    
    messageDiv.innerHTML = `
        <div class="label">🤖 Agent</div>
        <div class="content"><span class="streaming-cursor"></span></div>
    `;
    
    chatArea.appendChild(messageDiv);
    chatArea.scrollTop = chatArea.scrollHeight;
    
    return messageDiv;
}

// Update streaming message with new text
function updateStreamingMessage(messageDiv, text) {
    const content = messageDiv.querySelector('.content');
    content.innerHTML = marked.parse(text) + '<span class="streaming-cursor"></span>';
    
    const chatArea = document.getElementById('chatMessages');
    chatArea.scrollTop = chatArea.scrollHeight;
}

// Finalize the streaming message
function finalizeMessage(messageDiv, text) {
    chatHistory.push({ role: 'agent', content: text });
    
    messageDiv.classList.remove('streaming');
    const content = messageDiv.querySelector('.content');
    content.innerHTML = marked.parse(text);
    
    const chatArea = document.getElementById('chatMessages');
    chatArea.scrollTop = chatArea.scrollHeight;
}

// Render all chat messages
function renderChat() {
    const chatArea = document.getElementById('chatMessages');
    
    if (chatHistory.length === 0) {
        chatArea.innerHTML = '<div class="empty-state">No messages yet. Start chatting!</div>';
        return;
    }
    
    chatArea.innerHTML = chatHistory.map(msg => {
        const label = msg.role === 'user' ? '💬 You' : '🤖 Agent';
        const content = msg.role === 'agent' 
            ? marked.parse(msg.content)
            : `<div>${msg.content}</div>`;
        
        return `
            <div class="message ${msg.role}">
                <div class="label">${label}</div>
                <div class="content">${content}</div>
            </div>
        `;
    }).join('');
    
    chatArea.scrollTop = chatArea.scrollHeight;
}

// Handle Enter key to send message
window.handleKeyDown = function(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}
