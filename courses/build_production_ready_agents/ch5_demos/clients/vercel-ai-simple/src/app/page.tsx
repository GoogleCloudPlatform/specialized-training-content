'use client';

import { useChat } from 'ai/react';
import { useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';

const API_BASE_URL = 'http://localhost:8000';
const USER_ID = 'web_user_001';

export default function Chat() {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { messages, input, handleInputChange, handleSubmit, isLoading } = useChat({
    api: '/api/chat',
    body: {
      user_id: USER_ID,
    },
  });

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div style={styles.container}>
      <div style={styles.chatPanel}>
        <div style={styles.header}>
          <h1 style={styles.title}>ADK Agent Client</h1>
          <p style={styles.subtitle}>Vercel AI SDK</p>
        </div>

        <div style={styles.messagesContainer}>
          {messages.length === 0 ? (
            <div style={styles.emptyState}>No messages yet. Start chatting!</div>
          ) : (
            messages.map((message) => (
              <div
                key={message.id}
                style={{
                  ...styles.message,
                  ...(message.role === 'user' ? styles.userMessage : styles.assistantMessage),
                }}
              >
                <div style={styles.messageLabel}>
                  {message.role === 'user' ? '💬 You' : '🤖 Agent'}
                </div>
                <div style={styles.messageContent}>
                  {message.role === 'user' ? (
                    message.content
                  ) : (
                    <ReactMarkdown>{message.content}</ReactMarkdown>
                  )}
                </div>
              </div>
            ))
          )}
          <div ref={messagesEndRef} />
        </div>

        <form onSubmit={handleSubmit} style={styles.inputArea}>
          <textarea
            value={input}
            onChange={handleInputChange}
            placeholder="Type your message..."
            style={styles.textarea}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSubmit(e as any);
              }
            }}
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            style={{
              ...styles.button,
              ...(isLoading || !input.trim() ? styles.buttonDisabled : {}),
            }}
          >
            Send
          </button>
        </form>
      </div>
    </div>
  );
}

const styles: { [key: string]: React.CSSProperties } = {
  container: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    minHeight: '100vh',
    backgroundColor: '#f5f5f5',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
  },
  chatPanel: {
    display: 'flex',
    flexDirection: 'column',
    width: '100%',
    maxWidth: '800px',
    height: '90vh',
    backgroundColor: 'white',
    borderRadius: '12px',
    boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
    overflow: 'hidden',
  },
  header: {
    padding: '20px',
    borderBottom: '1px solid #e5e5e5',
    backgroundColor: '#fafafa',
  },
  title: {
    margin: 0,
    fontSize: '24px',
    fontWeight: '600',
    color: '#333',
  },
  subtitle: {
    margin: '4px 0 0 0',
    fontSize: '14px',
    color: '#666',
  },
  messagesContainer: {
    flex: 1,
    overflowY: 'auto',
    padding: '20px',
    display: 'flex',
    flexDirection: 'column',
    gap: '16px',
  },
  emptyState: {
    textAlign: 'center',
    color: '#999',
    marginTop: '40px',
  },
  message: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
  },
  userMessage: {
    alignItems: 'flex-end',
  },
  assistantMessage: {
    alignItems: 'flex-start',
  },
  messageLabel: {
    fontSize: '12px',
    fontWeight: '500',
    color: '#666',
  },
  messageContent: {
    padding: '12px 16px',
    borderRadius: '8px',
    maxWidth: '80%',
    wordBreak: 'break-word',
    backgroundColor: '#f0f0f0',
    lineHeight: '1.6',
  },
  inputArea: {
    display: 'flex',
    gap: '12px',
    padding: '20px',
    borderTop: '1px solid #e5e5e5',
    backgroundColor: '#fafafa',
  },
  textarea: {
    flex: 1,
    padding: '12px',
    border: '1px solid #ddd',
    borderRadius: '8px',
    fontSize: '14px',
    resize: 'none',
    minHeight: '60px',
    fontFamily: 'inherit',
  },
  button: {
    padding: '12px 24px',
    backgroundColor: '#0070f3',
    color: 'white',
    border: 'none',
    borderRadius: '8px',
    fontSize: '14px',
    fontWeight: '500',
    cursor: 'pointer',
    transition: 'background-color 0.2s',
  },
  buttonDisabled: {
    backgroundColor: '#ccc',
    cursor: 'not-allowed',
  },
  cursor: {
    animation: 'blink 1s infinite',
  },
};
