# Edhanta AI — Chat UI (Mock Only)

A ChatGPT-style educational chatbot UI. Frontend only, no backend or real AI calls.

## Scope
- Single-page chat experience at `/` (replace placeholder in `src/routes/index.tsx`)
- Mock assistant replies with a simulated "thinking" delay
- Each AI response shows textbook source citations
- Responsive: works on mobile and desktop

## Layout
```
┌────────────────────────────────────────┐
│        Edhanta AI  (centered header)   │  ← sticky top
├────────────────────────────────────────┤
│                                        │
│   [AI bubble]                          │
│      ↳ Sources: NCERT Physics Ch.4     │
│                          [User bubble] │
│   [AI typing… animated dots]           │
│                                        │
├────────────────────────────────────────┤
│  [ Ask Edhanta anything… ]  [ Send ]   │  ← fixed bottom composer
└────────────────────────────────────────┘
```

## Components (new files)
- `src/components/edhanta/ChatHeader.tsx` — centered logo + "Edhanta AI" title, subtle border-bottom
- `src/components/edhanta/MessageList.tsx` — scrollable conversation area, auto-scrolls to latest
- `src/components/edhanta/MessageBubble.tsx` — renders user vs assistant variants
- `src/components/edhanta/SourceList.tsx` — chip/badge row under AI messages ("NCERT Class 10 — Science, Ch. 6")
- `src/components/edhanta/TypingIndicator.tsx` — three-dot pulsing animation while "waiting"
- `src/components/edhanta/ChatComposer.tsx` — textarea + Send button, Enter to send, Shift+Enter newline
- `src/lib/edhanta-mock.ts` — mock reply generator + sample textbook sources, returns after ~1.2s delay

## Page wiring
- `src/routes/index.tsx`: replace placeholder. Holds `messages` state (`{id, role, content, sources?}[]`), `isLoading` flag. On submit: append user message → set loading → after timeout append mock AI message with 1–2 mock sources.
- Seed with one welcome assistant message: "Hi! I'm Edhanta AI. Ask me anything from your textbooks." with no sources.
- Update route `head()` meta: title "Edhanta AI — Your Study Companion", description, og tags.

## Styling / Design system
- Use existing semantic tokens in `src/styles.css` (no hardcoded colors).
- Add a few Edhanta-flavored tokens: `--brand` (warm indigo/teal — TBD, will pick a calm scholarly hue), `--chat-user`, `--chat-user-foreground`. Register in `@theme inline`.
- Assistant messages: no background, plain foreground text on page surface (per chat-ui guidance).
- User messages: filled bubble using `--chat-user` / `--chat-user-foreground` (high contrast).
- Source chips: `Badge` (shadcn) `variant="secondary"` with a small book icon (lucide `BookOpen`).
- Use shadcn `Button`, `Textarea`, `Badge`, `ScrollArea`.
- Subtle `animate-fade-in` on new messages; custom `@keyframes` for typing dots in `styles.css`.

## Responsiveness
- Container: `max-w-3xl mx-auto px-4` for messages and composer.
- Composer is `fixed bottom-0 inset-x-0` with a backdrop blur and top border; message list has bottom padding to clear it.
- Header sticky top with same blur treatment.
- Touch-friendly tap targets (min 44px) on mobile.

## Mock data shape
```ts
type Role = "user" | "assistant";
type Source = { title: string; chapter: string; page?: number };
type Message = { id: string; role: Role; content: string; sources?: Source[] };
```
`getMockReply(prompt)` returns a canned educational response plus 1–2 sources cycled from a small list (NCERT Physics, Biology, History, Math, etc.).

## Out of scope
- No backend, Lovable Cloud, auth, persistence, or real LLM calls.
- No multi-thread/conversation history sidebar (single thread only).
- No file uploads, voice input, or markdown rendering beyond plain text + line breaks.

## Files touched
- New: 6 components + 1 mock lib
- Edited: `src/routes/index.tsx`, `src/styles.css` (tokens + typing keyframes), `src/routes/__root.tsx` (only if title default needs adjusting — likely skip)
