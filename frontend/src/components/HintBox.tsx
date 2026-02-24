interface HintBoxProps {
  children: React.ReactNode;
  className?: string;
}

export default function HintBox({ children, className = "" }: HintBoxProps) {
  return (
    <div
      className={`flex gap-3 rounded-lg bg-amber-400/5 border-l-4 border-amber-400 p-4 ${className}`}
      role="note"
    >
      <svg
        className="w-5 h-5 text-amber-400 shrink-0 mt-0.5"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        strokeWidth={2}
        aria-hidden="true"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
      <div className="text-sm text-amber-100/80 font-body">{children}</div>
    </div>
  );
}
