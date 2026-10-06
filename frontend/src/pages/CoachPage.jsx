import React, { useState, useEffect, useRef } from 'react';
import { Sparkles, AlertCircle, RefreshCw } from 'lucide-react';
import CoachContext from '../components/coach/CoachContext';
import QuickActions from '../components/coach/QuickActions';
import ChatMessage from '../components/coach/ChatMessage';
import ChatComposer from '../components/coach/ChatComposer';
import CoachTyping from '../components/coach/CoachTyping';
import { getCoachContext, chatWithCoach } from '../lib/api';

const INITIAL_WELCOME_MESSAGE = {
  role: 'assistant',
  content: "Hey Nishith 👋\n\nI'm your MacroSnap Coach. Ask me about your calories, protein, meals, or what to eat next.",
};

export default function CoachPage() {
  const [messages, setMessages] = useState([INITIAL_WELCOME_MESSAGE]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [contextData, setContextData] = useState(null);
  const [lastPrompt, setLastPrompt] = useState('');

  const chatEndRef = useRef(null);

  // Auto-scroll chat to bottom on new messages
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading, error]);

  // Load live today's context on mount
  useEffect(() => {
    async function loadContext() {
      try {
        const data = await getCoachContext();
        setContextData(data);
      } catch (err) {
        console.error('Failed to load coach context:', err);
        // Fallback default context if API is unreachable
        setContextData({
          target_calories: 2380,
          consumed_calories: 1840,
          remaining_calories: 540,
          target_protein: 144,
          consumed_protein: 82,
          remaining_protein: 62,
        });
      }
    }
    loadContext();
  }, []);

  const handleSendMessage = async (promptText) => {
    const textToSend = promptText || input;
    if (!textToSend || !textToSend.trim() || isLoading) return;

    setError(null);
    setLastPrompt(textToSend.trim());

    // Append user message
    const userMsg = { role: 'user', content: textToSend.trim() };
    const updatedMessages = [...messages, userMsg];
    setMessages(updatedMessages);
    setInput('');
    setIsLoading(true);

    try {
      // Send message with conversation history (excluding initial greeting for clean token usage)
      const apiHistory = updatedMessages.slice(1).map((m) => ({
        role: m.role,
        content: m.content,
      }));

      const res = await chatWithCoach(textToSend.trim(), apiHistory);

      if (res && res.success) {
        const assistantMsg = { role: 'assistant', content: res.response };
        setMessages((prev) => [...prev, assistantMsg]);
      } else {
        setError(res?.error || 'Coach is temporarily unavailable.');
      }
    } catch (err) {
      console.error('Error querying Coach:', err);
      setError('Coach is temporarily unavailable.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRetry = () => {
    if (lastPrompt) {
      setError(null);
      handleSendMessage(lastPrompt);
    }
  };

  return (
    <div className="space-y-4 min-w-0 pb-2">
      {/* 1. Header Section */}
      <div className="space-y-0.5">
        <h1 className="text-red-500 font-extrabold text-sm tracking-wider uppercase">
          MACROSNAP COACH
        </h1>
        <p className="text-xs text-stone-400 font-medium">
          Your personalized nutrition assistant
        </p>
      </div>

      {/* 2. Today's Live Context Summary */}
      <CoachContext contextData={contextData} />

      {/* 3. Predefined Quick Action Chips */}
      <QuickActions onSelectPrompt={handleSendMessage} disabled={isLoading} />

      {/* 4. Chat Messages Area (Unbordered continuous chat area) */}
      <div className="space-y-2 pt-1 min-w-0">
        <div className="text-[11px] font-bold uppercase tracking-wider text-stone-400 px-0.5">
          Conversation
        </div>

        <div className="space-y-2.5 py-1 min-w-0">
          {messages.map((msg, index) => (
            <ChatMessage key={index} message={msg} />
          ))}

          {isLoading && <CoachTyping />}

          {error && (
            <div className="my-2.5 bg-red-950/80 border border-red-500/40 rounded-xl p-3 text-xs text-red-200 flex flex-wrap sm:flex-nowrap items-center justify-between gap-2.5 shadow-md">
              <div className="flex items-center gap-2 min-w-0 flex-1">
                <AlertCircle size={16} className="text-red-400 shrink-0" />
                <span className="leading-tight break-words font-medium">{error}</span>
              </div>
              <button
                type="button"
                onClick={handleRetry}
                className="bg-red-600 hover:bg-red-500 text-white font-bold text-[11px] px-3 py-1.5 rounded-lg flex items-center gap-1 shrink-0 active:scale-95 transition-transform ml-auto"
              >
                <RefreshCw size={12} /> Try Again
              </button>
            </div>
          )}

          <div ref={chatEndRef} />
        </div>
      </div>

      {/* 5. Message Input Composer (Visual anchor with subtle dark backdrop) */}
      <div className="sticky bottom-0 pt-2 pb-1 bg-gradient-to-t from-stone-950/90 via-stone-950/60 to-transparent backdrop-blur-sm">
        <ChatComposer
          value={input}
          onChange={setInput}
          onSubmit={handleSendMessage}
          disabled={isLoading}
        />
      </div>
    </div>
  );
}
