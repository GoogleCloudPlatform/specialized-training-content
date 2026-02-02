# Setup Instructions

## Install Dependencies

```bash
cd /Users/jeff/Desktop/Dev/atf-dev-jwd/build/ch5/vercel-ai-simple
npm install
```

## Run the Application

1. Make sure the backend server is running on port 8000:
   ```bash
   # In a separate terminal
   cd /Users/jeff/Desktop/Dev/atf-dev-jwd/build/ch5
   python sessions_server.py
   ```

2. Start the Next.js development server:
   ```bash
   npm run dev
   ```

3. Open your browser to http://localhost:3001

## Key Features

This implementation showcases the Vercel AI SDK approach:

- **`useChat` hook**: Manages chat state, streaming, and message handling
- **API Route**: Bridges the Vercel AI SDK with your custom backend
- **Streaming**: Native streaming support via `StreamingTextResponse`
- **Minimal code**: The SDK handles most of the complexity

## File Structure

```
vercel-ai-simple/
├── src/
│   └── app/
│       ├── api/
│       │   └── chat/
│       │       └── route.ts       # API endpoint adapter
│       ├── page.tsx               # Main chat UI
│       ├── layout.tsx             # App layout
│       └── globals.css            # Global styles
├── package.json
├── tsconfig.json
└── next.config.ts
```

## Comparison Points

When comparing with other implementations, note:

1. **State Management**: Automatic via `useChat` hook
2. **Streaming**: Built-in with `StreamingTextResponse`
3. **Code Size**: Minimal - most logic is in the SDK
4. **Flexibility**: Opinionated but extensible
5. **Framework**: Tightly integrated with Next.js/React
