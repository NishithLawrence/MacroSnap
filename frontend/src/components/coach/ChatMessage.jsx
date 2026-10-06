import React from 'react';
import { Bot, User } from 'lucide-react';

/**
 * Helper to safely format Markdown text into styled React elements
 * without raw HTML injection.
 */
function renderFormattedText(text) {
  if (!text) return null;

  const paragraphs = text.split(/\n\n+/);

  return paragraphs.map((paragraph, pIdx) => {
    const lines = paragraph.split('\n');

    // Check if paragraph is a bullet list
    const isBulletList = lines.every((line) => line.trim().startsWith('- ') || line.trim().startsWith('* ') || /^\d+\.\s/.test(line.trim()));

    if (isBulletList) {
      return (
        <ul key={pIdx} className="space-y-1.5 my-1.5 list-disc list-inside text-stone-200">
          {lines.map((line, lIdx) => {
            const cleanLine = line.trim().replace(/^[-*]\s+|\d+\.\s+/, '');
            return (
              <li key={lIdx} className="leading-relaxed">
                {parseBoldText(cleanLine)}
              </li>
            );
          })}
        </ul>
      );
    }

    return (
      <p key={pIdx} className="leading-relaxed mb-2 last:mb-0">
        {lines.map((line, lIdx) => (
          <React.Fragment key={lIdx}>
            {parseBoldText(line)}
            {lIdx < lines.length - 1 && <br />}
          </React.Fragment>
        ))}
      </p>
    );
  });
}

/**
 * Parses **bold** markers safely.
 */
function parseBoldText(text) {
  const parts = text.split(/(\*\*.*?\*\*)/g);
  return parts.map((part, idx) => {
    if (part.startsWith('**') && part.endsWith('**') && part.length >= 4) {
      return (
        <strong key={idx} className="font-semibold text-white">
          {part.slice(2, -2)}
        </strong>
      );
    }
    return part;
  });
}

export default function ChatMessage({ message }) {
  const isUser = message.role === 'user';

  if (isUser) {
    return (
      <div className="flex items-end justify-end gap-2 my-2.5 pl-8 min-w-0">
        <div className="bg-red-600 text-white rounded-2xl rounded-tr-sm px-4 py-3 text-xs sm:text-sm max-w-[85%] shadow-md leading-relaxed font-normal break-words">
          {message.content}
        </div>
        <div className="w-7 h-7 rounded-xl bg-red-600/30 border border-red-500/40 text-red-300 flex items-center justify-center shrink-0 mb-0.5">
          <User size={14} />
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-start gap-2.5 my-2.5 pr-4 min-w-0">
      <div className="w-8 h-8 rounded-xl bg-red-600/20 border border-red-500/30 text-red-400 flex items-center justify-center shrink-0 mt-0.5 shadow-sm">
        <Bot size={16} />
      </div>
      <div className="flex-1 bg-stone-900/80 backdrop-blur-md border border-white/10 text-stone-200 rounded-2xl rounded-tl-sm p-3.5 text-xs sm:text-sm max-w-[88%] shadow-lg space-y-1 min-w-0 break-words">
        <div className="text-[10px] font-bold text-red-400 uppercase tracking-wider mb-1">
          MacroSnap Coach
        </div>
        <div className="text-stone-200 space-y-1.5">
          {renderFormattedText(message.content)}
        </div>
      </div>
    </div>
  );
}
