import { ButtonHTMLAttributes, FC } from "react";
import clsx from "clsx";

type props = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "default" | "outline";
  size?: "md" | "lg";
};

export const Button: FC<props> = ({
  variant = "default",
  size = "md",
  className,
  children,
  ...props
}) => {
  const base = "font-medium rounded-md transition-colors";

  const variants = {
    default: "bg-primary text-white hover:bg-primary/90",
    outline: "border border-primary text-primary hover:bg-primary/10",
  };

  const sizes = {
    md: "px-4 py-2",
    lg: "px-6 py-3 text-lg",
  };

  return (
    <button
      className={clsx(base, variants[variant], sizes[size], className)}
      {...props}
    >
      {children}
    </button>
  );
};
