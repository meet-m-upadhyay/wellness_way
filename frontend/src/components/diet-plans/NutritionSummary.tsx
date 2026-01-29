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
  // Determine if this is daily or weekly data
  const isWeekly = nutrition.avg_daily_calories !== undefined;
  
  const calories = isWeekly ? nutrition.avg_daily_calories! : nutrition.total_calories!;
  const protein = isWeekly ? nutrition.avg_daily_protein_g! : nutrition.total_protein_g!;
  const carbs = isWeekly ? nutrition.avg_daily_carbs_g! : nutrition.total_carbs_g!;
  const fat = isWeekly ? nutrition.avg_daily_fat_g! : nutrition.total_fat_g!;

  // Calculate macronutrient percentages
  const proteinCalories = protein * 4;
  const carbCalories = carbs * 4;
  const fatCalories = fat * 9;
  const totalMacroCalories = proteinCalories + carbCalories + fatCalories;

  const proteinPercentage = totalMacroCalories > 0 ? (proteinCalories / totalMacroCalories) * 100 : 0;
  const carbPercentage = totalMacroCalories > 0 ? (carbCalories / totalMacroCalories) * 100 : 0;
  const fatPercentage = totalMacroCalories > 0 ? (fatCalories / totalMacroCalories) * 100 : 0;

  // Calculate progress towards target calories if provided
  const calorieProgress = targetCalories ? (calories / targetCalories) * 100 : null;

  const macronutrients = [
    {
      name: 'Protein',
      amount: Math.round(protein),
      unit: 'g',
      percentage: Math.round(proteinPercentage),
      color: 'bg-green-500',
      lightColor: 'bg-green-100 dark:bg-green-900/30',
      textColor: 'text-green-800 dark:text-green-200',
    },
    {
      name: 'Carbs',
      amount: Math.round(carbs),
      unit: 'g',
      percentage: Math.round(carbPercentage),
      color: 'bg-yellow-500',
      lightColor: 'bg-yellow-100 dark:bg-yellow-900/30',
      textColor: 'text-yellow-800 dark:text-yellow-200',
    },
    {
      name: 'Fat',
      amount: Math.round(fat),
      unit: 'g',
      percentage: Math.round(fatPercentage),
      color: 'bg-red-500',
      lightColor: 'bg-red-100 dark:bg-red-900/30',
      textColor: 'text-red-800 dark:text-red-200',
    },
  ];

  return (
    <Card>
      <div className="p-4 sm:p-6">
        <div className="text-center sm:text-left mb-4 sm:mb-6">
          <h3 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-white flex items-center justify-center sm:justify-start">
            <span className="text-xl mr-2">📊</span>
            {title}
          </h3>
        </div>
        
        {/* Calories Section */}
        <div className="mb-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-3">
            <h4 className="text-sm font-medium text-gray-600 dark:text-gray-300 mb-1 sm:mb-0">
              {isWeekly ? 'Average Daily Calories' : 'Total Calories'}
            </h4>
            {targetCalories && (
              <span className="text-sm text-gray-500 dark:text-gray-400">
                Target: {targetCalories}
              </span>
            )}
          </div>
          
          <div className="flex flex-col sm:flex-row sm:items-center text-center sm:text-left">
            <div className="flex items-center justify-center sm:justify-start">
              <span className="text-2xl sm:text-3xl font-bold text-blue-600 dark:text-blue-400 mr-2">
                {Math.round(calories)}
              </span>
              <span className="text-gray-500 dark:text-gray-400">kcal</span>
            </div>
            {calorieProgress && (
              <span className={`mt-2 sm:mt-0 sm:ml-3 text-sm font-medium ${
                calorieProgress >= 95 && calorieProgress <= 105 
                  ? 'text-green-600 dark:text-green-400' 
                  : calorieProgress < 95 
                    ? 'text-yellow-600 dark:text-yellow-400' 
                    : 'text-red-600 dark:text-red-400'
              }`}>
                ({Math.round(calorieProgress)}% of target)
              </span>
            )}
          </div>
          
          {targetCalories && (
            <div className="mt-2">
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div
                  className={`h-2 rounded-full ${
                    calorieProgress! >= 95 && calorieProgress! <= 105
                      ? 'bg-green-500'
                      : calorieProgress! < 95
                        ? 'bg-yellow-500'
                        : 'bg-red-500'
                  }`}
                  style={{ width: `${Math.min(calorieProgress!, 100)}%` }}
                ></div>
              </div>
            </div>
          )}
        </div>

        {/* Macronutrients Section */}
        <div>
          <h4 className="text-sm font-medium text-gray-600 dark:text-gray-300 mb-4">Macronutrient Breakdown</h4>
          
          <div className="space-y-4">
            {macronutrients.map((macro) => (
              <div key={macro.name}>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-600 dark:text-gray-300">{macro.name}</span>
                  <div className="flex items-center">
                    <span className="text-sm font-semibold text-gray-900 dark:text-white mr-2">
                      {macro.amount}{macro.unit}
                    </span>
                    {showPercentages && (
                      <span className={`text-xs px-2 py-1 rounded-full ${macro.lightColor} ${macro.textColor}`}>
                        {macro.percentage}%
                      </span>
                    )}
                  </div>
                </div>
                
                {showPercentages && (
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full ${macro.color}`}
                      style={{ width: `${macro.percentage}%` }}
                    ></div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Macro Distribution Pie Chart Representation */}
        {showPercentages && (
          <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
            <h4 className="text-sm font-medium text-gray-600 dark:text-gray-300 mb-3">Distribution</h4>
            <div className="flex items-center space-x-4 text-sm">
              {macronutrients.map((macro) => (
                <div key={macro.name} className="flex items-center">
                  <div className={`w-3 h-3 rounded-full ${macro.color} mr-2`}></div>
                  <span className="text-gray-600 dark:text-gray-300">
                    {macro.name}: {macro.percentage}%
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Additional Info for Weekly Plans */}
        {isWeekly && (
          <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
            <p className="text-xs text-gray-500 dark:text-gray-400">
              * Values shown are daily averages across the 7-day plan
            </p>
          </div>
        )}
      </div>
    </Card>
  );
};

export default NutritionSummary;