import React, { useRef } from 'react';
import { Camera, Image as ImageIcon, Sparkles } from 'lucide-react';

export default function PhotoCapture({ onPhotoSelected }) {
  const cameraInputRef = useRef(null);
  const galleryInputRef = useRef(null);

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      onPhotoSelected(file);
    }
  };

  return (
    <div className="space-y-4 min-w-0">
      {/* Hidden native file inputs for camera & gallery */}
      <input
        type="file"
        ref={cameraInputRef}
        accept="image/*"
        capture="environment"
        onChange={handleFileChange}
        className="hidden"
      />
      <input
        type="file"
        ref={galleryInputRef}
        accept="image/*"
        onChange={handleFileChange}
        className="hidden"
      />

      {/* Viewfinder Empty State Container */}
      <div className="bg-[#111318]/85 backdrop-blur-md border border-white/[0.08] rounded-[20px] p-6 text-center space-y-4 relative overflow-hidden shadow-2xl">
        {/* Subtle Frame Corners */}
        <div className="absolute top-4 left-4 w-6 h-6 border-t-2 border-l-2 border-[#FF2B3A]/60 rounded-tl-sm pointer-events-none" />
        <div className="absolute top-4 right-4 w-6 h-6 border-t-2 border-r-2 border-[#FF2B3A]/60 rounded-tr-sm pointer-events-none" />
        <div className="absolute bottom-4 left-4 w-6 h-6 border-b-2 border-l-2 border-[#FF2B3A]/60 rounded-bl-sm pointer-events-none" />
        <div className="absolute bottom-4 right-4 w-6 h-6 border-b-2 border-r-2 border-[#FF2B3A]/60 rounded-br-sm pointer-events-none" />

        <div className="w-16 h-16 rounded-2xl bg-[#FF2B3A]/10 border border-[#FF2B3A]/25 flex items-center justify-center text-[#FF2B3A] mx-auto shadow-inner mt-2">
          <Camera size={30} strokeWidth={2} />
        </div>

        <div className="space-y-1">
          <h2 className="text-[17px] font-bold text-[#F5F5F5] tracking-tight">
            SNAP YOUR MEAL
          </h2>
          <p className="text-[13px] text-[#9297A3] max-w-[260px] mx-auto leading-relaxed">
            Show us what's on your plate to automatically estimate calories and macros.
          </p>
        </div>

        {/* Primary & Secondary Action Buttons */}
        <div className="pt-2 space-y-2.5">
          <button
            type="button"
            onClick={() => cameraInputRef.current?.click()}
            className="w-full h-[52px] bg-[#FF2B3A] hover:bg-[#E02231] active:scale-[0.99] text-white font-bold text-[14px] tracking-wide rounded-[16px] shadow-lg shadow-[#FF2B3A]/25 transition-all duration-150 flex items-center justify-center gap-2 focus:outline-none"
          >
            <Camera size={19} strokeWidth={2.2} />
            <span>TAKE PHOTO</span>
          </button>

          <button
            type="button"
            onClick={() => galleryInputRef.current?.click()}
            className="w-full py-2.5 text-[13px] text-[#9297A3] hover:text-[#F5F5F5] font-medium transition-colors flex items-center justify-center gap-1.5 focus:outline-none"
          >
            <ImageIcon size={15} />
            <span>Upload from gallery</span>
          </button>
        </div>
      </div>
    </div>
  );
}
