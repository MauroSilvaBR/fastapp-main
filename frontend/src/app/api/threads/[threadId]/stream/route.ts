import { NextRequest, NextResponse } from "next/server";
import { langgraphAssistantId, langgraphBaseUrl } from "@/lib/config";

export const runtime = "nodejs";

function backend(path: string) {
  return `${langgraphBaseUrl}${path}`;
}

interface PostPayload {
  content: string;
  model: string;
  useTavily: boolean;
}

export async function POST(req: NextRequest, context: { params: Promise<{ threadId: string }> }) {
  const { threadId } = await context.params;
  const body = (await req.json()) as Partial<PostPayload>;

  if (!body?.content || !body.model) {
    return NextResponse.json({ error: "Missing content or model" }, { status: 400 });
  }

  const payload = {
    assistant_id: langgraphAssistantId,
    input: {
      messages: [
        {
          role: "system",
          content: JSON.stringify({ type: "settings", model: body.model, use_tavily: body.useTavily ?? false }),
        },
        {
          role: "user",
          content: body.content,
        },
      ],
    },
    config: {
      configurable: {
        model_name: body.model,
        use_tavily: body.useTavily ?? false,
      },
    },
  };

  const upstreamHeaders: Record<string, string> = { "Content-Type": "application/json" };
  const auth = req.headers.get("authorization");
  if (auth) {
    upstreamHeaders.Authorization = auth;
  }

  const res = await fetch(backend(`/threads/${threadId}/runs/stream`), {
    method: "POST",
    headers: upstreamHeaders,
    body: JSON.stringify(payload),
  });

  if (!res.ok || !res.body) {
    const error = await res.text();
    return NextResponse.json({ error: error || "Failed to start stream" }, { status: res.status });
  }

  const responseHeaders = new Headers();
  responseHeaders.set("Content-Type", res.headers.get("content-type") ?? "text/event-stream");
  responseHeaders.set("Cache-Control", "no-cache");
  responseHeaders.set("Connection", "keep-alive");

  return new Response(res.body, {
    status: res.status,
    headers: responseHeaders,
  });
}
