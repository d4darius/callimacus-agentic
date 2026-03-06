import { createReactBlockSpec } from "@blocknote/react";
import { InlineMath } from "react-katex";
import "katex/dist/katex.min.css";
import { useState } from "react";

export const MathBlock = createReactBlockSpec(
  {
    type: "math",
    propSchema: {
      content: {
        default: "e = mc^2",
      },
    },
    content: "none",
  },
  {
    render: (props) => {
      // Tracks whether the user is typing or viewing
      const [isEditing, setIsEditing] = useState(false);

      return (
        <div 
          className="math-block-container" 
          style={{ padding: "10px 0", textAlign: "center", cursor: "pointer" }}
          onClick={() => setIsEditing(true)}
          onBlur={() => setIsEditing(false)}
        >
          {isEditing ? (
            // Shows a dark-themed input box for LaTeX code
            <input
              autoFocus
              style={{
                width: "100%",
                padding: "8px",
                background: "var(--bg-media)", 
                color: "var(--text-main)",
                border: "1px solid var(--accent-blue)",
                borderRadius: "4px",
                fontFamily: "monospace",
                textAlign: "center",
                outline: "none"
              }}
              value={props.block.props.content}
              onChange={(e) => {
                // Live updates the block's memory as you type!
                props.editor.updateBlock(props.block, {
                  type: "math",
                  props: { content: e.target.value },
                });
              }}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  setIsEditing(false); // Close the editor on Enter!
                }
              }}
            />
          ) : (
            // Renders the beautiful KaTeX equation
            <div style={{ minHeight: "24px" }} title="Click to edit equation">
              <InlineMath math={props.block.props.content || "\\text{Empty equation}"} />
            </div>
          )}
        </div>
      );
    },
  }
);