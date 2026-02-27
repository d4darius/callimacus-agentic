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

  return (
    <>
      <div
        className="navbar"
        style={{
          display: "flex",
          alignItems: "center",
          padding: "0 20px",
          justifyContent: "space-between",
          boxSizing: "border-box",
        }}
      >
        <div
          style={{ fontWeight: "bold", color: "white", letterSpacing: "0.5px" }}
        >
          🧠 Callimachus Noter
        </div>
        <button
          onClick={() => setIsSessionActive(!isSessionActive)}
          style={{
            backgroundColor: isSessionActive ? "#ff4b4b" : "#20c997",
            color: "white",
            border: "none",
            padding: "6px 16px",
            borderRadius: "6px",
            fontWeight: "bold",
            cursor: "pointer",
            transition: "background-color 0.2s",
            boxShadow: "0 2px 8px rgba(0,0,0,0.2)",
          }}
        >
          {isSessionActive ? "⏹ Stop Session" : "● Start Session"}
        </button>
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
      <AudioStreamer isSessionActive={isSessionActive} />
    </>
  );
}

export default App;
