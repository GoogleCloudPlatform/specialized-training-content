"use client";

import { Thread } from "@assistant-ui/react";
import { MyRuntimeProvider } from "@/components/MyRuntimeProvider";

export default function Home() {
  return (
    <MyRuntimeProvider>
      <div className="h-screen flex flex-col bg-white">
        <header className="px-10 py-6 border-b border-gray-200">
          <h1 className="text-3xl font-light text-gray-900">
            ADK Agent Client
          </h1>
        </header>
        <div className="flex-1 overflow-hidden">
          <Thread />
        </div>
      </div>
    </MyRuntimeProvider>
  );
}
