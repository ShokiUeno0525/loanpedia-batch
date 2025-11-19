import { create } from 'zustand';

type State = { count: number };
type Actions = { increment: () => void; reset: () => void };

export const useCounterStore = create<State & Actions>((set) => ({
  count: 0,
  increment: () => set((s) => ({ count: s.count + 1 })),
  reset: () => set({ count: 0 }),
}));

