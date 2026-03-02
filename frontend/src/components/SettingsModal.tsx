import React, { useState, useEffect } from "react";

interface SettingsModalProps {
  onSave: () => void;
  isDismissible: boolean; // False on first load, True if opened from a settings button
}

export default function SettingsModal({
  onSave,
  isDismissible,
}: SettingsModalProps) {
  const [apiKey, setApiKey] = useState("");
  const [llmModel, setLlmModel] = useState("gpt-4o");
  const [background, setBackground] = useState("");
  const [preferences, setPreferences] = useState("");

  // Load existing settings on mount
  useEffect(() => {
    setApiKey(localStorage.getItem("callimachus_api_key") || "");
    setLlmModel(localStorage.getItem("callimachus_llm") || "gpt-4o");
    setBackground(
      localStorage.getItem("callimachus_background") ||
        "I am a student taking detailed lecture notes.",
    );
    setPreferences(
      localStorage.getItem("callimachus_preferences") ||
        "Use bullet points and concise language.",
    );
  }, []);

  const handleSave = () => {
    if (!apiKey.trim()) {
      alert("An API Key is required to use Callimachus.");
      return;
    }

    // Persist to local storage
    localStorage.setItem("callimachus_api_key", apiKey.trim());
    localStorage.setItem("callimachus_llm", llmModel);
    localStorage.setItem("callimachus_background", background);
    localStorage.setItem("callimachus_preferences", preferences);

    onSave();
  };

  return (
    <div
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: "rgba(0, 0, 0, 0.7)",
        backdropFilter: "blur(4px)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 99999,
      }}
    >
      <div
        style={{
          background: "var(--bg-media)",
          padding: "24px",
          borderRadius: "8px",
          width: "500px",
          border: "1px solid var(--border-color)",
          boxShadow: "0 10px 40px rgba(0,0,0,0.5)",
          color: "var(--text-main)",
        }}
      >
        <h2
          style={{
            margin: "0 0 20px 0",
            color: "var(--text-heading)",
            fontSize: "1.2rem",
            display: "flex",
            alignItems: "center",
            gap: "8px",
          }}
        >
          <svg
            width="18"
            height="18"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <circle cx="12" cy="12" r="3" />
            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
          </svg>
          Callimachus Setup
        </h2>

        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          <div>
            <label
              style={{
                display: "block",
                fontSize: "0.85rem",
                marginBottom: "6px",
                color: "var(--text-muted)",
              }}
            >
              LLM Provider
            </label>
            <select
              value={llmModel}
              onChange={(e) => setLlmModel(e.target.value)}
              style={{
                width: "100%",
                padding: "8px",
                background: "var(--bg-document)",
                border: "1px solid var(--border-color)",
                color: "var(--text-main)",
                borderRadius: "4px",
              }}
            >
              <optgroup label="Official API (BYOK)">
                <option value="gpt-4o">OpenAI (GPT-4o)</option>
                <option value="claude-3-5-sonnet-20240620">
                  Anthropic (Claude 3.5 Sonnet)
                </option>
                <option value="groq:llama3-70b-8192">Groq (Llama 3 70B)</option>
              </optgroup>

              <optgroup label="Anti-API (Local Proxy)">
                <option value="anti-api:gpt-4.1">
                  Anti-API Copilot (GPT-4.1)
                </option>
                <option value="anti-api:gpt-4o">
                  Anti-API Copilot (GPT-4o)
                </option>
                <option value="anti-api:claude-sonnet-4-5">
                  Anti-API Copilot (Claude Sonnet 3.5)
                </option>
                <option value="anti-api:gemini-3.1-pro-preview">
                  Anti-API Copilot (Gemini 3.1 Pro)
                </option>
              </optgroup>
            </select>
          </div>

          <div>
            <label
              style={{
                display: "block",
                fontSize: "0.85rem",
                marginBottom: "6px",
                color: "var(--text-muted)",
              }}
            >
              API Key
            </label>
            <input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="sk-..."
              style={{
                width: "100%",
                padding: "8px",
                background: "var(--bg-document)",
                border: "1px solid var(--border-color)",
                color: "var(--text-main)",
                borderRadius: "4px",
                boxSizing: "border-box",
              }}
            />
          </div>

          <div>
            <label
              style={{
                display: "block",
                fontSize: "0.85rem",
                marginBottom: "6px",
                color: "var(--text-muted)",
              }}
            >
              Your Background (Optional)
            </label>
            <textarea
              value={background}
              onChange={(e) => setBackground(e.target.value)}
              rows={2}
              style={{
                width: "100%",
                padding: "8px",
                background: "var(--bg-document)",
                border: "1px solid var(--border-color)",
                color: "var(--text-main)",
                borderRadius: "4px",
                boxSizing: "border-box",
                resize: "none",
              }}
            />
          </div>

          <div>
            <label
              style={{
                display: "block",
                fontSize: "0.85rem",
                marginBottom: "6px",
                color: "var(--text-muted)",
              }}
            >
              Format Preferences (Optional)
            </label>
            <textarea
              value={preferences}
              onChange={(e) => setPreferences(e.target.value)}
              rows={2}
              style={{
                width: "100%",
                padding: "8px",
                background: "var(--bg-document)",
                border: "1px solid var(--border-color)",
                color: "var(--text-main)",
                borderRadius: "4px",
                boxSizing: "border-box",
                resize: "none",
              }}
            />
          </div>
        </div>

        <div
          style={{
            display: "flex",
            justifyContent: "flex-end",
            gap: "12px",
            marginTop: "24px",
          }}
        >
          {isDismissible && (
            <button
              onClick={onSave}
              style={{
                padding: "8px 16px",
                background: "transparent",
                border: "1px solid var(--border-color)",
                color: "var(--text-muted)",
                borderRadius: "4px",
                cursor: "pointer",
              }}
            >
              Cancel
            </button>
          )}
          <button
            onClick={handleSave}
            style={{
              padding: "8px 16px",
              background: "var(--accent-blue)",
              border: "none",
              color: "white",
              borderRadius: "4px",
              fontWeight: "500",
              cursor: "pointer",
            }}
          >
            Save & Continue
          </button>
        </div>
      </div>
    </div>
  );
}
