import React, { useState } from 'react';
import Greeting from '../components/Greeting';
import CalorieHero from '../components/CalorieHero';
import MacroSummary from '../components/MacroSummary';
import PrimaryAction from '../components/PrimaryAction';
import MealList from '../components/MealList';

// Clean temporary initial state (will connect to backend API endpoints in Phase 2 functional wiring)
const INITIAL_HOME_DATA = {
  userName: 'Nishith',
  consumedCalories: 540,
  targetCalories: 2380,
  protein: { current: 82, target: 144 },
  carbs: { current: 180, target: 302 },
  fat: { current: 42, target: 66 },
  meals: [
    { id: 1, meal_type: 'Breakfast', name: '2 Scrambled Eggs & Toast', calories: 220, protein: 14 },
    { id: 2, meal_type: 'Lunch', name: 'Paneer Rice Bowl', calories: 320, protein: 28 },
  ],
};

export default function HomePage() {
  const [data, setData] = useState(INITIAL_HOME_DATA);

  const handleQuickAdd = () => {
    // Quick Add handler fallback for demonstration
    const newMeal = {
      id: Date.now(),
      meal_type: 'Quick Add',
      name: 'Protein Shake',
      calories: 200,
      protein: 25,
    };
    setData((prev) => ({
      ...prev,
      consumedCalories: prev.consumedCalories + newMeal.calories,
      protein: { ...prev.protein, current: prev.protein.current + newMeal.protein },
      meals: [newMeal, ...prev.meals],
    }));
  };

  return (
    <div className="space-y-6 min-w-0">
      {/* 1. Greeting Header */}
      <Greeting userName={data.userName} />

      {/* 2. Calorie Hero Card */}
      <CalorieHero
        consumed={data.consumedCalories}
        target={data.targetCalories}
        animeAsset="/assets/anime/home-hero.png"
      />

      {/* 3. Macro Breakdown Summary */}
      <MacroSummary
        protein={data.protein}
        carbs={data.carbs}
        fat={data.fat}
      />

      {/* 4. Primary Meal Logging Action */}
      <PrimaryAction onQuickAdd={handleQuickAdd} />

      {/* 5. Today's Meals Section */}
      <MealList meals={data.meals} />
    </div>
  );
}
