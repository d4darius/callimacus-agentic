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
        <div className="navbar-brand">🧠 Callimachus Noter</div>

        <div className="navbar-controls">
          <select
            className="audio-source-select"
            value={audioSource}
            onChange={(e) => setAudioSource(e.target.value as "mic" | "system")}
            disabled={isSessionActive}
          >
            <option value="mic">🎤 Microphone</option>
            <option value="system">💻 System/Meeting Audio</option>
          </select>

          <button
            className={`session-btn ${isSessionActive ? "recording" : "idle"}`}
            onClick={() => setIsSessionActive(!isSessionActive)}
          >
            {isSessionActive ? "⏹ Stop Session" : "● Start Session"}
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
