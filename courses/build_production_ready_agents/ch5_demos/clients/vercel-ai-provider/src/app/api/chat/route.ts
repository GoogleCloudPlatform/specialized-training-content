import { streamText } from 'ai';
import { createBackendProvider } from '@/lib/backend-provider';

// Force edge runtime for proper streaming support
export const runtime = 'edge';

const API_BASE_URL = 'http://localhost:8000';

// Session storage (simple in-memory for this demo)
let sessionId: string | null = null;

export async function POST(req: Request) {
  const { messages, user_id } = await req.json();

  // Get last user message
  const lastMessage = messages[messages.length - 1];
  const userMessage = lastMessage?.content || '';

  // Create session if needed
  if (!sessionId) {
    const sessionResponse = await fetch(`${API_BASE_URL}/sessions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: user_id || 'web_user_001',
        initial_state: {},
      }),
    });
    const sessionData = await sessionResponse.json();
    sessionId = sessionData.session_id;
  }

  // Call the backend chat endpoint
  const response = await fetch(`${API_BASE_URL}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      user_id: user_id || 'web_user_001',
      session_id: sessionId,
      message: userMessage,
    }),
  });

  if (!response.ok || !response.body) {
    return new Response('Backend error', { status: 500 });
  }

  // Create readable stream that transforms backend SSE to useChat format
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  const encoder = new TextEncoder();
  let buffer = '';

  const stream = new ReadableStream({
    async start(controller) {
      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            if (!line.startsWith('data: ')) continue;

            try {
              const data = JSON.parse(line.substring(6));
              
              if (data.type === 'response_chunk' && data.text && !data.is_final) {
                // Send as text chunk in format useChat expects
                controller.enqueue(encoder.encode(`0:${JSON.stringify(data.text)}\n`));
              }
            } catch (e) {
              console.error('Parse error:', e);
            }
          }
        }
      } finally {
        reader.releaseLock();
        controller.close();
      }
    },
  });

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/plain; charset=utf-8',
      'X-Vercel-AI-Data-Stream': 'v1',
    },
  });
}
