import React from "react";

type MediaWindowProps = { pdfId: string };

function MediaWindow({ pdfId }: MediaWindowProps) {
  const src = `http://localhost:8000/api/media/pdf/${encodeURIComponent(pdfId)}`;

  return (
    <iframe
      title="PDF viewer"
      src={src}
      style={{ width: "100%", height: "100%", border: "0" }}
    />
  );
}

export default MediaWindow;
