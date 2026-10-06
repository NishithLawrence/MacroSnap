import React from 'react';

export default function Greeting({ userName = 'Nishith' }) {
  return (
    <div className="mt-5 mb-6 space-y-1">
      <h1 className="text-[24px] font-bold text-[#F5F5F5] tracking-tight leading-tight">
        Good evening, {userName}
      </h1>
      <p className="text-[14px] text-[#9297A3] font-normal">
        Let's stay on target today.
      </p>
    </div>
  );
}
