import React, { useState } from 'react';
import { LegacyMeal } from '../../services/api';
import Card from '../ui/Card';
import Button from '../ui/Button';

interface MealCardProps {
  meal: LegacyMeal;
  mealType: string;
  onRegenerate?: () => void;
  isRegenerating?: boolean;
  showRegenerate?: boolean;
}

export const MealCard: React.FC<MealCardProps> = ({
  meal,
  mealType,
  onRegenerate,
  isRegenerating = false,
  showRegenerate = true,
}) => {
  const [showIngredients, setShowIngredients] = useState(false);
  const [showRecipe, setShowRecipe] = useState(false);

  const formatMealType = (type: string) => {
    return type.charAt(0).toUpperCase() + type.slice(1);
  };

  const getMealIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case 'breakfast': return '🌅';
      case 'lunch': return '🌞';
      case 'dinner': return '🌙';
      case 'snack': case 'snacks': return '🍎';
      default: return '🍽️';
    }
  };

  const nutritionItems = [
    { label: 'Calories', value: Math.round(meal.nutrition.calories), unit: 'kcal', color: 'text-blue-600 dark:text-blue-400', bg: 'bg-blue-50 dark:bg-blue-900/15' },
    { label: 'Protein', value: Math.round(meal.nutrition.protein_g), unit: 'g', color: 'text-primary-600 dark:text-primary-400', bg: 'bg-primary-50 dark:bg-primary-900/15' },
    { label: 'Carbs', value: Math.round(meal.nutrition.carbs_g), unit: 'g', color: 'text-amber-600 dark:text-amber-400', bg: 'bg-amber-50 dark:bg-amber-900/15' },
    { label: 'Fat', value: Math.round(meal.nutrition.fat_g), unit: 'g', color: 'text-rose-600 dark:text-rose-400', bg: 'bg-rose-50 dark:bg-rose-900/15' },
  ];

  return (
    <Card className="h-full" hover>
      <div className="p-5 sm:p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-wellness-light-elevated dark:bg-wellness-dark-elevated flex items-center justify-center text-xl">
              {getMealIcon(mealType)}
            </div>
            <div>
              <h3 className="text-base font-semibold text-wellness-light-text dark:text-wellness-dark-text text-left">{formatMealType(mealType)}</h3>
              <p className="text-sm text-wellness-light-textSecondary dark:text-wellness-dark-textSecondary text-left">{meal.name}</p>
            </div>
          </div>
          {showRegenerate && onRegenerate && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => onRegenerate()}
              disabled={isRegenerating}
              title="Regenerate Meal"
              className="!rounded-xl"
            >
              {isRegenerating ? (
                <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
              ) : (
                <>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  <span className="text-xs">🧠</span>
                </>
              )}
            </Button>
          )}
        </div>

        {/* Nutrition Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 mb-5">
          {nutritionItems.map((item) => (
            <div key={item.label} className={`${item.bg} rounded-xl p-3 text-center`}>
              <p className={`text-lg sm:text-xl font-bold ${item.color}`}>
                {item.value}<span className="text-xs font-medium ml-0.5">{item.unit}</span>
              </p>
              <p className="text-xs text-wellness-light-textMuted dark:text-wellness-dark-textMuted mt-0.5">{item.label}</p>
            </div>
          ))}
        </div>

        {/* Ingredients Section */}
        <div className="mb-3">
          <button
            onClick={() => setShowIngredients(!showIngredients)}
            className="flex items-center justify-between w-full text-left py-2.5 px-3 rounded-xl hover:bg-wellness-light-elevated dark:hover:bg-wellness-dark-elevated transition-colors duration-150"
          >
            <h4 className="font-medium text-sm text-wellness-light-text dark:text-wellness-dark-text">Ingredients ({meal.ingredients.length})</h4>
            <svg
              className={`w-4 h-4 text-wellness-light-textMuted dark:text-wellness-dark-textMuted transform transition-transform duration-200 ${showIngredients ? 'rotate-180' : ''}`}
              fill="none" stroke="currentColor" viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          <div className={`overflow-hidden transition-all duration-200 ${showIngredients ? 'max-h-[500px] opacity-100' : 'max-h-0 opacity-0'}`}>
            <div className="mt-1 pl-3 space-y-1.5">
              {meal.ingredients.map((ingredient, index) => (
                <div key={index} className="flex items-center text-sm text-wellness-light-textSecondary dark:text-wellness-dark-textSecondary">
                  <span className="w-1.5 h-1.5 bg-primary-400 dark:bg-primary-500 rounded-full mr-3 flex-shrink-0"></span>
                  {ingredient}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Recipe Section */}
        <div>
          <button
            onClick={() => setShowRecipe(!showRecipe)}
            className="flex items-center justify-between w-full text-left py-2.5 px-3 rounded-xl hover:bg-wellness-light-elevated dark:hover:bg-wellness-dark-elevated transition-colors duration-150"
          >
            <h4 className="font-medium text-sm text-wellness-light-text dark:text-wellness-dark-text text-left">Recipe</h4>
            <svg
              className={`w-4 h-4 text-wellness-light-textMuted dark:text-wellness-dark-textMuted transform transition-transform duration-200 ${showRecipe ? 'rotate-180' : ''}`}
              fill="none" stroke="currentColor" viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          <div className={`overflow-hidden transition-all duration-200 ${showRecipe ? 'max-h-[1000px] opacity-100' : 'max-h-0 opacity-0'}`}>
            <div className="mt-1 pl-3">
              <p className="text-sm text-wellness-light-textSecondary dark:text-wellness-dark-textSecondary leading-relaxed whitespace-pre-line text-left">
                {meal.instructions}
              </p>
            </div>
          </div>
        </div>

        {/* Additional Nutrition Info */}
        {meal.nutrition.fiber_g && (
          <div className="mt-4 pt-4 border-t border-wellness-light-border dark:border-wellness-dark-border">
            <div className="flex justify-between text-sm">
              <span className="text-wellness-light-textSecondary dark:text-wellness-dark-textSecondary">Fiber:</span>
              <span className="font-medium text-wellness-light-text dark:text-wellness-dark-text">{Math.round(meal.nutrition.fiber_g)}g</span>
            </div>
          </div>
        )}
      </div>
    </Card>
  );
};

export default MealCard;