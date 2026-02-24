import { ButtonHTMLAttributes } from "react";

type Variant = "primary" | "secondary" | "ghost" | "danger";
type Size = "sm" | "default" | "lg";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
}

const variantClasses: Record<Variant, string> = {
  primary:
    "bg-amber-400 text-bark-950 hover:bg-amber-300 hover:shadow-glow font-display font-bold",
  secondary:
    "bg-transparent text-amber-400 border border-bark-600 hover:border-amber-400 font-display font-semibold",
  ghost:
    "bg-transparent text-bark-400 hover:bg-bark-700 hover:text-amber-100 font-body",
  danger:
    "bg-transparent text-rust-400 border border-rust-500 hover:bg-rust-500/10 font-display font-semibold",
};

const sizeClasses: Record<Size, string> = {
  sm: "text-sm px-3 py-1",
  default: "text-base px-4 py-2",
  lg: "text-lg px-6 py-3",
};

export default function Button({
  variant = "primary",
  size = "default",
  className = "",
  children,
  ...props
}: ButtonProps) {
  return (
    <button
      className={`rounded-full transition-all duration-normal ease-out disabled:opacity-50 disabled:cursor-not-allowed ${variantClasses[variant]} ${sizeClasses[size]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}
