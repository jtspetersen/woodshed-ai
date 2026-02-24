interface LogoProps {
  size?: number;
  className?: string;
}

export default function Logo({ size = 40, className = "" }: LogoProps) {
  return (
    <div className={`flex items-center gap-3 ${className}`}>
      <svg
        viewBox="0 0 64 64"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        width={size}
        height={size}
        aria-hidden="true"
      >
        <path
          d="M8 28L32 10L56 28V52C56 54.2091 54.2091 56 52 56H12C9.79086 56 8 54.2091 8 52V28Z"
          fill="#3D3229"
        />
        <path d="M8 28L32 10L56 28Z" fill="#4A3B2E" />
        <line
          x1="10" y1="28" x2="54" y2="28"
          stroke="#F5A623" strokeWidth="1" opacity="0.3"
        />
        <g opacity="0.9">
          <ellipse cx="24.5" cy="45.5" rx="3.2" ry="2.4" fill="#FCBF6A" transform="rotate(-15 24.5 45.5)" />
          <line x1="27.2" y1="44.5" x2="27.2" y2="34" stroke="#FCBF6A" strokeWidth="1.8" strokeLinecap="round" />
          <path d="M27.2 34C27.2 34 30 35.2 32 37.5" stroke="#FCBF6A" strokeWidth="1.4" strokeLinecap="round" fill="none" />
        </g>
        <g opacity="0.7">
          <ellipse cx="37.5" cy="43" rx="3.2" ry="2.4" fill="#FCBF6A" transform="rotate(-15 37.5 43)" />
          <line x1="40.2" y1="42" x2="40.2" y2="33" stroke="#FCBF6A" strokeWidth="1.8" strokeLinecap="round" />
          <path d="M40.2 33C40.2 33 42.8 34 44.5 36" stroke="#FCBF6A" strokeWidth="1.4" strokeLinecap="round" fill="none" />
        </g>
        <path
          d="M8 28L32 10L56 28V52C56 54.2091 54.2091 56 52 56H12C9.79086 56 8 54.2091 8 52V28Z"
          fill="none" stroke="#F5A623" strokeWidth="2.5" strokeLinejoin="round"
        />
      </svg>
      <span className="font-display">
        <span className="font-extrabold text-amber-100">Woodshed</span>
        <span className="font-semibold text-amber-100/60 ml-1">AI</span>
      </span>
    </div>
  );
}
