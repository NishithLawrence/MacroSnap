import React from 'react';

/**
 * Revelation brand logo mark.
 * Clean, geometric monogram 'R' engineered with precision angles,
 * a faceted silver body, and an electric-red performance speed blade.
 *
 * @param {Object} props
 * @param {number} [props.size=24] - Size in pixels (width & height).
 * @param {string} [props.className=''] - Additional CSS classes.
 * @param {'accent'|'white'} [props.variant='accent'] - 'accent' uses electric-red speed blade; 'white' uses crisp monochrome silver/white.
 */
export default function RevelationLogo({ size = 24, className = '', variant = 'accent' }) {
  const isWhite = variant === 'white';

  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 40 40"
      width={size}
      height={size}
      fill="none"
      className={className}
      aria-label="Revelation Logo"
      role="img"
    >
      <defs>
        <linearGradient id={`rev-silver-${size}-${variant}`} x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#FFFFFF" />
          <stop offset="60%" stopColor="#E2E8F0" />
          <stop offset="100%" stopColor={isWhite ? '#F1F5F9' : '#94A3B8'} />
        </linearGradient>
        <linearGradient id={`rev-red-${size}-${variant}`} x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#FF4D5A" />
          <stop offset="100%" stopColor="#EF233C" />
        </linearGradient>
      </defs>

      {/* Stem */}
      <path
        d="M 9 8.5 C 8.45 8.5 8 8.95 8 9.5 L 8 30.5 C 8 31.05 8.45 31.5 9 31.5 L 14 31.5 C 14.55 31.5 15 31.05 15 30.5 L 15 9.5 C 15 8.95 14.55 8.5 14 8.5 Z"
        fill={`url(#rev-silver-${size}-${variant})`}
      />

      {/* Upper Loop */}
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M 14 8.5 L 24.5 8.5 C 28.92 8.5 32.5 11.63 32.5 15.5 C 32.5 19.37 28.92 22.5 24.5 22.5 L 14 22.5 L 14 8.5 Z M 19 12.8 L 24 12.8 C 25.66 12.8 27 13.92 27 15.5 C 27 17.08 25.66 18.2 24 18.2 L 19 18.2 L 19 12.8 Z"
        fill={`url(#rev-silver-${size}-${variant})`}
      />

      {/* Dynamic Speed Blade (Kick) */}
      <path
        d="M 18.5 19.8 L 24 19.8 L 32.3 31.2 C 32.7 31.7 32.3 32 31.6 32 L 26.2 32 C 25.6 32 25.1 31.6 24.7 31.1 L 18.5 22 Z"
        fill={isWhite ? '#FFFFFF' : `url(#rev-red-${size}-${variant})`}
      />
    </svg>
  );
}
