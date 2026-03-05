import { useState, useEffect } from "react";

interface SettingsModalProps {
  onSave: () => void;
  isDismissible: boolean;
}

export default function SettingsModal({
  onSave,
  isDismissible,
}: SettingsModalProps) {
  // --- TABS & MODES ---
  const [activeTab, setActiveTab] = useState<"api" | "background">("api");
  const [apiMode, setApiMode] = useState<"personal" | "anti-api">("personal");

  // --- SETTINGS STATE ---
  const [apiKey, setApiKey] = useState("");
  const [llmModel, setLlmModel] = useState("gpt-4o");
  const [background, setBackground] = useState("");
  const [preferences, setPreferences] = useState("");

  // --- ANTI-API STATE ---
  const [antiApiStatus, setAntiApiStatus] = useState<
    "idle" | "starting" | "running" | "error"
  >("idle");
  const [antiApiModels, setAntiApiModels] = useState<string[]>([]);

  // Load existing settings on mount
  useEffect(() => {
    setApiKey(localStorage.getItem("callimachus_api_key") || "");
    const savedModel = localStorage.getItem("callimachus_llm") || "gpt-4o";
    setLlmModel(savedModel);

    // Auto-detect if they were previously using anti-api
    if (savedModel.startsWith("anti-api:")) {
      setApiMode("anti-api");
      // The backend already started it on boot! Just wait for it to be ready.
      setAntiApiStatus("starting");
      fetchAntiApiModels(15);
    }

    setBackground(
      localStorage.getItem("callimachus_background") ||
        "I am a student taking detailed lecture notes.",
    );
    setPreferences(
      localStorage.getItem("callimachus_preferences") ||
        "Use bullet points and concise language.",
    );
  }, []);

  // --- ANTI-API CONTROLS ---
  const handleStartAntiApi = async () => {
    setAntiApiStatus("starting");
    try {
      const res = await fetch("http://localhost:8000/api/anti-api/start", {
        method: "POST",
      });
      if (res.ok) {
        // Start polling the server. It will try 5 times (waiting 2 seconds between each try)
        fetchAntiApiModels(5);
      } else {
        setAntiApiStatus("error");
      }
    } catch (err) {
      console.error(err);
      setAntiApiStatus("error");
    }
  };

  // Wait for Bun and Rust to compile!
  const fetchAntiApiModels = async (retries = 0) => {
    try {
      const res = await fetch("http://localhost:8000/api/anti-api/models");
      if (res.ok) {
        const data = await res.json();
        setAntiApiModels(data.models || []);
        setAntiApiStatus("running"); // ONLY set to running once we get a successful response
      } else {
        throw new Error("Proxy not ready yet");
      }
    } catch (err) {
      if (retries > 0) {
        console.warn(
          `Anti-API compiling/booting... Retrying in 2s. (${retries} attempts left)`,
        );
        setTimeout(() => fetchAntiApiModels(retries - 1), 2000);
      } else {
        console.error("Anti-API failed to boot after multiple attempts.");
        setAntiApiStatus("error");
      }
    }
  };

  // Handles shutting down the local server when switching modes
  const handleModeChange = async (newMode: "personal" | "anti-api") => {
    setApiMode(newMode);

    if (newMode === "personal") {
      setLlmModel("gpt-4o");
      try {
        await fetch("http://localhost:8000/api/anti-api/stop", {
          method: "POST",
        });
        setAntiApiStatus("idle");
        setAntiApiModels([]);
      } catch (err) {
        console.error("Failed to stop Anti-API", err);
      }
    } else {
      setLlmModel("");
      // Automatically start the engine as soon as they select the dropdown!
      handleStartAntiApi();
    }
  };

  const handleSave = () => {
    if (apiMode === "personal" && !apiKey.trim()) {
      alert("An API Key is required for Personal API mode.");
      return;
    }
    if (apiMode === "anti-api" && !llmModel.startsWith("anti-api:")) {
      alert("Please select a valid Anti-API model.");
      return;
    }

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
          }}
        >
          Callimachus Setup
        </h2>

        {/* TABS HEADER */}
        <div
          style={{
            display: "flex",
            gap: "10px",
            marginBottom: "20px",
            borderBottom: "1px solid var(--border-color)",
            paddingBottom: "10px",
          }}
        >
          <button
            onClick={() => setActiveTab("api")}
            style={{
              background: "transparent",
              border: "none",
              cursor: "pointer",
              fontWeight: "bold",
              color:
                activeTab === "api"
                  ? "var(--accent-blue)"
                  : "var(--text-muted)",
            }}
          >
            API & Models
          </button>
          <button
            onClick={() => setActiveTab("background")}
            style={{
              background: "transparent",
              border: "none",
              cursor: "pointer",
              fontWeight: "bold",
              color:
                activeTab === "background"
                  ? "var(--accent-blue)"
                  : "var(--text-muted)",
            }}
          >
            Background Info
          </button>
        </div>

        {/* TAB 1: API & MODELS */}
        {activeTab === "api" && (
          <div
            style={{ display: "flex", flexDirection: "column", gap: "16px" }}
          >
            {/* Clean Dropdown Selector */}
            <div>
              <label
                style={{
                  display: "block",
                  fontSize: "0.85rem",
                  marginBottom: "6px",
                  color: "var(--text-muted)",
                }}
              >
                API Connection Mode
              </label>
              <select
                value={apiMode}
                onChange={(e) =>
                  handleModeChange(e.target.value as "personal" | "anti-api")
                }
                style={{
                  width: "100%",
                  padding: "10px",
                  background: "var(--bg-document)",
                  border: "1px solid var(--border-color)",
                  color: "var(--text-main)",
                  borderRadius: "4px",
                  fontWeight: "500",
                  cursor: "pointer",
                }}
              >
                <option value="personal">
                  Personal API (Official Providers)
                </option>
                <option value="anti-api">Anti-API (Local Proxy)</option>
              </select>
            </div>

            {/* CONDITIONAL: PERSONAL API */}
            {apiMode === "personal" && (
              <>
                <div>
                  <label
                    style={{
                      display: "block",
                      fontSize: "0.85rem",
                      marginBottom: "6px",
                      color: "var(--text-muted)",
                    }}
                  >
                    Official Provider
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
                    <option value="gpt-4o">OpenAI (GPT-4o)</option>
                    <option value="claude-3-5-sonnet-20240620">
                      Anthropic (Claude 3.5 Sonnet)
                    </option>
                    <option value="groq:llama3-70b-8192">
                      Groq (Llama 3 70B)
                    </option>
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
              </>
            )}

            {/* CONDITIONAL: ANTI-API */}
            {apiMode === "anti-api" && (
              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  gap: "12px",
                  border: "1px dashed var(--border-color)",
                  padding: "16px",
                  borderRadius: "6px",
                }}
              >
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                  }}
                >
                  <span style={{ fontSize: "0.9rem" }}>Anti-API Engine</span>
                  <span
                    style={{
                      fontSize: "0.85rem",
                      fontWeight: "500",
                      color:
                        antiApiStatus === "running"
                          ? "var(--state-success)"
                          : antiApiStatus === "error"
                            ? "#ff6b6b"
                            : "var(--accent-blue)",
                    }}
                  >
                    {antiApiStatus === "idle"
                      ? "Waiting..."
                      : antiApiStatus === "starting"
                        ? "Booting Engine..."
                        : antiApiStatus === "error"
                          ? "Error"
                          : "Running"}
                  </span>
                </div>

                {antiApiStatus === "error" && (
                  <span style={{ color: "#ff6b6b", fontSize: "0.8rem" }}>
                    Failed to start. Check backend terminal.
                  </span>
                )}

                {/* Opens the Dashboard in a new tab */}
                {antiApiStatus === "running" && (
                  <a
                    href="http://localhost:8964"
                    target="_blank"
                    rel="noreferrer"
                    style={{
                      color: "var(--accent-blue)",
                      fontSize: "0.85rem",
                      textDecoration: "none",
                      display: "inline-block",
                    }}
                  >
                    Open Copilot Setup Dashboard ↗
                  </a>
                )}

                <div>
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      marginBottom: "6px",
                    }}
                  >
                    <label
                      style={{
                        fontSize: "0.85rem",
                        color: "var(--text-muted)",
                      }}
                    >
                      Available Local Models
                    </label>
                    <span
                      onClick={() => fetchAntiApiModels()}
                      style={{
                        fontSize: "0.8rem",
                        color: "var(--accent-blue)",
                        cursor: "pointer",
                      }}
                    >
                      ↻ Refresh
                    </span>
                  </div>

                  {/* Model Selector - Disabled until running */}
                  <select
                    value={llmModel}
                    onChange={(e) => setLlmModel(e.target.value)}
                    disabled={
                      antiApiStatus !== "running" || antiApiModels.length === 0
                    }
                    style={{
                      width: "100%",
                      padding: "8px",
                      background: "var(--bg-document)",
                      border: "1px solid var(--border-color)",
                      color: "var(--text-main)",
                      borderRadius: "4px",
                      opacity: antiApiStatus === "running" ? 1 : 0.5,
                      cursor:
                        antiApiStatus === "running" ? "pointer" : "not-allowed",
                    }}
                  >
                    <option value="" disabled>
                      {antiApiStatus === "running" && antiApiModels.length > 0
                        ? "Select a connected model..."
                        : "Start engine and connect models first..."}
                    </option>

                    {antiApiModels.map((m) => (
                      <option key={m} value={`anti-api:${m}`}>
                        {m}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            )}
          </div>
        )}

        {/* TAB 2: BACKGROUND INFO */}
        {activeTab === "background" && (
          <div
            style={{ display: "flex", flexDirection: "column", gap: "16px" }}
          >
            <div>
              <label
                style={{
                  display: "block",
                  fontSize: "0.85rem",
                  marginBottom: "6px",
                  color: "var(--text-muted)",
                }}
              >
                Your Background
              </label>
              <textarea
                value={background}
                onChange={(e) => setBackground(e.target.value)}
                rows={3}
                style={{
                  width: "100%",
                  padding: "8px",
                  background: "var(--bg-document)",
                  border: "1px solid var(--border-color)",
                  color: "var(--text-main)",
                  borderRadius: "4px",
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
                Format Preferences
              </label>
              <textarea
                value={preferences}
                onChange={(e) => setPreferences(e.target.value)}
                rows={3}
                style={{
                  width: "100%",
                  padding: "8px",
                  background: "var(--bg-document)",
                  border: "1px solid var(--border-color)",
                  color: "var(--text-main)",
                  borderRadius: "4px",
                  resize: "none",
                }}
              />
            </div>
          </div>
        )}

        {/* ACTION BUTTONS */}
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
