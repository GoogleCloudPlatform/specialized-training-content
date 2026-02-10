"use client";

import type { ReactNode } from "react";
import { useState, useCallback } from "react";
import {
  AssistantRuntimeProvider,
  useLocalRuntime,
  type ChatModelAdapter,
} from "@assistant-ui/react";

const API_BASE_URL = "http://localhost:8000";
const USER_ID = "web_user_001";

// Custom adapter that connects to the existing ADK backend
const MyModelAdapter: ChatModelAdapter = {
  async *run({ messages, abortSignal }) {
    // Get or create session
    let sessionId = sessionStorage.getItem("adk_session_id");
    
    if (!sessionId) {
      const sessionResponse = await fetch(`${API_BASE_URL}/sessions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          user_id: USER_ID,
          initial_state: {},
        }),
      });
      const sessionData = await sessionResponse.json();
      sessionId = sessionData.session_id;
      sessionStorage.setItem("adk_session_id", sessionId);
    }

    // Get the last user message
    const lastMessage = messages[messages.length - 1];
    const userMessage = lastMessage?.content
      .filter((c) => c.type === "text")
      .map((c) => c.text)
      .join("\n");

    // Send message to backend with streaming
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({
        user_id: USER_ID,
        session_id: sessionId,
        message: userMessage,
      }),
      signal: abortSignal,
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    // Handle streaming response
    const reader = response.body?.getReader();
    if (!reader) throw new Error("No response body");

    const decoder = new TextDecoder();
    let buffer = "";
    let accumulatedText = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;

        const data = JSON.parse(line.substring(6));

        if (data.type === "response_chunk" && !data.is_final) {
          accumulatedText += data.text;
          yield {
            content: [
              {
                type: "text",
                text: accumulatedText,
              },
            ],
          };
        }
      }
    }
  },
};

export function MyRuntimeProvider({
  children,
}: Readonly<{
  children: ReactNode;
}>) {
  const runtime = useLocalRuntime(MyModelAdapter);

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      {children}
    </AssistantRuntimeProvider>
  );
}
