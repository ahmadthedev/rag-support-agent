export interface Source {
  file: string;
  score: number;
}

export interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
  error?: boolean;
}

export interface ChatResponse {
  session_id: string;
  answer: string;
  sources: Source[];
}