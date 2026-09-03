import { useEffect } from "react";
import Link from "@tiptap/extension-link";
import TextAlign from "@tiptap/extension-text-align";
import { EditorContent, useEditor } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import {
  AlignCenter,
  AlignLeft,
  AlignRight,
  Bold,
  Italic,
  Link2,
  List,
  ListOrdered,
  Redo2,
  Undo2,
} from "lucide-react";

const escapeHtml = (value = "") =>
  value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");

const markupToHtml = (value = "") => {
  const inline = (text) =>
    escapeHtml(text)
      .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
      .replace(/__([^_]+)__/g, "<em>$1</em>")
      .replace(/\[([^\]]+)]\((https?:\/\/[^)]+)\)/g, '<a href="$2">$1</a>');
  const lines = value.split(/\n+/).filter(Boolean);
  if (!lines.length) return "<p></p>";
  const output = [];
  let list = null;
  for (const line of lines) {
    const bullet = line.match(/^[-*•]\s+(.*)$/);
    const ordered = line.match(/^\d+[.)]\s+(.*)$/);
    const nextList = bullet ? "ul" : ordered ? "ol" : null;
    if (list && list !== nextList) output.push(`</${list}>`);
    if (nextList && list !== nextList) output.push(`<${nextList}>`);
    if (nextList) output.push(`<li>${inline((bullet || ordered)[1])}</li>`);
    else output.push(`<p>${inline(line)}</p>`);
    list = nextList;
  }
  if (list) output.push(`</${list}>`);
  return output.join("");
};

const serializeInline = (node) => {
  let text = node.text || "";
  for (const mark of node.marks || []) {
    if (mark.type === "bold") text = `**${text}**`;
    if (mark.type === "italic") text = `__${text}__`;
    if (mark.type === "link") text = `[${text}](${mark.attrs.href})`;
  }
  return text;
};

const serializeNode = (node, index = 0) => {
  if (node.type === "text") return serializeInline(node);
  const text = (node.content || []).map(serializeNode).join("");
  if (node.type === "paragraph") return text;
  if (node.type === "bulletList")
    return (node.content || [])
      .map((item) => `- ${serializeNode(item)}`)
      .join("\n");
  if (node.type === "orderedList")
    return (node.content || [])
      .map((item, itemIndex) => `${itemIndex + 1}. ${serializeNode(item)}`)
      .join("\n");
  if (node.type === "listItem") return text;
  if (node.type === "hardBreak") return "\n";
  return text || (index ? "" : "");
};

const editorValue = (editor) =>
  (editor.getJSON().content || []).map(serializeNode).join("\n").trim();

function Tool({ title, active, disabled, onClick, children }) {
  return (
    <button
      type="button"
      title={title}
      aria-label={title}
      className={active ? "active" : ""}
      disabled={disabled}
      onMouseDown={(event) => event.preventDefault()}
      onClick={onClick}
    >
      {children}
    </button>
  );
}

export default function RichTextField({
  value = "",
  onChange,
  disabled,
  ariaLabel,
}) {
  const editor = useEditor({
    extensions: [
      StarterKit.configure({
        heading: false,
        blockquote: false,
        codeBlock: false,
      }),
      Link.configure({ openOnClick: false, protocols: ["http", "https"] }),
      TextAlign.configure({
        types: ["paragraph"],
        alignments: ["left", "center", "right"],
      }),
    ],
    content: markupToHtml(value),
    editable: !disabled,
    editorProps: { attributes: { "aria-label": ariaLabel || "Resume text" } },
    onUpdate: ({ editor: current }) => onChange(editorValue(current)),
  });

  useEffect(() => editor?.setEditable(!disabled), [disabled, editor]);
  useEffect(() => {
    if (editor && editorValue(editor) !== value)
      editor.commands.setContent(markupToHtml(value), { emitUpdate: false });
  }, [editor, value]);
  if (!editor) return null;

  const link = () => {
    const current = editor.getAttributes("link").href || "https://";
    const href = window.prompt("Link URL", current);
    if (href === null) return;
    if (!href.trim()) editor.chain().focus().unsetLink().run();
    else if (/^https?:\/\//i.test(href))
      editor.chain().focus().extendMarkRange("link").setLink({ href }).run();
  };
  return (
    <div className={`rich-text-field ${disabled ? "disabled" : ""}`}>
      <div
        className="rich-text-toolbar"
        role="toolbar"
        aria-label="Text formatting"
      >
        <Tool
          title="Undo"
          disabled={!editor.can().undo()}
          onClick={() => editor.chain().focus().undo().run()}
        >
          <Undo2 size={14} />
        </Tool>
        <Tool
          title="Redo"
          disabled={!editor.can().redo()}
          onClick={() => editor.chain().focus().redo().run()}
        >
          <Redo2 size={14} />
        </Tool>
        <i />
        <Tool
          title="Bold"
          active={editor.isActive("bold")}
          onClick={() => editor.chain().focus().toggleBold().run()}
        >
          <Bold size={14} />
        </Tool>
        <Tool
          title="Italic"
          active={editor.isActive("italic")}
          onClick={() => editor.chain().focus().toggleItalic().run()}
        >
          <Italic size={14} />
        </Tool>
        <Tool title="Link" active={editor.isActive("link")} onClick={link}>
          <Link2 size={14} />
        </Tool>
        <i />
        <Tool
          title="Bulleted list"
          active={editor.isActive("bulletList")}
          onClick={() => editor.chain().focus().toggleBulletList().run()}
        >
          <List size={14} />
        </Tool>
        <Tool
          title="Numbered list"
          active={editor.isActive("orderedList")}
          onClick={() => editor.chain().focus().toggleOrderedList().run()}
        >
          <ListOrdered size={14} />
        </Tool>
        <i />
        <Tool
          title="Align left"
          active={editor.isActive({ textAlign: "left" })}
          onClick={() => editor.chain().focus().setTextAlign("left").run()}
        >
          <AlignLeft size={14} />
        </Tool>
        <Tool
          title="Align center"
          active={editor.isActive({ textAlign: "center" })}
          onClick={() => editor.chain().focus().setTextAlign("center").run()}
        >
          <AlignCenter size={14} />
        </Tool>
        <Tool
          title="Align right"
          active={editor.isActive({ textAlign: "right" })}
          onClick={() => editor.chain().focus().setTextAlign("right").run()}
        >
          <AlignRight size={14} />
        </Tool>
      </div>
      <EditorContent editor={editor} />
    </div>
  );
}
