/**
 * Detects music notation blocks (ABC, guitar tab, MIDI references) in text.
 * Used by MessageBubble to render interactive music components inline.
 */

export type MusicBlockType = "abc" | "tab" | "midi";

export interface MusicBlock {
  type: MusicBlockType;
  content: string;
  /** Original start index in the source text */
  start: number;
  /** Original end index in the source text */
  end: number;
}

/**
 * Checks if a block of text looks like ABC notation.
 * ABC notation typically starts with header fields (X:, T:, M:, K:, etc.)
 * and contains note sequences.
 */
export function isAbcNotation(text: string): boolean {
  const trimmed = text.trim();
  // Must have at least one ABC header field
  const hasHeader = /^[XTMKLCQPV]:\s*.+$/m.test(trimmed);
  // Must have a key signature (K: is required in ABC)
  const hasKey = /^K:\s*.+$/m.test(trimmed);
  return hasHeader && hasKey;
}

/**
 * Checks if text looks like guitar tablature.
 * Guitar tab has 6 lines starting with string names (e|B|G|D|A|E)
 * followed by |--- patterns with fret numbers.
 */
export function isGuitarTab(text: string): boolean {
  const lines = text.trim().split("\n");
  if (lines.length < 4) return false;

  // Count lines that match tab format: optional string name, then |--digits-- patterns
  const tabLineRe = /^[eBGDAE]?\|?[-\d|hp\/\\~\s]+\|?$/;
  // More specific: a line with dashes and digits separated by |
  const tabContentRe = /[-\d]{3,}/;

  let tabLineCount = 0;
  for (const line of lines) {
    const trimmed = line.trim();
    if (trimmed && tabLineRe.test(trimmed) && tabContentRe.test(trimmed)) {
      tabLineCount++;
    }
  }

  // At least 4 lines that look like tab (standard guitar has 6 strings)
  return tabLineCount >= 4;
}

/**
 * Extracts music blocks from markdown/text content.
 * Looks for:
 * - Fenced code blocks with `abc` language tag
 * - Fenced code blocks with `tab` language tag
 * - Fenced code blocks that auto-detect as ABC or tab
 * - MIDI file references (*.mid, *.midi URLs or filenames)
 */
export function extractMusicBlocks(text: string): MusicBlock[] {
  const blocks: MusicBlock[] = [];

  // Match fenced code blocks: ```lang\n...\n```
  const codeBlockRe = /```(\w*)\n([\s\S]*?)```/g;
  let match: RegExpExecArray | null;

  while ((match = codeBlockRe.exec(text)) !== null) {
    const lang = match[1].toLowerCase();
    const content = match[2].trim();
    const start = match.index;
    const end = start + match[0].length;

    if (lang === "abc" || (!lang && isAbcNotation(content))) {
      blocks.push({ type: "abc", content, start, end });
    } else if (lang === "tab" || lang === "tablature") {
      blocks.push({ type: "tab", content, start, end });
    } else if (!lang && isGuitarTab(content)) {
      blocks.push({ type: "tab", content, start, end });
    }
  }

  return blocks;
}
