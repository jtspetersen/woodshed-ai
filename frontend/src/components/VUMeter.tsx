interface VUMeterProps {
  active?: boolean;
  bars?: number;
  className?: string;
}

const BAR_COLORS = [
  "bg-sage-400",
  "bg-sage-400",
  "bg-sage-300",
  "bg-amber-400",
  "bg-amber-300",
  "bg-rust-400",
  "bg-rust-500",
];

export default function VUMeter({
  active = true,
  bars = 5,
  className = "",
}: VUMeterProps) {
  return (
    <div
      className={`flex items-end gap-0.5 h-5 ${className}`}
      role="status"
      aria-label={active ? "Loading" : "Idle"}
      data-testid="vu-meter"
    >
      {Array.from({ length: bars }, (_, i) => (
        <div
          key={i}
          className={`w-1 rounded-full transition-transform ${
            BAR_COLORS[i % BAR_COLORS.length]
          } ${active ? "animate-vu-pulse" : "scale-y-[0.3]"}`}
          style={{
            height: "100%",
            animationDelay: active ? `${i * 100}ms` : undefined,
          }}
          data-testid="vu-bar"
        />
      ))}
    </div>
  );
}
