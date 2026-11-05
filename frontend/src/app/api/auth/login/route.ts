import { NextRequest, NextResponse } from "next/server";
import { langgraphBaseUrl } from "@/lib/config";

function backend(path: string) {
  return `${langgraphBaseUrl}${path}`;
}

export async function POST(req: NextRequest) {
  const body = await req.json();
  const res = await fetch(backend("/auth/login"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const detail = await res.text();
    return NextResponse.json({ error: detail || "Falha no login" }, { status: res.status });
  }

  const data = await res.json();
  return NextResponse.json(data);
}
