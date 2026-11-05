import { NextRequest, NextResponse } from "next/server";
import { langgraphBaseUrl } from "@/lib/config";

function backend(path: string) {
  return `${langgraphBaseUrl}${path}`;
}

function authHeaders(req: NextRequest) {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  const auth = req.headers.get("authorization");
  if (auth) {
    headers.Authorization = auth;
  }
  return headers;
}

export async function GET(req: NextRequest) {
  const res = await fetch(backend("/threads/search"), {
    method: "POST",
    headers: authHeaders(req),
    body: JSON.stringify({ limit: 50 }),
    cache: "no-store",
  });

  if (!res.ok) {
    return NextResponse.json({ error: "Failed to load threads" }, { status: res.status });
  }

  const data = await res.json();
  return NextResponse.json({ threads: data });
}

export async function POST(req: NextRequest) {
  const res = await fetch(backend("/threads"), {
    method: "POST",
    headers: authHeaders(req),
    body: JSON.stringify({ metadata: {} }),
    cache: "no-store",
  });

  if (!res.ok) {
    return NextResponse.json({ error: "Failed to create thread" }, { status: res.status });
  }

  const thread = await res.json();
  return NextResponse.json({ thread });
}
