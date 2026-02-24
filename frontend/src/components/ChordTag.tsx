interface ChordTagProps {
  children: React.ReactNode;
  className?: string;
}

export default function ChordTag({ children, className = "" }: ChordTagProps) {
  return (
    <span
      className={`chord-tag inline-block ${className}`}
      data-testid="chord-tag"
    >
      {children}
    </span>
  );
}
