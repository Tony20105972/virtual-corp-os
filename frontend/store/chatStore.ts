import { create } from "zustand"

export interface ChatMessage {
  id:      string
  agent:   string
  level:   "info" | "success" | "warn" | "error"
  message: string
}

interface ChatStore {
  messages:   ChatMessage[]
  addMessage: (msg: Omit<ChatMessage, "id">) => void
  clear:      () => void
}

export const useChatStore = create<ChatStore>((set) => ({
  messages: [],

  addMessage: (msg) =>
    set((s) => ({
      messages: [
        ...s.messages,
        { ...msg, id: `${Date.now()}-${Math.random()}` },
      ],
    })),

  clear: () => set({ messages: [] }),
}))
