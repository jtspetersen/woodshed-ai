/**
 * Lightweight markdown-to-HTML renderer for chat messages.
 * Handles: bold, italic, inline code, code blocks, newlines, chord detection.
 */

// Chord symbol regex: root + optional accidental + quality suffix
// Only matches when a quality suffix is present (avoids false positives on "A", "C", etc.)
const CHORD_RE =
  /\b([A-G][#b]?)(maj7|maj9|maj|min7|min9|min|m7b5|m7|m9|m11|mmaj7|m|dim7|dim|aug7|aug|sus2|sus4|sus|add9|6\/9|7#9|7b9|7#5|7b5|13|11|9|7|6)\b/g;

// Bare major chord regex: matches single-letter chords (A, C, D, etc.) only when
// they appear in a chord-sequence context (next to dashes, arrows, commas with other chords)
// e.g. "Em - Am - D - C" or "G, C, D"
const BARE_CHORD_RE =
  /(?<=[\s,\-–—→>])\b([A-G][#b]?)\b(?=\s*[\s,\-–—→><]|\s*$)/g;

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

export function renderMarkdown(text: string): string {
  // 1. Escape HTML entities first (security for dangerouslySetInnerHTML)
  let html = escapeHtml(text);

  // 2. Code blocks (```lang\n...\n```) — must come before inline processing
  html = html.replace(/```(\w*)\n([\s\S]*?)```/g, (_, lang, code) => {
    const dataAttr = lang === "abc" ? ' data-notation="abc"' : "";
    return `<pre class="font-mono text-sm bg-bark-950 border border-bark-600 rounded-md p-3 my-2 overflow-x-auto"${dataAttr}><code>${code.trim()}</code></pre>`;
  });

  // 3. Inline code (`...`)
  html = html.replace(
    /`([^`]+)`/g,
    '<code class="font-mono text-sm bg-bark-800 text-amber-300 px-1.5 py-0.5 rounded">$1</code>',
  );

  // 4. Bold (**...**)
  html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");

  // 5. Italic (*...*)
  html = html.replace(/\*(.+?)\*/g, "<em>$1</em>");

  // 5b. Markdown links [text](url) — strip file download links
  //     (generated files have dedicated download buttons already)
  html = html.replace(
    /\[([^\]]+)\]\(([^)]+)\)/g,
    (_, text: string, href: string) => {
      const lower = text.toLowerCase();
      if (
        lower.includes("download") ||
        lower.includes("midi file") ||
        href === "&quot;#&quot;" ||
        href === "#" ||
        href.endsWith(".mid") ||
        href.endsWith(".midi")
      ) {
        return "";
      }
      return `<a href="${href}">${text}</a>`;
    },
  );

  // 6. Chord symbols — wrap in chord-tag span (outside code blocks)
  const parts = html.split(/(<pre[\s\S]*?<\/pre>|<code[\s\S]*?<\/code>|<span class="chord-tag">[\s\S]*?<\/span>)/g);
  html = parts
    .map((part) => {
      if (part.startsWith("<pre") || part.startsWith("<code") || part.startsWith('<span class="chord-tag"')) return part;
      // First pass: chords with explicit quality suffix (Dm7, Cmaj7, etc.)
      let result = part.replace(
        CHORD_RE,
        '<span class="chord-tag">$&</span>',
      );
      // Second pass: bare major chords in sequence context (D, C, A next to dashes/commas)
      result = result.replace(
        BARE_CHORD_RE,
        '<span class="chord-tag">$1</span>',
      );
      return result;
    })
    .join("");

  // 7. Newlines to <br> outside pre blocks
  const finalParts = html.split(/(<pre[\s\S]*?<\/pre>)/g);
  html = finalParts
    .map((part) => {
      if (part.startsWith("<pre")) return part;
      return part.replace(/\n/g, "<br>");
    })
    .join("");

  return html;
}
