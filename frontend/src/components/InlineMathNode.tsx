import { createReactInlineContentSpec } from "@blocknote/react";
import { InlineMath } from "react-katex";
import "katex/dist/katex.min.css";

export const InlineMathNode = createReactInlineContentSpec(
  {
    type: "mathInline",
    propSchema: {
      equation: {
        default: "x",
      },
    },
    content: "none",
  },
  {
    render: (props) => (
      <span
        className="inline-math-node"
        style={{
          padding: "0 4px",
          color: "inherit",
          backgroundColor: "rgba(0,0,0,0.15)", // Slight highlight to distinguish it
          borderRadius: "4px",
        }}
        title="Inline Math"
      >
        <InlineMath math={props.inlineContent.props.equation} />
      </span>
    ),
  },
);
