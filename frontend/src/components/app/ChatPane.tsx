"use client";

import Link from "next/link";
import Image from "next/image";
import { FormEvent, useMemo, useState, useEffect, useRef, useCallback } from "react";
import clsx from "clsx";
import { useGenesisUI } from "@/state/useGenesisUI";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useAuth } from "@/state/useAuth";
import { Alert } from "@/components/ui/alert";


export function ChatPane() {
  const { isLoading, isSending, currentSessionId, messagesBySession, sendMessage, createSession } = useGenesisUI();
  const { token, isReady: authReady, isLoggingIn, loginError, login } = useAuth();
  const messages = useMemo(
    () => (currentSessionId ? messagesBySession[currentSessionId] ?? [] : []),
    [messagesBySession, currentSessionId],
  );
  const hasActiveSession = Boolean(currentSessionId);
  const sessionLabel = currentSessionId ? currentSessionId.slice(0, 12) : "Selecione uma thread";
  const [draft, setDraft] = useState("");
  const [passkeyInput, setPasskeyInput] = useState("");
  const [localLoginError, setLocalLoginError] = useState<string | null>(null);

  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const mainRef = useRef<HTMLElement>(null);
  const [userHasScrolled, setUserHasScrolled] = useState(false);
  const lastMessageCountRef = useRef(0);

  const handleSubmit = useCallback(async (event?: FormEvent<HTMLFormElement>) => {
    event?.preventDefault();
    const trimmed = draft.trim();
    if (!trimmed || isLoading || isSending || !token || !hasActiveSession) return;

    // Limpa o draft imediatamente para feedback visual
    setDraft("");

    // Reseta o controle de scroll ao enviar mensagem
    setUserHasScrolled(false);

    try {
      await sendMessage(trimmed);
    } catch (error) {
      // Se houver erro, restaura o draft
      setDraft(trimmed);
      console.error("Erro ao enviar mensagem:", error);
    }
  }, [draft, hasActiveSession, isLoading, isSending, token, sendMessage]);

  const handleCreateSession = useCallback(() => {
    if (isLoading || isSending) return;
    createSession().catch(console.error);
  }, [createSession, isLoading, isSending]);

  async function handleLoginSubmit(event?: FormEvent<HTMLFormElement>) {
    event?.preventDefault();
    const trimmed = passkeyInput.trim();
    if (!trimmed) {
      setLocalLoginError("Informe a passkey para continuar.");
      return;
    }
    setLocalLoginError(null);
    try {
      await login(trimmed);
      setPasskeyInput("");
    } catch (error) {
      const message = error instanceof Error ? error.message : "Falha ao autenticar";
      setLocalLoginError(message);
    }
  }

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
        event.preventDefault();
        handleSubmit();
      }
    }

    const textarea = textareaRef.current;
    if (textarea) {
      textarea.addEventListener("keydown", handleKeyDown);
      return () => textarea.removeEventListener("keydown", handleKeyDown);
    }
  }, [handleSubmit]);

  // Detecta qualquer interação de scroll do usuário
  useEffect(() => {
    const mainElement = mainRef.current;
    if (!mainElement) return;

    function handleUserScroll(event: Event) {
      const target = event.target as HTMLElement;
      if (!target) return;
      
      // Verifica se o usuário está scrollando para cima
      const { scrollTop, scrollHeight, clientHeight } = target;
      const isNearBottom = scrollHeight - scrollTop - clientHeight < 100;
      
      // Se não está perto do fim, marca que o usuário scrollou
      if (!isNearBottom) {
        setUserHasScrolled(true);
      }
    }

    // Detecta scroll via roda do mouse, touch, ou barra de rolagem
    mainElement.addEventListener('scroll', handleUserScroll, { passive: true });
    mainElement.addEventListener('wheel', handleUserScroll, { passive: true });
    mainElement.addEventListener('touchmove', handleUserScroll, { passive: true });
    
    return () => {
      mainElement.removeEventListener('scroll', handleUserScroll);
      mainElement.removeEventListener('wheel', handleUserScroll);
      mainElement.removeEventListener('touchmove', handleUserScroll);
    };
  }, []);

  // Auto-scroll quando novas mensagens chegam
  useEffect(() => {
    const hasNewMessages = messages.length > lastMessageCountRef.current;
    lastMessageCountRef.current = messages.length;
    
    // Faz scroll se: não scrollou manualmente OU se há novas mensagens
    if (!userHasScrolled || hasNewMessages) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, userHasScrolled]);

  // Reseta o controle quando troca de sessão
  useEffect(() => {
    setUserHasScrolled(false);
    lastMessageCountRef.current = 0;
  }, [currentSessionId]);

  if (!authReady) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-[#080d18] via-[#0c1324] to-[#05080f] px-4">
        <p className="text-xs uppercase tracking-[0.45em] text-[#7f8baf]">Sincronizando credenciais…</p>
      </div>
    );
  }

  if (!token) {
    const authMessage = localLoginError || loginError;
    return (
      <div className="relative min-h-screen overflow-hidden bg-gradient-to-br from-[#05080f] via-[#0b1324] to-[#111a2d] px-4 py-10 sm:px-6 lg:px-10">
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_15%_10%,rgba(32,51,109,0.22),transparent_55%)]" />
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_80%_8%,rgba(16,134,173,0.2),transparent_50%)]" />
        <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(120deg,rgba(255,255,255,0.05),transparent)]" />

        <div className="relative mx-auto flex max-w-4xl flex-col items-center gap-8 text-center">
          <div className="flex flex-col items-center gap-4">
            <div className="flex items-center justify-center rounded-3xl bg-black/40 p-4 shadow-[0_20px_60px_rgba(16,134,173,0.35)] ring-1 ring-white/10">
              <Image
                src="/hawk_azul192.png"
                alt="Hawk"
                width={140}
                height={140}
                priority
                className="h-28 w-28 drop-shadow-[0_20px_60px_rgba(16,134,173,0.45)]"
                style={{ objectFit: "contain" }}
              />
            </div>
            <div className="space-y-2">
              <h1
                className="text-4xl font-black uppercase leading-tight text-white sm:text-5xl"
                style={{ fontFamily: "var(--font-condensed)" }}
              >
                Construa Sistemas de IA
              </h1>
            </div>
          </div>

          <section className="w-full max-w-xl text-left">
            <div className="rounded-[32px] border border-white/15 bg-gradient-to-br from-[#090f1c]/95 via-[#101a32]/95 to-[#05080f]/95 p-6 text-[#dfdecf] shadow-[0_40px_100px_rgba(0,0,0,0.75)] ring-1 ring-white/10 sm:p-8">
              <div className="flex items-center justify-between">
                <p className="text-[11px] uppercase tracking-[0.5em] text-[#05adca]/70">Acesso restrito</p>
                <span className="inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/5 px-3 py-1 text-[11px] uppercase tracking-[0.35em] text-[#9ba3c0]">
                  <span className="h-2 w-2 rounded-full bg-[#58d38f]" aria-hidden />
                  <Link
                    href="https://www.rhawk.pro/comunidade"
                    target="_blank"
                    rel="noreferrer"
                    className="transition hover:text-white"
                  >
                    Top Hawks
                  </Link>
                </span>
              </div>
              <h2
                className="mt-3 text-3xl font-bold uppercase text-white sm:text-4xl"
                style={{ fontFamily: "var(--font-condensed)" }}
              >
                Autenticação Requerida
              </h2>
              <p className="mt-3 text-sm text-[#9ba3c0]">
                Insira o passkey gerada. Ao liberar, você cai direto no console em tempo real.
              </p>
              <form onSubmit={handleLoginSubmit} className="mt-6 space-y-4 sm:mt-8">
                <label className="block text-[11px] uppercase tracking-[0.3em] text-[#7f8baf]">
                  Código secreto
                </label>
                <input
                  type="password"
                  value={passkeyInput}
                  onChange={(event) => setPasskeyInput(event.target.value)}
                  placeholder="********"
                  className="w-full rounded-2xl border border-white/15 bg-[#050b16] px-4 py-3 text-sm text-white placeholder:text-[#5f6785] focus:border-[#1086ad] focus:outline-none focus:ring-1 focus:ring-[#1086ad]"
                />
                {authMessage ? (
                  <Alert variant="error" className="mt-3">
                    <span className="text-sm">{authMessage}</span>
                  </Alert>
                ) : null}
                <Button
                  type="submit"
                  disabled={isLoggingIn || !passkeyInput.trim()}
                  className="w-full justify-center py-4 text-sm"
                >
                  {isLoggingIn ? "Validando..." : "Liberar console"}
                </Button>
              </form>
              <div className="mt-5 rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-xs text-[#9ba3c0]">
                <p className="text-[11px] uppercase tracking-[0.35em] text-[#7f8baf]">Features</p>
                <p className="mt-2">
                  Agente Langchain 1.0 multi modelo, busca web, sumarização e threads persistentes em banco privado. Customização e observabilidade, agora pronto para você operar.
                </p>
              </div>
            </div>
          </section>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-1 flex-col bg-gradient-to-br from-[#05080f] via-[#0a1426] to-[#080d18]">
      <header className="flex flex-col gap-2 border-b border-white/5 bg-[#090f1c]/85 px-4 py-4 text-[#dfdecf] shadow-[0_20px_60px_rgba(0,0,0,0.65)] backdrop-blur-2xl sm:px-6 sm:py-5 lg:h-24 lg:flex-row lg:items-center lg:justify-between lg:px-10">
        <div className="space-y-1">
          <div className="text-[11px] uppercase tracking-[0.4em] text-[#05adca]/75">Painel de Controle</div>
          <div className="text-2xl font-bold uppercase text-white sm:text-3xl" style={{ fontFamily: "var(--font-condensed)" }}>
            Sessão {sessionLabel}
          </div>
        </div>
        <div className="text-[11px] uppercase tracking-[0.35em] text-[#7f8baf]">
          {hasActiveSession ? `${messages.length} mensagens registradas` : "Selecione uma thread"}
        </div>
      </header>

      <main
        ref={mainRef}
        className="relative flex flex-1 flex-col gap-5 overflow-y-auto px-4 py-6 text-[#dfdecf] sm:px-6 lg:px-10"
      >
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_20%_15%,rgba(32,51,109,0.22),transparent_60%)]" />
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_80%_0%,rgba(242,101,49,0.12),transparent_55%)]" />
        <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(120deg,rgba(255,255,255,0.04),transparent)]" />
        <div className="relative flex-1 space-y-4">
          {!hasActiveSession ? (
            <div className="flex h-full items-center justify-center">
              <Card className="w-full max-w-3xl border border-white/15 bg-[rgba(9,14,26,0.92)] text-white shadow-[0_45px_120px_rgba(0,0,0,0.65)]">
                <CardHeader className="text-center">
                  <p className="text-[11px] uppercase tracking-[0.4em] text-[#05adca]/70">Seleção de Thread</p>
                  <h2 className="text-3xl font-bold uppercase" style={{ fontFamily: "var(--font-condensed)" }}>
                    Inicie uma missão
                  </h2>
                </CardHeader>
                <CardContent>
                  <div className="grid gap-4 sm:grid-cols-2">
                    <button
                      type="button"
                      onClick={handleCreateSession}
                      disabled={isLoading}
                      className={clsx(
                        "flex h-44 flex-col justify-between rounded-3xl border px-5 py-4 text-left transition-all",
                        "border-[#1086ad]/70 bg-[#1086ad]/12 text-white shadow-[0_30px_70px_rgba(6,12,24,0.65)] disabled:opacity-50",
                      )}
                    >
                      <span className="text-xl font-semibold uppercase" style={{ fontFamily: "var(--font-condensed)" }}>
                        Nova Thread
                      </span>
                      <span className="text-xs uppercase tracking-[0.35em] text-[#f5c7b4]">Criar missão rápida</span>
                    </button>
                    <Link
                      href="/history"
                      className="flex h-44 flex-col justify-between rounded-3xl border border-white/15 px-5 py-4 text-left text-[#dfdecf] transition hover:border-white/40 hover:bg-white/5"
                    >
                      <span className="text-xl font-semibold uppercase" style={{ fontFamily: "var(--font-condensed)" }}>
                        Pesquisar Thread
                      </span>
                      <span className="text-xs uppercase tracking-[0.35em] text-[#7f8baf]">Localize sessões passadas</span>
                    </Link>
                  </div>
                </CardContent>
              </Card>
            </div>
          ) : isLoading ? (
            <Card className="border border-white/12 bg-white/5 text-center text-[#9ba3c0]">
              <CardHeader>Carregando sessões</CardHeader>
              <CardContent>Aguarde enquanto conectamos ao LangGraph.</CardContent>
            </Card>
          ) : messages.length === 0 ? (
            <Card className="border border-dashed border-white/15 bg-transparent text-center text-[#7f8baf]">
              <CardContent>Envie um comando para iniciar a missão.</CardContent>
            </Card>
          ) : (
            messages.map((message) => {
              const isAssistant = message.role === "assistant";
              const isThinking = message.content === "Pensando...";
              return (
                <article
                  key={message.id}
                  className={clsx(
                    "w-full max-w-full rounded-[28px] border px-5 py-5 text-sm leading-relaxed shadow-[0_25px_70px_rgba(0,0,0,0.55)] transition-all sm:px-6 md:max-w-3xl",
                    isAssistant
                      ? "border-white/10 bg-gradient-to-br from-[#111a2d]/90 to-[#0a0f1d]/90 text-[#f6f7fb]"
                      : "border-[#1086ad]/60 bg-[#1086ad]/12 text-[#ecf6ff] ring-1 ring-[#1086ad]/30 sm:ml-auto",
                  )}
                >
                  <div className="mb-2 flex items-center justify-between text-[10px] uppercase tracking-[0.35em] text-[#7f8baf]">
                    <span>{message.role === "assistant" ? "Agente Hawk" : "Operador"}</span>
                    <span className="text-[#5c6383]">{new Date(message.timestamp).toLocaleTimeString()}</span>
                  </div>
                  {isAssistant ? (
                    isThinking ? (
                      <div className="flex items-center gap-2 italic text-[#9ba3c0]">
                        <span className="animate-pulse">Pensando...</span>
                      </div>
                    ) : (
                      <div className="markdown-body">
                        <ReactMarkdown
                          remarkPlugins={[remarkGfm]}
                          components={{
                            a: ({ ...props }) => (
                              <a
                                {...props}
                                className="font-semibold text-[#05adca] underline decoration-[#05adca]/60 underline-offset-4 hover:text-white"
                                target="_blank"
                                rel="noreferrer"
                              />
                            ),
                            code: ({ className, children, ...props }) => {
                              const isInline = !className?.includes('language-');
                              return isInline ? (
                                <code
                                  className={clsx(
                                    "rounded bg-[#1a2236] px-1.5 py-0.5 text-[13px] text-[#f6f7fb]",
                                    className,
                                  )}
                                  {...props}
                                >
                                  {children}
                                </code>
                              ) : (
                                <pre
                                  className="overflow-x-auto rounded-2xl border border-white/10 bg-[#050912] p-4 text-[13px] text-[#dfdecf]"
                                >
                                  <code className={className} {...props}>{children}</code>
                                </pre>
                              );
                            },
                            li: ({ ...props }) => <li className="pl-1" {...props} />,
                          }}
                        >
                          {message.content}
                        </ReactMarkdown>
                      </div>
                    )
                  ) : (
                    <p
                      className="whitespace-pre-wrap break-words text-[15px] text-[#e6f4ff]"
                      style={{ fontFamily: "var(--font-sans)" }}
                    >
                      {message.content}
                    </p>
                  )}
                <div className="mt-3 flex flex-wrap gap-3 text-[10px] uppercase tracking-[0.35em] text-[#7f8baf]">
                  {message.modelId ? <span>Modelo: {message.modelId}</span> : null}
                  {message.usedTavily ? <span>Busca Web Ativada</span> : null}
                </div>
              </article>
              );
            })
          )}
          <div ref={messagesEndRef} />
        </div>
      </main>

      {hasActiveSession ? (
        <footer className="border-t border-white/5 bg-[#090f1c]/80 px-4 py-5 backdrop-blur-2xl sm:px-6 lg:px-10">
          <form onSubmit={handleSubmit} className="flex w-full flex-col gap-3 sm:flex-row sm:items-end sm:gap-4">
            <div className="flex-1">
              <label className="mb-2 block text-[11px] uppercase tracking-[0.35em] text-[#7f8baf]">
                Entrada de Comando
              </label>
              <textarea
                ref={textareaRef}
                value={draft}
                onChange={(event) => setDraft(event.target.value)}
                placeholder={isLoading ? "Carregando..." : "Descreva o próximo passo da missão"}
                className="h-28 w-full resize-none rounded-2xl border border-white/15 bg-gradient-to-br from-[#070b14] to-[#111b33] px-5 py-4 text-sm text-white placeholder:text-[#5c6383] shadow-[0_35px_80px_rgba(0,0,0,0.55)] focus:border-[#1086ad] focus:outline-none focus:ring-2 focus:ring-[#1086ad]/70 sm:h-32 lg:h-[110px]"
                disabled={isLoading}
              />
            </div>
            <div className="flex w-full items-end sm:w-auto sm:pt-[30px]">
              <Button
                type="submit"
                disabled={isLoading || isSending || !draft.trim()}
                className="h-12 w-full px-6 text-[11px] sm:h-[110px] sm:w-auto sm:px-10"
              >
                Enviar
              </Button>
            </div>
          </form>
          <div className="mt-3 text-[11px] uppercase tracking-[0.3em] text-[#7f8baf]">
            Sessão atual: <span className="text-white">{sessionLabel}</span>
          </div>
        </footer>
      ) : null}
    </div>
  );
}
