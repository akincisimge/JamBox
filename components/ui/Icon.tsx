const icons = {
  plus: <path d="M12 5v14M5 12h14" />,
  hash: <path d="M10 3 8 21M16 3l-2 18M4 9h16M3 15h16" />,
  users: (
    <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8ZM22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" />
  ),
  play: <path d="m9 7 8 5-8 5V7Z" />,
  pause: <path d="M9 7v10M15 7v10" />,
  send: <path d="m4 4 17 8-17 8 4-8-4-8Zm4 8h13" />,
  arrow: <path d="M5 12h14M13 6l6 6-6 6" />,
  close: <path d="m6 6 12 12M18 6 6 18" />,
  copy: (
    <>
      <rect x="8" y="8" width="11" height="11" rx="2" />
      <path d="M16 8V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h2" />
    </>
  ),
};

export type IconName = keyof typeof icons;

export function Icon({ name, size = 22 }: { name: IconName; size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {icons[name]}
    </svg>
  );
}
