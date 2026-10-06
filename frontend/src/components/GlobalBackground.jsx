import React from 'react';

/**
 * GlobalBackground Component
 * Renders the single selected anime wallpaper cleanly across the entire app
 * with a dark gradient overlay and top vignette to eliminate top light artifacts
 * while enhancing anime character details.
 */
export default function GlobalBackground({
  imageSrc = '/assets/anime/home-bg.png',
  overlayOpacity = 0.38
}) {
  return (
    <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden bg-[#08090C]">
      {/* Anime Wallpaper Layer */}
      <div
        className="absolute inset-0 bg-cover bg-no-repeat bg-[center_top_12%] opacity-90 transition-opacity duration-300"
        style={{ backgroundImage: `url("${imageSrc}")` }}
      />

      {/* Top Vignette - Eliminates light artifacts at top edge & header */}
      <div className="absolute inset-x-0 top-0 h-28 bg-gradient-to-b from-[#08090C] via-[#08090C]/80 to-transparent z-10 pointer-events-none" />

      {/* Main Dark Tint & Gradient Overlay for UI contrast */}
      <div
        className="absolute inset-0 bg-gradient-to-b from-black/25 via-black/40 to-[#08090C]/90 z-0"
        style={{ backgroundColor: `rgba(8, 9, 12, ${overlayOpacity})` }}
      />
    </div>
  );
}
