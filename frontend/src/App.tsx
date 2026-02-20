import { useState } from "react";
import Document from "./components/Document";
import Sidebar from "./components/Sidebar.tsx";
import MediaWindow from "./components/MediaWindow";

function App() {
  // Tracking the currently open file
  const [currentDocId, setCurrentDocId] = useState<string>("test.json");

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
      <div className="media-window">
        <MediaWindow pdfId="test" />
      </div>
    </div>
  );
}

export default App;
