import React, { useState, useRef } from "react";

interface MediaWindowProps {
  onToggleExpand: (isExpanded: boolean) => void;
}

function MediaWindow({ onToggleExpand }: MediaWindowProps) {
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleContainerClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file && file.type === "application/pdf") {
      // 💡 THE TRICK: Append #toolbar=0 to natively hide the top bar!
      const fileUrl = URL.createObjectURL(file) + "#toolbar=0&navpanes=0";
      setPdfUrl(fileUrl);
      onToggleExpand(true); // Tell App.tsx to expand the window
    } else if (file) {
      alert("Please select a valid PDF file.");
    }
  };

  const closePdf = () => {
    setPdfUrl(null);
    onToggleExpand(false); // Tell App.tsx to shrink the window
  };

  if (pdfUrl) {
    return (
      <div style={{ width: "100%", height: "100%", position: "relative" }}>
        <button
          onClick={closePdf}
          style={{
            position: "absolute",
            top: "8px",
            right: "24px",
            background: "#2a2a2a",
            color: "#aaa",
            border: "1px solid #444",
            padding: "4px 8px",
            borderRadius: "4px",
            cursor: "pointer",
            zIndex: 10,
            fontSize: "12px",
            boxShadow: "0 2px 6px rgba(0,0,0,0.5)",
          }}
        >
          ✕ Close PDF
        </button>

        <iframe
          title="PDF viewer"
          src={pdfUrl}
          style={{ width: "100%", height: "100%", border: "0" }}
        />
      </div>
    );
  }

  return (
    <div
      onClick={handleContainerClick}
      style={{
        width: "100%",
        height: "100%",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        cursor: "pointer",
        backgroundColor: "#1e1e1e",
        border: "2px dashed #444",
        borderRadius: "8px",
        boxSizing: "border-box",
        transition: "background-color 0.2s ease",
      }}
      onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = "#242424")}
      onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = "#1e1e1e")}
    >
      <input
        type="file"
        accept="application/pdf"
        ref={fileInputRef}
        onChange={handleFileChange}
        style={{ display: "none" }}
      />

      <div
        style={{
          fontSize: "32px",
          color: "#555",
          marginBottom: "8px",
          fontWeight: "300",
        }}
      >
        +
      </div>
      <button
        style={{
          padding: "6px 12px",
          fontSize: "12px",
          backgroundColor: "#a970ff",
          color: "white",
          fontWeight: "bold",
          border: "none",
          borderRadius: "6px",
          cursor: "pointer",
          pointerEvents: "none",
          whiteSpace: "nowrap",
        }}
      >
        Open file
      </button>
    </div>
  );
}

export default MediaWindow;
