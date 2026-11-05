"use client";

import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { createPortal } from "react-dom";
import clsx from "clsx";
import { useGenesisUI } from "@/state/useGenesisUI";
import { useAuth } from "@/state/useAuth";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";

interface TopBarProps {
  onToggleSidebar?: () => void;
}

export function TopBar({ onToggleSidebar }: TopBarProps) {
  const pathname = usePathname();
  const {
    models,
    selectedModelId,
    setSelectedModelId,
    useTavily,
    setUseTavily,
  } = useGenesisUI();
  const { logout, token } = useAuth();
  const [isMounted, setIsMounted] = useState(false);
  const [isModelPanelOpen, setIsModelPanelOpen] = useState(false);
  const hasAccess = Boolean(token);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  const selectedModel = useMemo(
    () => models.find((model) => model.id === selectedModelId),
    [models, selectedModelId],
  );

  return (
    <>
      <header className="sticky top-0 z-30 flex flex-col gap-3 border-b border-white/10 bg-[rgba(9,14,26,0.9)] px-4 py-3 text-[#dfdecf] shadow-[0_25px_80px_rgba(0,0,0,0.45)] backdrop-blur-2xl sm:px-6 md:flex-row md:items-center md:justify-between md:px-8">
        <div className="flex items-center gap-3 md:items-center">
          <button
            type="button"
            onClick={onToggleSidebar}
            className="inline-flex h-11 w-11 items-center justify-center rounded-2xl border border-white/20 bg-white/5 text-white transition hover:border-[#1086ad] hover:bg-[#1086ad]/15 lg:hidden"
            aria-label="Abrir menu"
          >
            <span className="flex flex-col gap-1.5">
              <span className="block h-0.5 w-5 bg-white" />
              <span className="block h-0.5 w-5 bg-white" />
              <span className="block h-0.5 w-5 bg-white" />
            </span>
          </button>
          <div>
            <p className="text-[10px] uppercase tracking-[0.35em] text-[#05adca]/70">Fábrica de Agentes</p>
            <p
              className="text-xl font-black uppercase text-white sm:text-2xl"
              style={{ fontFamily: "var(--font-condensed)" }}
            >
              Top Hawks
            </p>
          </div>
          <nav className="hidden items-center gap-2 text-[12px] uppercase tracking-[0.25em] md:flex">
            <Link
              href="/"
              className={clsx(
                "rounded-full border px-3 py-2 transition sm:px-4",
                pathname === "/"
                  ? "border-white/60 bg-white/10 text-white"
                  : "border-transparent text-[#9ba3c0] hover:border-white/20 hover:bg-white/5",
              )}
            >
              Console
            </Link>
            <Link
              href="/history"
              className={clsx(
                "rounded-full border px-3 py-2 transition sm:px-4",
                pathname === "/history"
                  ? "border-white/60 bg-white/10 text-white"
                  : "border-transparent text-[#9ba3c0] hover:border-white/20 hover:bg-white/5",
              )}
            >
              Histórico
            </Link>
          </nav>
        </div>
        <div className="flex w-full flex-col items-stretch gap-3 sm:w-auto sm:flex-row sm:items-center sm:justify-end sm:gap-4">
          {hasAccess ? (
            <>
              <button
                type="button"
                onClick={() => setIsModelPanelOpen(true)}
                className="flex items-center gap-3 rounded-full border border-white/20 bg-white/5 px-3 py-2 text-left transition hover:border-[#1086ad] hover:bg-[#1086ad]/15"
              >
                <span className="inline-flex h-11 w-11 items-center justify-center rounded-full border border-white/30 bg-transparent">
                  <Image src="/hawk_azul192.png" alt="Selecionar modelo" width={36} height={36} className="rounded-full" />
                </span>
                <div className="min-w-[160px]">
                  <p className="text-[10px] uppercase tracking-[0.4em] text-[#7f8baf]">Modelo ativo</p>
                  <p className="text-sm font-semibold text-white" style={{ fontFamily: "var(--font-condensed)" }}>
                    {selectedModel?.label ?? selectedModelId ?? "Selecionar"}
                  </p>
                </div>
              </button>
              <Switch
                checked={useTavily}
                label={useTavily ? "Busca Web ativa" : "Busca Web inativa"}
                onClick={() => setUseTavily(!useTavily)}
                className="text-[12px]"
              />
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={logout}
                className="border border-white/20 text-[10px] uppercase tracking-[0.4em]"
              >
                Sair
              </Button>
            </>
          ) : (
            <div className="flex justify-start text-[11px] uppercase tracking-[0.35em] text-[#7f8baf] sm:justify-end">
              Aguardando autenticação
            </div>
          )}
        </div>
      </header>
      {isMounted && isModelPanelOpen
        ? createPortal(
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-[rgba(4,6,12,0.92)] px-6 py-10 backdrop-blur-2xl">
              <div className="relative w-full max-w-4xl rounded-[32px] border border-white/15 bg-gradient-to-br from-[#090f1c]/95 via-[#0e1525]/95 to-[#05080f]/95 p-8 text-[#dfdecf] shadow-[0_40px_90px_rgba(0,0,0,0.75)] ring-1 ring-white/10">
                <div className="mb-6 flex items-center justify-between">
                  <div>
                    <p className="text-[11px] uppercase tracking-[0.4em] text-[#05adca]/70">Seleção de Modelo</p>
                    <h2 className="text-3xl font-black uppercase" style={{ fontFamily: "var(--font-condensed)" }}>
                      Ajuste tático
                    </h2>
                  </div>
                  <button
                    type="button"
                    onClick={() => setIsModelPanelOpen(false)}
                    className="rounded-full border border-white/20 px-4 py-2 text-sm uppercase tracking-[0.35em] text-[#dfdecf] hover:border-[#1086ad]"
                  >
                    Fechar
                  </button>
                </div>
                <div className="grid gap-4 sm:grid-cols-2">
                  {models.map((model) => {
                    const active = model.id === selectedModelId;
                    return (
                      <button
                        key={model.id}
                        onClick={() => {
                          setSelectedModelId(model.id);
                          setIsModelPanelOpen(false);
                        }}
                        className={clsx(
                          "flex flex-col gap-2 rounded-2xl border px-4 py-5 text-left transition-all",
                          active
                            ? "border-[#1086ad]/70 bg-[#1086ad]/12 text-white shadow-[0_30px_60px_rgba(6,12,24,0.65)]"
                            : "border-white/10 bg-white/5 text-[#dfdecf] hover:border-[#1086ad]/50 hover:bg-white/10",
                        )}
                      >
                        <span className="text-lg font-semibold uppercase" style={{ fontFamily: "var(--font-condensed)" }}>
                          {model.label}
                        </span>
                        <span className="text-xs text-[#9ba3c0]">{model.id}</span>
                        <div className="text-[11px] uppercase tracking-[0.35em] text-[#7f8baf]">
                          Custo in/out ${model.inputCost.toFixed(2)} / ${model.outputCost.toFixed(2)}
                        </div>
                        {active ? (
                          <span className="rounded-full border border-[#1086ad] px-3 py-1 text-center text-[10px] uppercase tracking-[0.4em] text-white">
                            Em uso
                          </span>
                        ) : null}
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>,
            document.body,
          )
        : null}
    </>
  );
}
