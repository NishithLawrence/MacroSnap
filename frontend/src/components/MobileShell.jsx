import React from 'react';
import AppHeader from './AppHeader';
import BottomNav from './BottomNav';
import GlobalBackground from './GlobalBackground';

export default function MobileShell({ children }) {
  return (
    <div className="w-full h-screen h-[100dvh] bg-[#040406] flex justify-center items-center antialiased selection:bg-[#FF2B3A]/30 selection:text-white overflow-hidden">
      {/* Centered Mobile Viewport Container */}
      <div className="w-full max-w-[440px] h-full bg-[#08090C] text-[#F5F5F5] flex flex-col relative border-x border-white/[0.05] shadow-2xl overflow-hidden min-w-0">
        {/* Single Global Anime Wallpaper */}
        <GlobalBackground imageSrc="/assets/anime/home-bg.png" overlayOpacity={0.36} />

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
