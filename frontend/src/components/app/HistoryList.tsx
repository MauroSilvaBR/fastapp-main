"use client";

import { useMemo } from "react";
import { useRouter } from "next/navigation";
import { useGenesisUI } from "@/state/useGenesisUI";
import { Card, CardContent, CardHeader } from "@/components/ui/card";

export function HistoryList() {
  const router = useRouter();
  const { isLoading, sessions, messagesBySession, selectSession } = useGenesisUI();

  const items = useMemo(
    () =>
      sessions.map((session) => ({
        ...session,
        messageCount: messagesBySession[session.id]?.length ?? 0,
        lastMessage: messagesBySession[session.id]?.slice(-1)[0]?.content ?? "",
      })),
    [sessions, messagesBySession],
  );

  return (
    <div className="flex min-h-screen flex-1 flex-col bg-gradient-to-br from-[#05080f] via-[#0b1428] to-[#080d18] px-4 py-8 text-[#dfdecf] sm:px-6 lg:px-10 lg:py-12">
      <header className="mb-8 lg:mb-10">
        <div className="text-[11px] uppercase tracking-[0.4em] text-[#05adca]/70">Registro de Operações</div>
        <h1
          className="text-3xl font-bold uppercase text-white"
          style={{ fontFamily: "var(--font-condensed)" }}
        >
          Threads Recentes
        </h1>
        <p className="mt-2 max-w-xl text-sm text-[#7f8baf]">
          Histórico usando checkpointer Postgres  
        </p>
      </header>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {isLoading ? (
          <Card className="border border-white/12 bg-white/5 text-[#9ba3c0]">
            <CardHeader>Carregando histórico…</CardHeader>
            <CardContent>Aguarde enquanto carregamos os registros do LangGraph.</CardContent>
          </Card>
        ) : (
          items.map((item) => (
            <Card
              key={item.id}
              className="group cursor-pointer border border-white/15 bg-[rgba(9,14,26,0.9)] transition-all hover:border-[#1086ad]/50 hover:bg-[#1086ad]/5 hover:shadow-[0_35px_80px_rgba(0,0,0,0.55)]"
              onClick={() => {
                selectSession(item.id)
                  .catch(console.error)
                  .finally(() => router.push("/"));
              }}
            >
              <CardHeader>
                <div
                  className="text-xl font-semibold uppercase text-white"
                  style={{ fontFamily: "var(--font-condensed)" }}
                >
                  {item.title}
                </div>
              </CardHeader>
              <CardContent className="space-y-4 text-sm text-[#9ba3c0]">
                <div className="line-clamp-4 text-white/90">
                  {item.lastMessage || "Sem mensagens ainda."}
                </div>
                <div className="space-y-1 text-[10px] uppercase tracking-[0.35em] text-[#7f8baf]">
                  <div>{item.messageCount} mensagens</div>
                  <div>{new Date(item.createdAt).toLocaleString("pt-BR")}</div>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>

      {items.length === 0 && !isLoading ? (
        <div className="mt-12 rounded-3xl border border-dashed border-white/12 bg-white/5 p-12 text-center text-[#7f8baf]">
          Threads aparecerão aqui conforme você interagir com o agente.
        </div>
      ) : null}
    </div>
  );
}
