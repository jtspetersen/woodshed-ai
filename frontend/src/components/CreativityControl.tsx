"use client";

const OPTIONS = ["More Precise", "Balanced", "More Creative"] as const;
export type Creativity = (typeof OPTIONS)[number];

interface CreativityControlProps {
  value: Creativity;
  onChange: (value: Creativity) => void;
  disabled?: boolean;
  className?: string;
}

export default function CreativityControl({
  value,
  onChange,
  disabled = false,
  className = "",
}: CreativityControlProps) {
  return (
    <div
      className={`flex gap-1 bg-bark-900 rounded-full p-1 border border-bark-600 ${className}`}
      role="radiogroup"
      aria-label="Creativity level"
    >
      {OPTIONS.map((option) => {
        const selected = option === value;
        return (
          <button
            key={option}
            type="button"
            role="radio"
            aria-checked={selected}
            disabled={disabled}
            onClick={() => onChange(option)}
            className={`px-3 py-1 text-sm font-display font-semibold rounded-full transition-all duration-fast ${
              selected
                ? "bg-amber-400 text-bark-950"
                : "text-bark-400 hover:text-amber-100"
            } disabled:opacity-50 disabled:cursor-not-allowed`}
          >
            {option}
          </button>
        );
      })}
    </div>
  );
}
