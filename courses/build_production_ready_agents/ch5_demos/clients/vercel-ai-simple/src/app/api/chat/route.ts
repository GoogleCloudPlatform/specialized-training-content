const API_BASE_URL = 'http://localhost:8000';

// Session storage (simple in-memory for this demo)
let sessionId: string | null = null;

export async function POST(req: Request) {
  const { messages, user_id } = await req.json();

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

  // Get the last user message
  const lastMessage = messages[messages.length - 1];

  // Call the backend chat endpoint
  const response = await fetch(`${API_BASE_URL}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      user_id: user_id || 'web_user_001',
      session_id: sessionId,
      message: lastMessage.content,
    }),
  });

  if (!response.ok || !response.body) {
    throw new Error('Failed to get response from backend');
  }

  // Create a transform stream to convert backend SSE to plain text stream
  const textStream = new ReadableStream({
    async start(controller) {
      const reader = response.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) {
            console.log('[Route] Stream complete');
            break;
          }

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            if (!line.startsWith('data: ')) continue;

            try {
              const data = JSON.parse(line.substring(6));
              console.log('[Route] Parsed chunk:', data);

              if (data.type === 'response_chunk' && !data.is_final) {
                console.log('[Route] Enqueuing text:', data.text);
                // Encode as data stream format for AI SDK
                controller.enqueue(
                  new TextEncoder().encode(`0:${JSON.stringify(data.text)}\n`)
                );
              }
            } catch (e) {
              console.error('[Route] Failed to parse chunk:', e);
            }
          }
        }
      } catch (error) {
        console.error('[Route] Stream error:', error);
        controller.error(error);
      } finally {
        reader.releaseLock();
        controller.close();
      }
    },
  });

  return new Response(textStream, {
    headers: {
      'Content-Type': 'text/plain; charset=utf-8',
      'X-Vercel-AI-Data-Stream': 'v1',
    },
  });
}
