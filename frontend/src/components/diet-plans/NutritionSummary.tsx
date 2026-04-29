import React from 'react';
import Card from '../ui/Card';

interface NutritionData {
  total_calories?: number;
  total_protein_g?: number;
  total_carbs_g?: number;
  total_fat_g?: number;
  avg_daily_calories?: number;
  avg_daily_protein_g?: number;
  avg_daily_carbs_g?: number;
  avg_daily_fat_g?: number;
}

interface NutritionSummaryProps {
  nutrition: NutritionData;
  title?: string;
  showPercentages?: boolean;
  targetCalories?: number;
}

export const NutritionSummary: React.FC<NutritionSummaryProps> = ({
  nutrition,
  title = "Nutrition Summary",
  showPercentages = true,
  targetCalories,
}) => {
  const isWeekly = nutrition.avg_daily_calories !== undefined;

  const calories = isWeekly ? nutrition.avg_daily_calories! : nutrition.total_calories!;
  const protein = isWeekly ? nutrition.avg_daily_protein_g! : nutrition.total_protein_g!;
  const carbs = isWeekly ? nutrition.avg_daily_carbs_g! : nutrition.total_carbs_g!;
  const fat = isWeekly ? nutrition.avg_daily_fat_g! : nutrition.total_fat_g!;

  const proteinCalories = protein * 4;
  const carbCalories = carbs * 4;
  const fatCalories = fat * 9;
  const totalMacroCalories = proteinCalories + carbCalories + fatCalories;

  const proteinPercentage = totalMacroCalories > 0 ? (proteinCalories / totalMacroCalories) * 100 : 0;
  const carbPercentage = totalMacroCalories > 0 ? (carbCalories / totalMacroCalories) * 100 : 0;
  const fatPercentage = totalMacroCalories > 0 ? (fatCalories / totalMacroCalories) * 100 : 0;

  const calorieProgress = targetCalories ? (calories / targetCalories) * 100 : null;

  const macronutrients = [
    {
      name: 'Protein',
      amount: Math.round(protein),
      unit: 'g',
      percentage: Math.round(proteinPercentage),
      gradient: 'from-primary-400 to-primary-600',
      bg: 'bg-primary-50 dark:bg-primary-900/15',
      text: 'text-primary-700 dark:text-primary-300',
      dot: 'bg-primary-500',
    },
    {
      name: 'Carbs',
      amount: Math.round(carbs),
      unit: 'g',
      percentage: Math.round(carbPercentage),
      gradient: 'from-amber-400 to-amber-600',
      bg: 'bg-amber-50 dark:bg-amber-900/15',
      text: 'text-amber-700 dark:text-amber-300',
      dot: 'bg-amber-500',
    },
    {
      name: 'Fat',
      amount: Math.round(fat),
      unit: 'g',
      percentage: Math.round(fatPercentage),
      gradient: 'from-rose-400 to-rose-600',
      bg: 'bg-rose-50 dark:bg-rose-900/15',
      text: 'text-rose-700 dark:text-rose-300',
      dot: 'bg-rose-500',
    },
  ];

  return (
    <Card>
      <div className="p-5 sm:p-6">
        <div className="text-center sm:text-left mb-5">
          <h3 className="text-base sm:text-lg font-semibold text-wellness-light-text dark:text-wellness-dark-text flex items-center justify-center sm:justify-start gap-2">
            <span className="text-lg">📊</span>
            {title}
          </h3>
        </div>

        {/* Calories Section */}
        <div className="mb-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-3">
            <h4 className="text-sm font-medium text-wellness-light-textSecondary dark:text-wellness-dark-textSecondary mb-1 sm:mb-0">
              {isWeekly ? 'Average Daily Calories' : 'Total Calories'}
            </h4>
            {targetCalories && (
              <span className="text-xs text-wellness-light-textMuted dark:text-wellness-dark-textMuted">
                Target: {targetCalories} kcal
              </span>
            )}
          </div>

          <div className="flex flex-col sm:flex-row sm:items-center text-center sm:text-left gap-2">
            <div className="flex items-baseline justify-center sm:justify-start gap-1">
              <span className="text-3xl font-bold text-blue-600 dark:text-blue-400">
                {Math.round(calories)}
              </span>
              <span className="text-sm text-wellness-light-textMuted dark:text-wellness-dark-textMuted">kcal</span>
            </div>
            {calorieProgress && (
              <span className={`text-xs font-semibold px-2 py-1 rounded-lg ${calorieProgress >= 95 && calorieProgress <= 105
                  ? 'bg-primary-50 dark:bg-primary-900/15 text-primary-700 dark:text-primary-300'
                  : calorieProgress < 95
                    ? 'bg-amber-50 dark:bg-amber-900/15 text-amber-700 dark:text-amber-300'
                    : 'bg-rose-50 dark:bg-rose-900/15 text-rose-700 dark:text-rose-300'
                }`}>
                {Math.round(calorieProgress)}% of target
              </span>
            )}
          </div>

          {targetCalories && (
            <div className="mt-3">
              <div className="w-full bg-wellness-light-elevated dark:bg-wellness-dark-elevated rounded-full h-2">
                <div
                  className={`h-2 rounded-full transition-all duration-500 bg-gradient-to-r ${calorieProgress! >= 95 && calorieProgress! <= 105
                      ? 'from-primary-400 to-primary-600'
                      : calorieProgress! < 95
                        ? 'from-amber-400 to-amber-600'
                        : 'from-rose-400 to-rose-600'
                    }`}
                  style={{ width: `${Math.min(calorieProgress!, 100)}%` }}
                ></div>
              </div>
            </div>
          )}
        </div>

        {/* Macronutrients Section */}
        <div>
          <h4 className="text-sm font-medium text-wellness-light-textSecondary dark:text-wellness-dark-textSecondary mb-4">Macronutrient Breakdown</h4>

          <div className="space-y-4">
            {macronutrients.map((macro) => (
              <div key={macro.name}>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-wellness-light-textSecondary dark:text-wellness-dark-textSecondary">{macro.name}</span>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold text-wellness-light-text dark:text-wellness-dark-text">
                      {macro.amount}{macro.unit}
                    </span>
                    {showPercentages && (
                      <span className={`text-xs font-semibold px-2 py-0.5 rounded-lg ${macro.bg} ${macro.text}`}>
                        {macro.percentage}%
                      </span>
                    )}
                  </div>
                </div>

                {showPercentages && (
                  <div className="w-full bg-wellness-light-elevated dark:bg-wellness-dark-elevated rounded-full h-2">
                    <div
                      className={`h-2 rounded-full bg-gradient-to-r ${macro.gradient} transition-all duration-500`}
                      style={{ width: `${macro.percentage}%` }}
                    ></div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Distribution Legend */}
        {showPercentages && (
          <div className="mt-6 pt-5 border-t border-wellness-light-border dark:border-wellness-dark-border">
            <h4 className="text-xs font-medium text-wellness-light-textMuted dark:text-wellness-dark-textMuted mb-3 uppercase tracking-wider">Distribution</h4>
            <div className="flex items-center flex-wrap gap-4 text-sm">
              {macronutrients.map((macro) => (
                <div key={macro.name} className="flex items-center gap-1.5">
                  <div className={`w-2.5 h-2.5 rounded-full ${macro.dot}`}></div>
                  <span className="text-wellness-light-textSecondary dark:text-wellness-dark-textSecondary text-xs">
                    {macro.name}: {macro.percentage}%
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {isWeekly && (
          <div className="mt-5 pt-5 border-t border-wellness-light-border dark:border-wellness-dark-border">
            <p className="text-xs text-wellness-light-textMuted dark:text-wellness-dark-textMuted">
              * Values shown are daily averages across the 7-day plan
            </p>
          </div>
        )}
      </div>
    </Card>
  );
};

export default NutritionSummary;