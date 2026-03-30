import React, { useState, useEffect, useRef } from 'react';
import { fetchEventSource } from '@microsoft/fetch-event-source';
import { marked } from 'marked';
import './App.css';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';
const USER_ID = 'web_user_001';

/**
 * Main App Component
 * Handles agent session management and message streaming
 */
function App() {
  const [sessionId, setSessionId] = useState(null);
  const [chatHistory, setChatHistory] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingText, setStreamingText] = useState('');
  const chatMessagesRef = useRef(null);

  // Initialize session on component mount
  useEffect(() => {
    createSession();
  }, []);

  // Auto-scroll to bottom when chat updates
  useEffect(() => {
    if (chatMessagesRef.current) {
      chatMessagesRef.current.scrollTop = chatMessagesRef.current.scrollHeight;
    }
  }, [chatHistory, streamingText]);

  /**
   * Create a new agent session
   */
  const createSession = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/sessions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: USER_ID })
      });

      const data = await response.json();
      setSessionId(data.session_id);
      console.log('Session created:', data.session_id);
    } catch (error) {
      console.error('Failed to create session:', error);
    }
  };

  /**
   * Send message to agent and handle streaming response
   */
  const sendMessage = async () => {
    const message = inputValue.trim();
    if (!message || !sessionId) return;

    // Add user message to chat history
    setChatHistory(prev => [...prev, { role: 'user', content: message }]);
    setInputValue('');
    setIsStreaming(true);
    setStreamingText('');

    let accumulatedText = '';

    try {
      await fetchEventSource(`${API_BASE_URL}/query`, {
        method: 'POST',
        openWhenHidden: true,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: USER_ID,
          session_id: sessionId,
          message: message
        }),

        onmessage(event) {
          try {
            const data = JSON.parse(event.data);
            
            console.log('Event:', data);

            // Extract text from the event
            let textContent = '';

            // Check for content.parts[0].text (Gemini response structure)
            if (data.content?.parts && Array.isArray(data.content.parts) && data.content.parts.length > 0) {
              const part = data.content.parts[0];
              textContent = part.text || part;
            }
            // Fallback to other possible text fields
            else if (data.text) {
              textContent = data.text;
            } else if (data.message) {
              textContent = data.message;
            }

            // Add text to accumulated content
            if (textContent) {
              accumulatedText += textContent;
              setStreamingText(accumulatedText);
            }

            // Finalize when server signals last event
            if (data.is_final && accumulatedText) {
              setChatHistory(prev => [...prev, { role: 'agent', content: accumulatedText }]);
              setIsStreaming(false);
              setStreamingText('');
            }
          } catch (err) {
            console.error('Error parsing event:', err);
          }
        },

        onerror(err) {
          console.error('SSE error:', err);
          setIsStreaming(false);
          throw err;
        }
      });
    } catch (error) {
      console.error('Failed to send message:', error);
      if (accumulatedText) {
        setChatHistory(prev => [...prev, { role: 'agent', content: accumulatedText }]);
      }
      setIsStreaming(false);
      setStreamingText('');
    }
  };

  /**
   * Handle Enter key to send message
   */
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  /**
   * Render a single message
   */
  const renderMessage = (msg, index) => {
    const label = msg.role === 'user' ? '💬 You' : '🤖 Agent';
    const content = msg.role === 'agent' 
      ? { __html: marked(msg.content) }
      : { __html: `<div>${msg.content}</div>` };

    return (
      <div key={index} className={`message ${msg.role}`}>
        <div className="label">{label}</div>
        <div className="content" dangerouslySetInnerHTML={content}></div>
      </div>
    );
  };

  return (
    <div className="app-container">
      <div className="chat-panel">
        <div className="header">
          <h1>Vertex AI Agent Client</h1>
          {sessionId && <div className="session-info">Session: {sessionId.slice(0, 8)}...</div>}
        </div>

        <div className="chat-messages" ref={chatMessagesRef}>
          {chatHistory.length === 0 && !isStreaming ? (
            <div className="empty-state">No messages yet. Start chatting!</div>
          ) : (
            <>
              {chatHistory.map((msg, index) => renderMessage(msg, index))}
              
              {isStreaming && (
                <div className="message agent streaming">
                  <div className="label">🤖 Agent</div>
                  <div 
                    className="content" 
                    dangerouslySetInnerHTML={{ 
                      __html: marked(streamingText || '') + '<span class="streaming-cursor"></span>' 
                    }}
                  />
                </div>
              )}
            </>
          )}
        </div>

        <div className="input-area">
          <textarea
            id="messageInput"
            placeholder="Type your message..."
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={!sessionId || isStreaming}
          />
          <button 
            onClick={sendMessage}
            disabled={!sessionId || isStreaming || !inputValue.trim()}
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}

export default App;
