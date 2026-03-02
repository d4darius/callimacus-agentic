import { useState, useEffect } from "react";
import Document from "./components/Document";
import Sidebar from "./components/Sidebar.tsx";
import MediaWindow from "./components/MediaWindow";
import AudioStreamer from "./components/AudioStreamer";
import SettingsModal from "./components/SettingsModal";

function App() {
  // Tracking the currently open file
  const [currentDocId, setCurrentDocId] = useState<string>("");
  const [isMediaExpanded, setIsMediaExpanded] = useState<boolean>(false);
  const [isSessionActive, setIsSessionActive] = useState<boolean>(false);
  const [audioSource, setAudioSource] = useState<"mic" | "system">("mic");
  const [showSettings, setShowSettings] = useState<boolean>(false);
  const [isFirstLoad, setIsFirstLoad] = useState<boolean>(false);

  // Boot Check
  useEffect(() => {
    const key = localStorage.getItem("callimachus_api_key");
    if (!key) {
      setIsFirstLoad(true);
      setShowSettings(true);
    }
  }, []);

  return (
    <>
      {showSettings && (
        <SettingsModal
          onSave={() => {
            setShowSettings(false);
            setIsFirstLoad(false); // Once saved, it is no longer the "first load"
          }}
          isDismissible={!isFirstLoad} // Blocks closing if it's the first time
        />
      )}
      <div className="navbar">
        <div
          className="navbar-brand"
          style={{ display: "flex", alignItems: "center", gap: "8px" }}
        >
          {/* Brain / Notebook Icon replacing the emoji */}
          <img
            src="/src/assets/Callimachus_logo.svg"
            alt="Callimachus Logo"
            style={{ height: "25px", width: "auto" }}
          />
          Callimachus Noter
        </div>

        <div className="navbar-controls">
          {/* Settings Gear Icon Button */}
          <button
            onClick={() => setShowSettings(true)}
            style={{
              background: "transparent",
              border: "none",
              color: "var(--text-muted)",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              padding: "0 8px",
              transition: "color 0.2s",
            }}
            title="Open Settings"
            onMouseEnter={(e) =>
              (e.currentTarget.style.color = "var(--text-main)")
            }
            onMouseLeave={(e) =>
              (e.currentTarget.style.color = "var(--text-muted)")
            }
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
          </button>
          <select
            className="audio-source-select"
            value={audioSource}
            onChange={(e) => setAudioSource(e.target.value as "mic" | "system")}
            disabled={isSessionActive}
          >
            <option value="mic">Microphone</option>
            <option value="system">System/Meeting Audio</option>
          </select>

          <button
            className={`session-btn ${isSessionActive ? "recording" : "idle"}`}
            onClick={() => setIsSessionActive(!isSessionActive)}
          >
            {isSessionActive ? (
              <>
                <svg
                  width="12"
                  height="12"
                  viewBox="0 0 24 24"
                  fill="currentColor"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <rect width="14" height="14" x="5" y="5" rx="2" />
                </svg>
                Stop Session
              </>
            ) : (
              <>
                <svg
                  width="12"
                  height="12"
                  viewBox="0 0 24 24"
                  fill="currentColor"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <circle cx="12" cy="12" r="8" />
                </svg>
                Start Session
              </>
            )}
          </button>
        </div>
      </div>

      <div className="App wrap">
        <Sidebar
          currentDocId={currentDocId}
          onSelectDocument={(id) => setCurrentDocId(id)}
        />
        <div className="document-window">
          <Document
            docname={currentDocId.replace(".json", "")}
            docId={currentDocId}
            isSessionActive={isSessionActive}
          />
        </div>
        <div
          className={`media-window ${isMediaExpanded ? "expanded" : "collapsed"}`}
        >
          <MediaWindow onToggleExpand={setIsMediaExpanded} />
        </div>
      </div>

      <AudioStreamer
        isSessionActive={isSessionActive}
        audioSource={audioSource}
      />
    </>
  );
}

export default App;
