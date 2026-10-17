import React, { useEffect, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Calendar, Utensils, Camera, RefreshCw, AlertCircle } from 'lucide-react';
import { getMealHistory, deleteMeal, updateMeal } from '../lib/api';
import HistoryDateGroup from '../components/HistoryDateGroup';
import DeleteMealDialog from '../components/DeleteMealDialog';
import EditMealModal from '../components/EditMealModal';

export default function HistoryPage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [dateGroups, setDateGroups] = useState([]);

  // Dialog state
  const [mealToDelete, setMealToDelete] = useState(null);
  const [mealToEdit, setMealToEdit] = useState(null);

  const fetchHistory = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getMealHistory();
      setDateGroups(res.dates || []);
    } catch (err) {
      console.error('Failed to load meal history:', err);
      setError(err.message || 'Unable to fetch meal history.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const handleConfirmDelete = async (mealId) => {
    // Perform real backend deletion
    await deleteMeal(mealId);

    // Update UI state immediately after successful deletion
    setDateGroups((prevGroups) => {
      return prevGroups
        .map((group) => {
          const updatedMeals = group.meals.filter((m) => m.meal_id !== mealId);
          // Recalculate daily totals for group
          const totals = updatedMeals.reduce(
            (acc, m) => {
              const t = m.total || {};
              acc.calories += t.calories || 0;
              acc.protein_g += t.protein_g || 0;
              acc.carbs_g += t.carbs_g || 0;
              acc.fat_g += t.fat_g || 0;
              return acc;
            },
            { calories: 0, protein_g: 0, carbs_g: 0, fat_g: 0 }
          );
          return {
            ...group,
            meals: updatedMeals,
            totals,
          };
        })
        .filter((group) => group.meals.length > 0);
    });
  };

  const handleSaveEdit = async (mealId, updatedMeal) => {
    await updateMeal(mealId, updatedMeal);

    // Refresh history from backend to ensure authoritative data consistency
    await fetchHistory();
  };

  const totalMealCount = dateGroups.reduce((acc, g) => acc + (g.meals || []).length, 0);

  return (
    <div className="space-y-5 min-w-0 pb-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">Meal History</h1>
          <p className="text-xs text-zinc-400 mt-0.5">Past logged meals and daily summaries</p>
        </div>
        <div className="p-2 rounded-xl bg-zinc-900 border border-white/5 text-[#EF233C]">
          <Calendar size={18} />
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertCircle size={16} className="shrink-0 text-rose-400" />
            <span>{error}</span>
          </div>
          <button
            type="button"
            onClick={fetchHistory}
            className="px-2.5 py-1 bg-rose-500/20 hover:bg-rose-500/30 text-rose-200 font-semibold rounded-lg transition-colors"
          >
            Retry
          </button>
        </div>
      )}

      {/* Loading Skeleton */}
      {loading && dateGroups.length === 0 && (
        <div className="app-card p-8 text-center space-y-3">
          <RefreshCw size={24} className="animate-spin text-[#EF233C] mx-auto" />
          <p className="text-xs font-semibold text-zinc-400">Loading meal history...</p>
        </div>
      )}

      {/* Empty State when no meals exist */}
      {!loading && totalMealCount === 0 && (
        <div className="app-card p-8 text-center space-y-4">
          <div className="w-14 h-14 rounded-full bg-zinc-900 border border-white/10 flex items-center justify-center text-zinc-400 mx-auto shadow-inner">
            <Utensils size={26} className="text-[#EF233C]" />
          </div>
          <div className="space-y-1 max-w-[280px] mx-auto">
            <h2 className="text-sm font-bold text-white">No Meals Logged Yet</h2>
            <p className="text-xs text-zinc-400">
              Start tracking your nutrition by scanning a meal photo or logging your first meal.
            </p>
          </div>
          <div className="pt-2">
            <Link
              to="/snap"
              className="inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-[#EF233C] to-[#9D0208] text-white text-xs font-bold shadow-lg shadow-[#EF233C]/20 hover:opacity-90 transition-opacity"
            >
              <Camera size={16} />
              <span>Go to Snap</span>
            </Link>
          </div>
        </div>
      )}

      {/* Meal Date Groups List */}
      {!loading && dateGroups.length > 0 && (
        <div className="space-y-4">
          {dateGroups.map((group) => (
            <HistoryDateGroup
              key={group.date}
              dateGroup={group}
              onEditMeal={(m) => setMealToEdit(m)}
              onDeleteMeal={(m) => setMealToDelete(m)}
            />
          ))}
        </div>
      )}

      {/* Delete Confirmation Dialog */}
      <DeleteMealDialog
        meal={mealToDelete}
        isOpen={Boolean(mealToDelete)}
        onClose={() => setMealToDelete(null)}
        onConfirmDelete={handleConfirmDelete}
      />

      {/* Edit Meal Modal */}
      <EditMealModal
        meal={mealToEdit}
        isOpen={Boolean(mealToEdit)}
        onClose={() => setMealToEdit(null)}
        onSave={handleSaveEdit}
      />
    </div>
  );
}
