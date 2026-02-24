interface GuitarTabProps {
  tab: string;
}

/** Regex to highlight chord names above tab lines (e.g., Am, Dm7, G7) */
const CHORD_IN_TAB_RE =
  /\b([A-G][#b]?(?:maj7|maj9|maj|min7|min9|min|m7b5|m7|m9|m|dim7|dim|aug|sus[24]|add9|7|9|6)?)\b/g;

export default function GuitarTab({ tab }: GuitarTabProps) {
  // Process lines: tab lines stay monospace, text lines get chord highlighting
  const lines = tab.split("\n");

  const tabLineRe = /^[eBGDAE]?\|?[-\d|hp\/\\~\s]+\|?$/;

  return (
    <pre
      className="font-mono text-sm bg-bark-800 border border-bark-600 rounded-md p-3 my-2 overflow-x-auto leading-relaxed"
      data-testid="guitar-tab"
    >
      {lines.map((line, i) => {
        const trimmed = line.trim();
        const isTabLine = tabLineRe.test(trimmed) && /[-\d]{3,}/.test(trimmed);

        if (isTabLine) {
          // Pure tab line — render as-is in monospace
          return (
            <span key={i} className="text-amber-100">
              {line}
              {"\n"}
            </span>
          );
        }

        // Text/chord label line — highlight chord names
        const parts: React.ReactNode[] = [];
        let lastIndex = 0;
        let match: RegExpExecArray | null;
        const re = new RegExp(CHORD_IN_TAB_RE.source, "g");

        while ((match = re.exec(line)) !== null) {
          if (match.index > lastIndex) {
            parts.push(line.slice(lastIndex, match.index));
          }
          parts.push(
            <span key={`${i}-${match.index}`} className="text-amber-400 font-bold">
              {match[0]}
            </span>,
          );
          lastIndex = re.lastIndex;
        }
        if (lastIndex < line.length) {
          parts.push(line.slice(lastIndex));
        }

        return (
          <span key={i} className="text-bark-300">
            {parts.length > 0 ? parts : line}
            {"\n"}
          </span>
        );
      })}
    </pre>
  );
}
