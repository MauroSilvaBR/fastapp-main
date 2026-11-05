const DEFAULT_LANGGRAPH_BASE = "http://127.0.0.1:2024";
const DEFAULT_ASSISTANT_ID = "agent";

export const langgraphBaseUrl = process.env.LANGGRAPH_API_BASE ?? DEFAULT_LANGGRAPH_BASE;
export const langgraphAssistantId = process.env.LANGGRAPH_ASSISTANT_ID ?? DEFAULT_ASSISTANT_ID;
