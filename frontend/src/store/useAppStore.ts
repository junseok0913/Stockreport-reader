import { create } from 'zustand';
import type { Message, ChunkInfo } from '../types';

interface AppState {
  // PDF state
  fileId: string | null;
  pdfUrl: string | null;
  filename: string | null;
  pages: number | null;
  currentPage: number;

  // Chunks state
  chunks: ChunkInfo[];
  pinnedChunks: string[];
  hasBBox: boolean;

  // Chat state
  messages: Message[];
  isStreaming: boolean;

  // Actions
  setPdfData: (fileId: string, pdfUrl: string, filename: string, pages: number | null) => void;
  setCurrentPage: (page: number) => void;
  setChunks: (chunks: ChunkInfo[]) => void;
  togglePinChunk: (chunkId: string) => void;
  clearPinnedChunks: () => void;
  addMessage: (message: Omit<Message, 'id' | 'timestamp'>) => void;
  updateMessage: (id: string, updates: Partial<Message>) => void;
  setIsStreaming: (isStreaming: boolean) => void;
  reset: () => void;
}

const initialState = {
  fileId: null,
  pdfUrl: null,
  filename: null,
  pages: null,
  currentPage: 1,
  chunks: [],
  pinnedChunks: [],
  hasBBox: false,
  messages: [],
  isStreaming: false,
};

export const useAppStore = create<AppState>((set) => ({
  ...initialState,

  setPdfData: (fileId, pdfUrl, filename, pages) =>
    set({
      fileId,
      pdfUrl,
      filename,
      pages,
      currentPage: 1,
    }),

  setCurrentPage: (page) => set({ currentPage: page }),

  setChunks: (chunks) =>
    set({
      chunks,
      hasBBox: chunks.length > 0,
    }),

  togglePinChunk: (chunkId) =>
    set((state) => ({
      pinnedChunks: state.pinnedChunks.includes(chunkId)
        ? state.pinnedChunks.filter((id) => id !== chunkId)
        : [...state.pinnedChunks, chunkId],
    })),

  clearPinnedChunks: () => set({ pinnedChunks: [] }),

  addMessage: (message) =>
    set((state) => ({
      messages: [
        ...state.messages,
        {
          ...message,
          id: crypto.randomUUID(),
          timestamp: new Date(),
        },
      ],
    })),

  updateMessage: (id, updates) =>
    set((state) => ({
      messages: state.messages.map((msg) => (msg.id === id ? { ...msg, ...updates } : msg)),
    })),

  setIsStreaming: (isStreaming) => set({ isStreaming }),

  reset: () => set(initialState),
})); 