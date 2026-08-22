/**
 * Stroke-based icon set on a 24px grid.
 *
 * Inline SVG rather than a font or emoji so icons inherit `currentColor`
 * and stay legible in both themes. Every status in this UI carries an icon
 * as well as a color — color alone would make `completed` and `failed`
 * indistinguishable with red-green color vision deficiency.
 */

interface IconProps {
  size?: number;
  className?: string;
}

function base(size: number, className?: string) {
  return {
    width: size,
    height: size,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
    className,
    "aria-hidden": true,
    focusable: false,
  };
}

export function ShieldIcon({ size = 17, className }: IconProps) {
  return (
    <svg {...base(size, className)} strokeWidth={2}>
      <path d="M12 3l7 3v6c0 4.4-3 8.2-7 9-4-.8-7-4.6-7-9V6z" />
      <path d="M9.4 12.2l1.9 1.9 3.6-3.6" />
    </svg>
  );
}

export function CheckIcon({ size = 14, className }: IconProps) {
  return (
    <svg {...base(size, className)} strokeWidth={2.6}>
      <path d="M4 12.5l5.2 5.2L20 7" />
    </svg>
  );
}

export function CrossIcon({ size = 14, className }: IconProps) {
  return (
    <svg {...base(size, className)} strokeWidth={2.6}>
      <path d="M7 7l10 10" />
      <path d="M17 7L7 17" />
    </svg>
  );
}

export function SpinnerIcon({ size = 14, className }: IconProps) {
  return (
    <svg {...base(size, className ? `spin ${className}` : "spin")} strokeWidth={3}>
      <path d="M12 3a9 9 0 1 0 9 9" />
    </svg>
  );
}

export function PendingIcon({ size = 14, className }: IconProps) {
  return (
    <svg {...base(size, className)} strokeWidth={2} strokeDasharray="3 3">
      <circle cx="12" cy="12" r="8.5" />
    </svg>
  );
}

export function DashIcon({ size = 14, className }: IconProps) {
  return (
    <svg {...base(size, className)} strokeWidth={2.4}>
      <path d="M5 12h14" />
    </svg>
  );
}

export function AlertIcon({ size = 14, className }: IconProps) {
  return (
    <svg {...base(size, className)} strokeWidth={2.2}>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 8v5" />
      <path d="M12 16.5v.01" />
    </svg>
  );
}

export function WarnIcon({ size = 15, className }: IconProps) {
  return (
    <svg {...base(size, className)} strokeWidth={2.2}>
      <path d="M12 8.5V13" />
      <path d="M12 16.5v.01" />
      <path d="M10.3 3.9L2.6 17.4A1.9 1.9 0 0 0 4.3 20.3h15.4a1.9 1.9 0 0 0 1.7-2.9L13.7 3.9a1.9 1.9 0 0 0-3.4 0z" />
    </svg>
  );
}

export function InfoIcon({ size = 14, className }: IconProps) {
  return (
    <svg {...base(size, className)} strokeWidth={2.2}>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 11v5.5" />
      <path d="M12 7.5v.01" />
    </svg>
  );
}

export function ClockIcon({ size = 14, className }: IconProps) {
  return (
    <svg {...base(size, className)} strokeWidth={2}>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7.5V12l3 2" />
    </svg>
  );
}

export function PlayIcon({ size = 13, className }: IconProps) {
  return (
    <svg {...base(size, className)} strokeWidth={2.2}>
      <path d="M7 4.5l12 7.5-12 7.5z" />
    </svg>
  );
}

export function FileIcon({ size = 12, className }: IconProps) {
  return (
    <svg {...base(size, className)} strokeWidth={2}>
      <path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z" />
      <path d="M14 3v5h5" />
    </svg>
  );
}

export function DownloadIcon({ size = 11, className }: IconProps) {
  return (
    <svg {...base(size, className)} strokeWidth={2}>
      <path d="M12 4v11" />
      <path d="M7.5 11L12 15.5 16.5 11" />
      <path d="M5 19h14" />
    </svg>
  );
}

export function SunIcon({ size = 14, className }: IconProps) {
  return (
    <svg {...base(size, className)} strokeWidth={2}>
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2.5v2M12 19.5v2M2.5 12h2M19.5 12h2M5.3 5.3l1.4 1.4M17.3 17.3l1.4 1.4M18.7 5.3l-1.4 1.4M6.7 17.3l-1.4 1.4" />
    </svg>
  );
}

export function MoonIcon({ size = 14, className }: IconProps) {
  return (
    <svg {...base(size, className)} strokeWidth={2}>
      <path d="M20 14.5A8.5 8.5 0 0 1 9.5 4a8.5 8.5 0 1 0 10.5 10.5z" />
    </svg>
  );
}

export function SystemIcon({ size = 14, className }: IconProps) {
  return (
    <svg {...base(size, className)} strokeWidth={2}>
      <rect x="3" y="4" width="18" height="12" rx="2" />
      <path d="M8 20h8" />
    </svg>
  );
}
