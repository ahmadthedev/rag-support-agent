import { useEffect, useRef, useState } from "react";
import type { KeyboardEvent } from "react";
import ReactMarkdown from "react-markdown";
import { resetSession, sendMessage } from "./api";
import type { Message } from "./types";
import "./App.css";

// Edit these to match your actual knowledge base
const SUGGESTIONS = [
  "What is this knowledge base about?",
  "How do I get started?",
  "Summarize the README",
];

export default function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const sessionId = useRef<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function send(text: string) {
    const content = text.trim();
    if (!content || loading) return;

    setMessages((m) => [...m, { role: "user", content }]);
    setInput("");
    setLoading(true);

    try {
      const res = await sendMessage(content, sessionId.current);
      sessionId.current = res.session_id;
      setMessages((m) => [
        ...m,
        { role: "assistant", content: res.answer, sources: res.sources },
      ]);
    } catch (e) {
      setMessages((m) => [
        ...m,
        {
          role: "assistant",
          content: e instanceof Error ? e.message : "Something went wrong.",
          error: true,
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  async function newChat() {
    if (sessionId.current) await resetSession(sessionId.current);
    sessionId.current = null;
    setMessages([]);
  }

  function onKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send(input);
    }
  }

  return (
    <div className="app">
      <header className="header">
        <div>
          <h1>Support Assistant</h1>
          <p>Answers from our knowledge base</p>
        </div>
        <button className="ghost" onClick={newChat}>
          New chat
        </button>
      </header>

      <main className="messages">
        {messages.length === 0 && (
          <div className="empty">
            <h2>How can we help?</h2>
            <div className="suggestions">
              {SUGGESTIONS.map((s) => (
                <button key={s} onClick={() => send(s)}>
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m, i) => (
          <div key={i} className={`row ${m.role}`}>
            <div className={`bubble ${m.error ? "error" : ""}`}>
              {m.role === "assistant" ? (
                <ReactMarkdown>{m.content}</ReactMarkdown>
              ) : (
                m.content
              )}
              {m.sources && m.sources.length > 0 && (
                <div className="sources">
                  <span>Sources:</span>
                  {m.sources.map((s) => (
                    <code key={s.file} title={`relevance ${s.score}`}>
                      {s.file}
                    </code>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="row assistant">
            <div className="bubble typing">
              <span /> <span /> <span />
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </main>

      <footer className="composer">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder="Ask a question…  (Enter to send, Shift+Enter for new line)"
          rows={1}
        />
        <button onClick={() => send(input)} disabled={loading || !input.trim()}>
          Send
        </button>
      </footer>
    </div>
  );
}