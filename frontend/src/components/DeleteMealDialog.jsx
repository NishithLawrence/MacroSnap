import React, { useState } from 'react';
import { AlertTriangle, Trash2, X } from 'lucide-react';

export default function DeleteMealDialog({ meal, isOpen, onClose, onConfirmDelete }) {
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState(null);

  if (!isOpen || !meal) return null;

  const handleDelete = async () => {
    setError(null);
    setDeleting(true);
    try {
      await onConfirmDelete(meal.meal_id);
      onClose();
    } catch (err) {
      console.error('Failed to delete meal:', err);
      setError(err.message || 'Failed to delete meal from server.');
    } finally {
      setDeleting(false);
    }
  };

  const mealTitle = meal.meal_type || 'Meal';
  const foodNames = (meal.foods || []).map((f) => f.name).join(', ') || 'Logged meal';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fadeIn">
      <div className="bg-[#13131A] border border-white/10 rounded-2xl p-5 max-w-sm w-full space-y-4 shadow-2xl">
        <div className="flex items-center justify-between border-b border-white/5 pb-3">
          <div className="flex items-center gap-2 text-rose-500 font-bold text-sm">
            <AlertTriangle size={18} />
            <span>Confirm Meal Deletion</span>
          </div>
          <button
            type="button"
            onClick={onClose}
            disabled={deleting}
            className="p-1 rounded-lg text-zinc-400 hover:text-white transition-colors"
          >
            <X size={16} />
          </button>
        </div>

        <div className="space-y-2 text-xs">
          <p className="text-zinc-300">
            Are you sure you want to delete this <span className="font-bold text-white">{mealTitle}</span>?
          </p>
          <div className="p-2.5 rounded-xl bg-zinc-900/80 border border-white/5 text-[11px] text-zinc-400">
            <p className="font-semibold text-zinc-200 truncate">{foodNames}</p>
            <p className="text-[10px] text-[#EF233C] mt-0.5 font-bold">{meal.total?.calories || meal.calories || 0} kcal</p>
          </div>
        </div>

        {error && (
          <div className="p-2.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-[11px]">
            {error}
          </div>
        )}

        <div className="flex items-center justify-end gap-2 pt-2 border-t border-white/5">
          <button
            type="button"
            onClick={onClose}
            disabled={deleting}
            className="px-3.5 py-1.5 rounded-xl bg-zinc-900 border border-white/10 text-xs font-semibold text-zinc-300 hover:text-white transition-colors"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleDelete}
            disabled={deleting}
            className="px-3.5 py-1.5 rounded-xl bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold transition-colors flex items-center gap-1.5 disabled:opacity-50"
          >
            <Trash2 size={14} />
            <span>{deleting ? 'Deleting...' : 'Delete Meal'}</span>
          </button>
        </div>
      </div>
    </div>
  );
}
