import { useState } from "react";
import Document from "./components/Document";
import Sidebar from "./components/Sidebar.tsx";
import MediaWindow from "./components/MediaWindow";
import AudioStreamer from "./components/AudioStreamer";

function App() {
  // Tracking the currently open file
  const [currentDocId, setCurrentDocId] = useState<string>("");
  const [isMediaExpanded, setIsMediaExpanded] = useState<boolean>(false);
  const [isSessionActive, setIsSessionActive] = useState<boolean>(false);
  const [audioSource, setAudioSource] = useState<"mic" | "system">("mic");

  return (
    <>
      <div className="navbar">
        <div
          className="navbar-brand"
          style={{ display: "flex", alignItems: "center", gap: "8px" }}
        >
          {/* Brain / Notebook Icon replacing the emoji */}
          <svg
            width="18"
            height="18"
            viewBox="0 0 24 24"
            fill="none"
            stroke="var(--accent-blue)"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20" />
          </svg>
          Callimachus Noter
        </div>

        <div className="navbar-controls">
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
