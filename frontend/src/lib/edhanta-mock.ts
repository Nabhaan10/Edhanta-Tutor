export type Role = "user" | "assistant";
export type Source = { title: string; chapter: string; page?: number };
export type Message = {
  id: string;
  role: Role;
  content: string;
  sources?: Source[];
  /** Local object URL for an uploaded image (user messages only). */
  imageUrl?: string;
};

const SOURCE_POOL: Source[] = [
  { title: "NCERT Class 10 — Science", chapter: "Ch. 6: Life Processes", page: 95 },
  { title: "NCERT Class 9 — Physics", chapter: "Ch. 8: Motion", page: 102 },
  { title: "NCERT Class 11 — Biology", chapter: "Ch. 5: Morphology of Flowering Plants", page: 71 },
  { title: "NCERT Class 10 — Mathematics", chapter: "Ch. 4: Quadratic Equations", page: 70 },
  { title: "NCERT Class 8 — History", chapter: "Ch. 2: From Trade to Territory", page: 18 },
  { title: "NCERT Class 12 — Chemistry", chapter: "Ch. 3: Electrochemistry", page: 63 },
];

const REPLIES = [
  "Great question! Here's a clear breakdown:\n\nThe core idea is built on three pillars — observation, hypothesis, and verification. In your textbook, this is introduced with a simple everyday example and then formalized step by step.\n\nWould you like me to walk through a worked example next?",
  "Let's unpack this carefully.\n\nFirst, recall the definition. Then apply it to the standard example in your chapter. The trick most students miss is the second step — make sure the units are consistent before substituting values.\n\nTry the practice question at the end of the section and tell me what you get!",
  "Excellent topic to revise. The key insight is that the process is cyclic — each stage feeds into the next. Memorize the diagram, not just the words; the visual will help you recall it during exams.",
  "Here's a quick summary:\n\n• Concept: defined in the opening paragraph of the chapter.\n• Importance: explained through real-world examples.\n• Application: shown in the solved problems.\n\nLet me know if you'd like a deeper dive into any one of these.",
];

let seed = 0;

export function getMockReply(prompt: string): Promise<{ content: string; sources: Source[] }> {
  return new Promise((resolve) => {
    const delay = 900 + Math.random() * 800;
    setTimeout(() => {
      const content = REPLIES[seed % REPLIES.length];
      const s1 = SOURCE_POOL[seed % SOURCE_POOL.length];
      const s2 = SOURCE_POOL[(seed + 2) % SOURCE_POOL.length];
      seed += 1;
      void prompt;
      resolve({ content, sources: [s1, s2] });
    }, delay);
  });
}

export function uid() {
  return Math.random().toString(36).slice(2, 11);
}
