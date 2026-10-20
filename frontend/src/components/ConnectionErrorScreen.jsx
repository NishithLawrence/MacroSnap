import React, { useState } from 'react';
import { WifiOff, RefreshCw, ExternalLink } from 'lucide-react';

export default function ConnectionErrorScreen({ error, onRetry }) {
  const [retrying, setRetrying] = useState(false);

  const handleRetry = async () => {
    setRetrying(true);
    try {
      if (onRetry) await onRetry();
    } finally {
      setRetrying(false);
    }
  };

  return (
    <div className="min-h-[70vh] flex items-center justify-center p-4">
      <div className="app-card p-6 max-w-sm w-full text-center space-y-5 border border-red-500/20 bg-zinc-900/80 shadow-2xl">
        <div className="w-16 h-16 mx-auto rounded-2xl bg-red-500/10 border border-red-500/30 flex items-center justify-center text-[#EF233C] shadow-lg shadow-red-500/10">
          <WifiOff size={28} />
        </div>

        <div className="space-y-2">
          <h2 className="text-lg font-bold text-white tracking-tight">
            Backend Connection Failed
          </h2>
          <p className="text-xs text-zinc-400 leading-relaxed">
            Unable to establish a secure connection to the MacroSnap API server.
            If the server is waking up on Render, it may take 30–50 seconds to respond.
          </p>
        </div>

        <div className="p-3 bg-black/40 rounded-xl border border-white/5 text-[11px] text-zinc-400 font-mono break-all text-left space-y-1">
          <div className="text-[10px] uppercase text-zinc-500 font-bold">API Endpoint</div>
          <div className="text-zinc-300">https://macrosnap-backend-esq0.onrender.com</div>
          {error && (
            <div className="text-red-400/90 pt-1 text-[10px] border-t border-white/5">
              {String(error)}
            </div>
          )}
        </div>

        <div className="space-y-2 pt-2">
          <button
            onClick={handleRetry}
            disabled={retrying}
            className="w-full py-3 px-4 rounded-xl bg-[#EF233C] hover:bg-[#D90429] disabled:opacity-50 text-white text-xs font-bold flex items-center justify-center gap-2 shadow-lg shadow-[#EF233C]/25 transition-all active:scale-95"
          >
            <RefreshCw size={15} className={retrying ? 'animate-spin' : ''} />
            <span>{retrying ? 'Reconnecting...' : 'Retry Connection'}</span>
          </button>

          <a
            href="https://macrosnap-backend-esq0.onrender.com/docs"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 text-[11px] text-zinc-400 hover:text-zinc-200 transition-colors pt-1"
          >
            <span>Open API Swagger Docs</span>
            <ExternalLink size={12} />
          </a>
        </div>
      </div>
    </div>
  );
}
