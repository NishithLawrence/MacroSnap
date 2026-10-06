import React, { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, CheckCircle, AlertCircle, ArrowLeft, RotateCcw } from 'lucide-react';

import MealTypeSelector from '../components/snap/MealTypeSelector';
import PhotoCapture from '../components/snap/PhotoCapture';
import PhotoPreview from '../components/snap/PhotoPreview';
import ScanProgress from '../components/snap/ScanProgress';
import FoodResult from '../components/snap/FoodResult';
import MealTotal from '../components/snap/MealTotal';
import MealDisclaimer from '../components/snap/MealDisclaimer';

import { scanMeal, createMeal } from '../lib/api';

export default function SnapPage() {
  const navigate = useNavigate();

  // Single State Status Machine: EMPTY | PHOTO_SELECTED | ANALYZING | RESULTS | SAVING | SUCCESS | ERROR
  const [status, setStatus] = useState('EMPTY');
  const [mealType, setMealType] = useState('Lunch');
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [foods, setFoods] = useState([]);
  const [errorMessage, setErrorMessage] = useState('');

  // Handle Photo Selection
  const handlePhotoSelected = (file) => {
    setSelectedFile(file);
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
    setStatus('PHOTO_SELECTED');
    setErrorMessage('');
  };

  // Reset to Empty
  const handleReset = () => {
    setSelectedFile(null);
    setPreviewUrl(null);
    setFoods([]);
    setStatus('EMPTY');
    setErrorMessage('');
  };

  // Trigger AI Scanning API
  const handleAnalyze = async () => {
    if (!selectedFile) return;

    setStatus('ANALYZING');
    setErrorMessage('');

    try {
      const data = await scanMeal(selectedFile, mealType);
      if (data && data.foods) {
        setFoods(data.foods);
        setStatus('RESULTS');
      } else {
        throw new Error('No foods detected in image.');
      }
    } catch (err) {
      console.error('Scan error:', err);
      setErrorMessage(err.message || 'Unable to analyze this meal.');
      setStatus('ERROR');
    }
  };

  // Food row update handler
  const handleFoodChange = (index, updatedFood) => {
    const updated = [...foods];
    updated[index] = updatedFood;
    setFoods(updated);
  };

  // Remove food item handler
  const handleFoodDelete = (index) => {
    const updated = foods.filter((_, i) => i !== index);
    setFoods(updated);
  };

  // Add manual food item
  const handleAddFood = () => {
    const newItem = {
      id: `manual_${Date.now()}`,
      name: 'Custom Item',
      portion: '1 serving',
      calories: 150,
      protein_g: 10,
      carbs_g: 15,
      fat_g: 5,
      confidence: 'high',
    };
    setFoods([...foods, newItem]);
  };

  // Recalculate totals dynamically from current foods array
  const computedTotal = useMemo(() => {
    return foods.reduce(
      (acc, item) => ({
        calories: acc.calories + (Number(item.calories) || 0),
        protein_g: acc.protein_g + (Number(item.protein_g) || 0),
        carbs_g: acc.carbs_g + (Number(item.carbs_g) || 0),
        fat_g: acc.fat_g + (Number(item.fat_g) || 0),
      }),
      { calories: 0, protein_g: 0, carbs_g: 0, fat_g: 0 }
    );
  }, [foods]);

  // Confirm & Log Meal
  const handleConfirmAndSave = async () => {
    if (foods.length === 0) return;

    setStatus('SAVING');
    try {
      const mealPayload = {
        meal_type: mealType,
        foods: foods,
        total: computedTotal,
        name: foods.map((f) => f.name).join(', ') || 'Logged Meal',
        calories: computedTotal.calories,
        protein: computedTotal.protein_g,
        carbs: computedTotal.carbs_g,
        fat: computedTotal.fat_g,
      };

      await createMeal(mealPayload);
      setStatus('SUCCESS');
    } catch (err) {
      console.error('Save error:', err);
      setErrorMessage(err.message || 'Failed to save meal to tracker.');
      setStatus('ERROR');
    }
  };

  return (
    <div className="space-y-5 min-w-0">
      {/* Header Bar */}
      <div>
        <h1 className="text-xl font-bold text-[#F5F5F5] tracking-tight">Snap Scanner</h1>
        <p className="text-xs text-[#9297A3] mt-0.5">AI Vision nutrition estimation</p>
      </div>

      {/* 1. Meal Type Selector (Visible during photo selection & empty states) */}
      {(status === 'EMPTY' || status === 'PHOTO_SELECTED') && (
        <MealTypeSelector selected={mealType} onChange={setMealType} />
      )}

      {/* 2. State: EMPTY */}
      {status === 'EMPTY' && <PhotoCapture onPhotoSelected={handlePhotoSelected} />}

      {/* 3. State: PHOTO_SELECTED */}
      {status === 'PHOTO_SELECTED' && previewUrl && (
        <PhotoPreview
          imageSrc={previewUrl}
          onRetake={handleReset}
          onAnalyze={handleAnalyze}
        />
      )}

      {/* 4. State: ANALYZING */}
      {status === 'ANALYZING' && <ScanProgress imageSrc={previewUrl} />}

      {/* 5. State: RESULTS or SAVING */}
      {(status === 'RESULTS' || status === 'SAVING') && (
        <div className="space-y-4 min-w-0">
          {/* Small Image Thumbnail Header */}
          <div className="bg-[#111318]/85 backdrop-blur-md border border-white/[0.08] p-3 rounded-2xl flex items-center gap-3">
            {previewUrl && (
              <img
                src={previewUrl}
                alt="Meal Thumbnail"
                className="w-14 h-14 rounded-xl object-cover border border-white/10 shrink-0"
              />
            )}
            <div className="flex-1 min-w-0">
              <span className="text-[10px] font-bold uppercase tracking-wider text-[#FF2B3A] block">
                {mealType}
              </span>
              <h2 className="text-[14px] font-bold text-[#F5F5F5] truncate">
                {foods.length > 0 ? foods[0].name : 'Detected Meal'}
              </h2>
              <span className="text-[11px] text-[#9297A3]">
                {foods.length} {foods.length === 1 ? 'item detected' : 'items detected'}
              </span>
            </div>
          </div>

          {/* Detected Foods List */}
          <div className="space-y-2.5">
            <div className="flex items-center justify-between">
              <h3 className="text-[14px] font-semibold text-[#F5F5F5]">Detected Foods</h3>
              <button
                type="button"
                onClick={handleAddFood}
                className="text-[12px] text-[#FF2B3A] hover:underline font-semibold inline-flex items-center gap-1 focus:outline-none"
              >
                <Plus size={14} />
                <span>Add food</span>
              </button>
            </div>

            {foods.length === 0 ? (
              <div className="bg-[#111318]/85 border border-white/[0.08] rounded-xl p-4 text-center text-xs text-[#9297A3]">
                No items in meal. Click "+ Add food" to enter items manually.
              </div>
            ) : (
              foods.map((food, idx) => (
                <FoodResult
                  key={food.id || idx}
                  food={food}
                  index={idx}
                  onChange={handleFoodChange}
                  onDelete={handleFoodDelete}
                />
              ))
            )}
          </div>

          {/* Meal Total Summary */}
          <MealTotal total={computedTotal} />

          {/* AI Disclaimer */}
          <MealDisclaimer />

          {/* Action Buttons */}
          <div className="space-y-2 pt-1 text-center">
            <button
              type="button"
              disabled={status === 'SAVING' || foods.length === 0}
              onClick={handleConfirmAndSave}
              className="w-full h-[52px] bg-[#FF2B3A] hover:bg-[#E02231] active:scale-[0.99] disabled:opacity-50 text-white font-bold text-[14px] tracking-wide rounded-[16px] shadow-lg shadow-[#FF2B3A]/25 transition-all duration-150 flex items-center justify-center gap-2 focus:outline-none"
            >
              <CheckCircle size={19} strokeWidth={2.2} />
              <span>{status === 'SAVING' ? 'SAVING MEAL...' : 'CONFIRM & LOG MEAL'}</span>
            </button>

            <button
              type="button"
              onClick={handleReset}
              className="inline-flex items-center gap-1 text-[13px] text-[#9297A3] hover:text-[#F5F5F5] font-medium py-1.5 px-3 transition-colors focus:outline-none"
            >
              <RotateCcw size={14} />
              <span>Choose another photo</span>
            </button>
          </div>
        </div>
      )}

      {/* 6. State: SUCCESS */}
      {status === 'SUCCESS' && (
        <div className="bg-[#111318]/90 backdrop-blur-md border border-emerald-500/30 rounded-[20px] p-6 text-center space-y-4 shadow-2xl">
          <div className="w-14 h-14 rounded-full bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 flex items-center justify-center mx-auto">
            <CheckCircle size={32} />
          </div>

          <div className="space-y-1">
            <h2 className="text-xl font-bold text-[#F5F5F5]">MEAL LOGGED ✓</h2>
            <p className="text-xs text-[#9297A3]">
              {computedTotal.calories} kcal added to your daily {mealType} tracker.
            </p>
          </div>

          <div className="pt-3 space-y-2.5">
            <button
              type="button"
              onClick={() => navigate('/home')}
              className="w-full h-[50px] bg-[#FF2B3A] hover:bg-[#E02231] text-white font-bold text-xs tracking-wide rounded-xl shadow-lg transition-all flex items-center justify-center gap-2"
            >
              <ArrowLeft size={16} />
              <span>Back to Home</span>
            </button>

            <button
              type="button"
              onClick={handleReset}
              className="w-full py-2.5 text-xs text-[#9297A3] hover:text-[#F5F5F5] font-semibold transition-colors"
            >
              Snap Another Meal
            </button>
          </div>
        </div>
      )}

      {/* 7. State: ERROR */}
      {status === 'ERROR' && (
        <div className="bg-[#111318]/90 backdrop-blur-md border border-rose-500/30 rounded-[20px] p-6 text-center space-y-4 shadow-2xl">
          <div className="w-14 h-14 rounded-full bg-rose-500/15 border border-rose-500/30 text-rose-400 flex items-center justify-center mx-auto">
            <AlertCircle size={32} />
          </div>

          <div className="space-y-1">
            <h2 className="text-lg font-bold text-[#F5F5F5]">Unable to Analyze Meal</h2>
            <p className="text-xs text-rose-300 max-w-[260px] mx-auto leading-relaxed">
              {errorMessage || 'Gemini Vision API encountered an issue processing this image.'}
            </p>
          </div>

          <div className="pt-2 space-y-2">
            <button
              type="button"
              onClick={handleAnalyze}
              className="w-full h-[48px] bg-[#FF2B3A] hover:bg-[#E02231] text-white font-bold text-xs tracking-wide rounded-xl shadow-lg transition-all"
            >
              Try Again
            </button>

            <button
              type="button"
              onClick={handleReset}
              className="w-full py-2 text-xs text-[#9297A3] hover:text-[#F5F5F5] font-semibold transition-colors"
            >
              Choose Another Photo
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
