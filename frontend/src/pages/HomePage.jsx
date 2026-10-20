import React, { useState, useEffect } from 'react';
import Greeting from '../components/Greeting';
import CalorieHero from '../components/CalorieHero';
import MacroSummary from '../components/MacroSummary';
import PrimaryAction from '../components/PrimaryAction';
import MealList from '../components/MealList';
import { useProfile } from '../context/ProfileContext';
import { getCoachContext, createMeal } from '../lib/api';

export default function HomePage() {
  const { profile, activePlan } = useProfile();

  const [userName, setUserName] = useState(profile?.name?.trim() || '');
  const [consumedCalories, setConsumedCalories] = useState(0);
  const [targetCalories, setTargetCalories] = useState(
    activePlan?.calorie_target ?? activePlan?.target_calories ?? 0
  );
  const [protein, setProtein] = useState({
    current: 0,
    target: activePlan?.protein_target ?? activePlan?.protein_g ?? 0,
  });
  const [carbs, setCarbs] = useState({
    current: 0,
    target: activePlan?.carbs_target ?? activePlan?.carbs_g ?? 0,
  });
  const [fat, setFat] = useState({
    current: 0,
    target: activePlan?.fat_target ?? activePlan?.fat_g ?? 0,
  });
  const [meals, setMeals] = useState([]);

  // Sync targets when profile/activePlan updates from context
  useEffect(() => {
    if (profile?.name) {
      setUserName(profile.name.trim());
    } else {
      setUserName('');
    }

    if (activePlan) {
      const cal = activePlan.calorie_target ?? activePlan.target_calories ?? 0;
      const p = activePlan.protein_target ?? activePlan.protein_g ?? 0;
      const c = activePlan.carbs_target ?? activePlan.carbs_g ?? 0;
      const f = activePlan.fat_target ?? activePlan.fat_g ?? 0;

      setTargetCalories(cal);
      setProtein((prev) => ({ ...prev, target: p }));
      setCarbs((prev) => ({ ...prev, target: c }));
      setFat((prev) => ({ ...prev, target: f }));
    }
  }, [profile, activePlan]);

  // Load today's live intake and confirmed meals from backend
  useEffect(() => {
    let isMounted = true;
    async function loadTodayData() {
      try {
        const data = await getCoachContext();
        if (!isMounted) return;

        if (data?.has_profile) {
          if (data.user_name && data.user_name !== 'there') {
            setUserName(data.user_name);
          }
          if (data.target_calories) setTargetCalories(data.target_calories);
          setConsumedCalories(data.consumed_calories || 0);
          setProtein({
            current: data.consumed_protein || 0,
            target: data.target_protein || 0,
          });
          setCarbs({
            current: data.consumed_carbs || 0,
            target: data.target_carbs || 0,
          });
          setFat({
            current: data.consumed_fat || 0,
            target: data.target_fat || 0,
          });
          setMeals(data.today_meals || []);
        }
      } catch (err) {
        console.warn('Unable to load today nutrition intake:', err);
      }
    }

    loadTodayData();
    return () => {
      isMounted = false;
    };
  }, []);

  const handleQuickAdd = async () => {
    const todayStr = new Date().toISOString().split('T')[0];
    const newMealPayload = {
      meal_type: 'Quick Add',
      name: 'Protein Snack',
      calories: 200,
      protein: 25,
      carbs: 5,
      fat: 3,
      date: todayStr,
    };

    try {
      const saved = await createMeal(newMealPayload);
      const mealRecord = saved.meal || {
        id: Date.now(),
        ...newMealPayload,
      };

      setConsumedCalories((prev) => prev + mealRecord.calories);
      setProtein((prev) => ({ ...prev, current: prev.current + (mealRecord.protein || 0) }));
      setCarbs((prev) => ({ ...prev, current: prev.current + (mealRecord.carbs || 0) }));
      setFat((prev) => ({ ...prev, current: prev.current + (mealRecord.fat || 0) }));
      setMeals((prev) => [mealRecord, ...prev]);
    } catch (err) {
      console.error('Failed to log quick meal:', err);
      // Fallback local update
      setConsumedCalories((prev) => prev + 200);
      setProtein((prev) => ({ ...prev, current: prev.current + 25 }));
      setMeals((prev) => [
        { id: Date.now(), meal_type: 'Quick Add', name: 'Protein Snack', calories: 200, protein: 25 },
        ...prev,
      ]);
    }
  };

  return (
    <div className="space-y-6 min-w-0">
      {/* 1. Greeting Header */}
      <Greeting userName={userName} />

      {/* 2. Calorie Hero Card */}
      <CalorieHero
        consumed={consumedCalories}
        target={targetCalories}
        animeAsset="/assets/anime/home-hero.png"
      />

      {/* 3. Macro Breakdown Summary */}
      <MacroSummary
        protein={protein}
        carbs={carbs}
        fat={fat}
      />

      {/* 4. Primary Meal Logging Action */}
      <PrimaryAction onQuickAdd={handleQuickAdd} />

      {/* 5. Today's Meals Section */}
      <MealList meals={meals} />
    </div>
  );
}
