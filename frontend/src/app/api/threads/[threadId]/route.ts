import { NextRequest, NextResponse } from "next/server";
import { langgraphBaseUrl } from "@/lib/config";

function backend(path: string) {
  return `${langgraphBaseUrl}${path}`;
}

export async function GET(req: NextRequest, context: { params: Promise<{ threadId: string }> }) {
  const { threadId } = await context.params;
  const headers: Record<string, string> = {};
  const auth = req.headers.get("authorization");
  if (auth) {
    headers.Authorization = auth;
  }
  const res = await fetch(backend(`/threads/${threadId}`), {
    method: "GET",
    headers,
    cache: "no-store",
  });

  if (!res.ok) {
    return NextResponse.json({ error: "Failed to fetch thread" }, { status: res.status });
  }

  const thread = await res.json();
  return NextResponse.json({ thread });
}
