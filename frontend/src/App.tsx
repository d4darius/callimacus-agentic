import { useState } from "react";
import Document from "./components/Document";
import Sidebar from "./components/Sidebar.tsx";
import MediaWindow from "./components/MediaWindow";

function App() {
  // Tracking the currently open file
  const [currentDocId, setCurrentDocId] = useState<string>("");
  const [isMediaExpanded, setIsMediaExpanded] = useState<boolean>(false);

  return (
    <div className="App wrap">
      <Sidebar
        currentDocId={currentDocId}
        onSelectDocument={(id) => setCurrentDocId(id)}
      />
      <div className="document-window">
        <Document
          docname={currentDocId.replace(".json", "")}
          docId={currentDocId}
        />
      </div>
      <div
        className={`media-window ${isMediaExpanded ? "expanded" : "collapsed"}`}
      >
        <MediaWindow onToggleExpand={setIsMediaExpanded} />
      </div>
    </div>
  );
}

export default App;
