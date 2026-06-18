"use client";

import { makeMarkdownText } from "@assistant-ui/react-markdown";
import remarkGfm from "remark-gfm";

// Renders assistant message text as formatted markdown (headings, lists,
// bold/italic, code, tables via remark-gfm) instead of raw text.
export const MarkdownText = makeMarkdownText({
  remarkPlugins: [remarkGfm],
});
