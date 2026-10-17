import React from 'react';
import { useLocation } from 'react-router-dom';
import AppHeader from './AppHeader';
import BottomNav from './BottomNav';
import GlobalBackground from './GlobalBackground';

export default function MobileShell({ children }) {
  const location = useLocation();

  const getWallpaperForPath = (path) => {
    if (path.startsWith('/snap')) return '/assets/anime/snap-bg.png';
    if (path.startsWith('/coach')) return '/assets/anime/coach-bg.png';
    if (path.startsWith('/progress')) return '/assets/anime/progress-bg.png';
    if (path.startsWith('/history')) return '/assets/anime/history-bg.png';
    if (path.startsWith('/profile')) return '/assets/anime/profile-bg.png';
    return '/assets/anime/home-bg.png';
  };

  const bgImage = getWallpaperForPath(location.pathname);

  return (
    <div className="w-full h-screen h-[100dvh] bg-[#040406] flex justify-center items-center antialiased selection:bg-[#FF2B3A]/30 selection:text-white overflow-hidden">
      {/* Centered Mobile Viewport Container */}
      <div className="w-full max-w-[440px] h-full bg-[#08090C] text-[#F5F5F5] flex flex-col relative border-x border-white/[0.05] shadow-2xl overflow-hidden min-w-0">
        {/* Dynamic Global Artwork mapped to active section */}
        <GlobalBackground imageSrc={bgImage} overlayOpacity={0.36} />

        {/* Top Header (shrink-0) */}
        <div className="relative z-20 shrink-0">
          <AppHeader />
        </div>

        {/* Dedicated Scrollable Main Area (flex-1 min-h-0 overflow-y-auto) with pb-12 padding */}
        <main className="relative z-10 flex-1 min-h-0 overflow-y-auto overflow-x-hidden px-4 pt-4 pb-12 space-y-6">
          {children}
        </main>

        {/* Dedicated Bottom Navigation Region (shrink-0) */}
        <div className="relative z-30 shrink-0">
          <BottomNav />
        </div>
      </div>
    </div>
  );
}

