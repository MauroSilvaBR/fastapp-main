import { NextRequest, NextResponse } from "next/server";
import { langgraphAssistantId, langgraphBaseUrl } from "@/lib/config";

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

  const headers: Record<string, string> = { "Content-Type": "application/json" };
  const auth = req.headers.get("authorization");
  if (auth) {
    headers.Authorization = auth;
  }

  const res = await fetch(backend(`/threads/${threadId}/runs/wait`), {
    method: "POST",
    headers,
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const error = await res.text();
    return NextResponse.json({ error: error || "Failed to send message" }, { status: res.status });
  }

  const data = (await res.json()) as unknown;

  type RunWaitResult = { messages: unknown[] };
  type FastApiEnvelope = { result: RunWaitResult };

  const hasResult = (value: unknown): value is FastApiEnvelope =>
    typeof value === "object" && value !== null && "result" in value;

  const normalized: RunWaitResult = hasResult(data) ? data.result : (data as RunWaitResult);
  return NextResponse.json({ result: normalized });
}
