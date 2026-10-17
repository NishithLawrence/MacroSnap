import React, { useState } from 'react';
import { Edit2, X, Plus, Trash2 } from 'lucide-react';

export default function EditMealModal({ meal, isOpen, onClose, onSave }) {
  const [mealType, setMealType] = useState(meal?.meal_type || 'Lunch');
  const [foods, setFoods] = useState(
    meal?.foods && meal.foods.length
      ? meal.foods.map((f) => ({ ...f }))
      : [{ id: '1', name: '', portion: '', calories: 0, protein_g: 0, carbs_g: 0, fat_g: 0 }]
  );
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  // Sync state when editing a new meal
  React.useEffect(() => {
    if (meal) {
      setMealType(meal.meal_type || 'Lunch');
      setFoods(
        meal.foods && meal.foods.length
          ? meal.foods.map((f) => ({ ...f }))
          : [{ id: '1', name: '', portion: '', calories: 0, protein_g: 0, carbs_g: 0, fat_g: 0 }]
      );
      setError(null);
    }
  }, [meal]);

  if (!isOpen || !meal) return null;


  const handleFoodChange = (idx, field, val) => {
    const next = [...foods];
    if (field === 'name' || field === 'portion') {
      next[idx][field] = val;
    } else {
      const num = parseFloat(val);
      next[idx][field] = isNaN(num) ? 0 : Math.max(0, num);
    }
    setFoods(next);
  };

  const handleAddFood = () => {
    setFoods([
      ...foods,
      { id: `item_${Date.now()}`, name: '', portion: '', calories: 0, protein_g: 0, carbs_g: 0, fat_g: 0 },
    ]);
  };

  const handleRemoveFood = (idx) => {
    if (foods.length <= 1) return;
    setFoods(foods.filter((_, i) => i !== idx));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    // Validate foods
    for (let i = 0; i < foods.length; i++) {
      if (!foods[i].name || !foods[i].name.trim()) {
        setError(`Food item #${i + 1} must have a name.`);
        return;
      }
    }

    const updated = {
      ...meal,
      meal_type: mealType,
      foods: foods.map((f) => ({
        id: f.id || `item_${Math.random()}`,
        name: f.name.trim(),
        portion: f.portion ? f.portion.trim() : '',
        calories: Math.round(f.calories || 0),
        protein_g: Math.round(f.protein_g || 0),
        carbs_g: Math.round(f.carbs_g || 0),
        fat_g: Math.round(f.fat_g || 0),
      })),
    };

    setSaving(true);
    try {
      await onSave(meal.meal_id, updated);
      onClose();
    } catch (err) {
      console.error('Failed to update meal:', err);
      setError(err.message || 'Failed to save meal changes.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fadeIn">
      <div className="bg-[#13131A] border border-white/10 rounded-2xl p-5 max-w-md w-full space-y-4 shadow-2xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between border-b border-white/5 pb-3">
          <div className="flex items-center gap-2 font-bold text-sm text-white">
            <Edit2 size={16} className="text-[#EF233C]" />
            <span>Edit Meal Details</span>
          </div>
          <button
            type="button"
            onClick={onClose}
            disabled={saving}
            className="p-1 rounded-lg text-zinc-400 hover:text-white transition-colors"
          >
            <X size={16} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4 text-xs">
          {/* Meal Type Selection */}
          <div>
            <label className="block text-[10px] text-zinc-400 font-semibold mb-1">Meal Category</label>
            <div className="grid grid-cols-4 gap-1.5">
              {['Breakfast', 'Lunch', 'Dinner', 'Snack'].map((type) => (
                <button
                  key={type}
                  type="button"
                  onClick={() => setMealType(type)}
                  className={`py-1.5 px-2 rounded-xl text-[11px] font-semibold border transition-colors ${
                    mealType === type
                      ? 'bg-[#EF233C] text-white border-[#EF233C]'
                      : 'bg-zinc-900 text-zinc-400 border-white/5 hover:text-white'
                  }`}
                >
                  {type}
                </button>
              ))}
            </div>
          </div>

          {/* Food Items List */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-[10px] text-zinc-400 font-semibold uppercase">Food Items</label>
              <button
                type="button"
                onClick={handleAddFood}
                className="text-[10px] text-[#EF233C] font-semibold flex items-center gap-1 hover:underline"
              >
                <Plus size={12} /> Add Item
              </button>
            </div>

            {foods.map((food, idx) => (
              <div key={idx} className="p-3 bg-zinc-900/60 rounded-xl border border-white/5 space-y-2 relative">
                {foods.length > 1 && (
                  <button
                    type="button"
                    onClick={() => handleRemoveFood(idx)}
                    className="absolute top-2 right-2 p-1 text-zinc-500 hover:text-rose-400"
                    title="Remove item"
                  >
                    <Trash2 size={13} />
                  </button>
                )}

                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="text-[9px] text-zinc-500 block">Food Name</label>
                    <input
                      type="text"
                      value={food.name}
                      onChange={(e) => handleFoodChange(idx, 'name', e.target.value)}
                      placeholder="e.g. Grilled Chicken"
                      className="w-full px-2 py-1 bg-black/40 border border-white/10 rounded-lg text-xs text-white"
                    />
                  </div>
                  <div>
                    <label className="text-[9px] text-zinc-500 block">Portion</label>
                    <input
                      type="text"
                      value={food.portion}
                      onChange={(e) => handleFoodChange(idx, 'portion', e.target.value)}
                      placeholder="e.g. 150g"
                      className="w-full px-2 py-1 bg-black/40 border border-white/10 rounded-lg text-xs text-white"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-4 gap-1.5 text-center">
                  <div>
                    <label className="text-[9px] text-zinc-500 block">Calories</label>
                    <input
                      type="number"
                      value={food.calories}
                      onChange={(e) => handleFoodChange(idx, 'calories', e.target.value)}
                      className="w-full px-1.5 py-1 bg-black/40 border border-white/10 rounded-lg text-xs text-center text-white"
                    />
                  </div>
                  <div>
                    <label className="text-[9px] text-sky-400 block">Protein (g)</label>
                    <input
                      type="number"
                      value={food.protein_g}
                      onChange={(e) => handleFoodChange(idx, 'protein_g', e.target.value)}
                      className="w-full px-1.5 py-1 bg-black/40 border border-white/10 rounded-lg text-xs text-center text-white"
                    />
                  </div>
                  <div>
                    <label className="text-[9px] text-amber-400 block">Carbs (g)</label>
                    <input
                      type="number"
                      value={food.carbs_g}
                      onChange={(e) => handleFoodChange(idx, 'carbs_g', e.target.value)}
                      className="w-full px-1.5 py-1 bg-black/40 border border-white/10 rounded-lg text-xs text-center text-white"
                    />
                  </div>
                  <div>
                    <label className="text-[9px] text-rose-400 block">Fat (g)</label>
                    <input
                      type="number"
                      value={food.fat_g}
                      onChange={(e) => handleFoodChange(idx, 'fat_g', e.target.value)}
                      className="w-full px-1.5 py-1 bg-black/40 border border-white/10 rounded-lg text-xs text-center text-white"
                    />
                  </div>
                </div>
              </div>
            ))}
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
              disabled={saving}
              className="px-3.5 py-1.5 rounded-xl bg-zinc-900 border border-white/10 font-semibold text-zinc-300 hover:text-white"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving}
              className="px-4 py-1.5 rounded-xl bg-[#EF233C] text-white font-bold hover:bg-[#d90429] disabled:opacity-50"
            >
              {saving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
