import React from 'react';
import Card from '../ui/Card';
import Button from '../ui/Button';

interface PlanTypeSelectorProps {
  selectedType: 'daily' | 'weekly' | null;
  onSelect: (type: 'daily' | 'weekly') => void;
  onGenerate: (options?: { targetDate?: string; startDate?: string }) => void;
  isLoading?: boolean;
}

export const PlanTypeSelector: React.FC<PlanTypeSelectorProps> = ({
  selectedType,
  onSelect,
  onGenerate,
  isLoading = false,
}) => {

  const handleGenerate = () => {
    onGenerate({});
  };

  return (
    <Card className="max-w-4xl mx-auto animate-card-enter">
      <div className="p-6 sm:p-8">
        <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-wellness-light-text dark:text-wellness-dark-text mb-2 text-left">Choose Your Diet Plan Type</h2>
        <p className="text-sm text-wellness-light-textSecondary dark:text-wellness-dark-textSecondary mb-8 text-left leading-relaxed">
          Select the type of diet plan you'd like to generate based on your profile and goals.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-5 mb-8">
          {/* Daily Plan Option */}
          <div
            className={`border-2 rounded-2xl p-6 cursor-pointer transition-all duration-200 hover:scale-[1.01] ${selectedType === 'daily'
              ? 'border-primary-500 dark:border-primary-400 bg-primary-50/50 dark:bg-primary-900/10 shadow-glow-emerald'
              : 'border-wellness-light-border dark:border-wellness-dark-border hover:border-primary-300 dark:hover:border-primary-700 bg-white dark:bg-wellness-dark-card'
              }`}
            onClick={() => onSelect('daily')}
          >
            <div className="flex items-center mb-4">
              <div className={`w-5 h-5 rounded-full border-2 mr-3 flex items-center justify-center transition-all duration-200 ${selectedType === 'daily'
                ? 'border-primary-500 bg-primary-500'
                : 'border-wellness-light-textMuted dark:border-wellness-dark-textMuted'
                }`}>
                {selectedType === 'daily' && (
                  <div className="w-2 h-2 bg-white rounded-full"></div>
                )}
              </div>
              <h3 className="text-lg font-semibold text-wellness-light-text dark:text-wellness-dark-text">Daily Plan</h3>
            </div>

            <div className="space-y-3">
              <p className="text-sm text-wellness-light-textSecondary dark:text-wellness-dark-textSecondary leading-relaxed">
                Get a complete meal plan for a single day with breakfast, lunch, dinner, and snacks.
              </p>

              <div className="space-y-2">
                <h4 className="font-medium text-sm text-wellness-light-text dark:text-wellness-dark-text">Perfect for:</h4>
                <ul className="text-sm text-wellness-light-textSecondary dark:text-wellness-dark-textSecondary space-y-1.5">
                  <li className="flex items-center gap-2"><span className="w-1 h-1 rounded-full bg-primary-500"></span> Trying out new meal ideas</li>
                  <li className="flex items-center gap-2"><span className="w-1 h-1 rounded-full bg-primary-500"></span> Planning today's meals</li>
                  <li className="flex items-center gap-2"><span className="w-1 h-1 rounded-full bg-primary-500"></span> Quick meal inspiration</li>
                  <li className="flex items-center gap-2"><span className="w-1 h-1 rounded-full bg-primary-500"></span> Testing dietary preferences</li>
                </ul>
              </div>

              <div className="bg-primary-50 dark:bg-primary-900/15 border border-primary-200 dark:border-primary-800/30 rounded-xl p-3 mt-4">
                <p className="text-sm text-primary-700 dark:text-primary-300">
                  <span className="font-semibold">⚡ Quick:</span> Generated in seconds
                </p>
              </div>
            </div>
          </div>

          {/* Weekly Plan Option (Disabled for Maintenance) */}
          <div
            className={`relative border-2 rounded-2xl p-6 transition-all duration-200 ${selectedType === 'weekly'
              ? 'border-primary-500 dark:border-primary-400 bg-primary-50/50 dark:bg-primary-900/10 shadow-glow-emerald'
              : 'border-wellness-light-border dark:border-wellness-dark-border bg-white dark:bg-wellness-dark-card opacity-60 grayscale-[0.5]'
              } cursor-not-allowed`}
          >
            {/* Maintenance Badge */}
            <div className="absolute -top-3 right-4 bg-amber-100 dark:bg-amber-900/40 text-amber-700 dark:text-amber-300 px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider border border-amber-200 dark:border-amber-800/50 shadow-sm z-10 flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse"></span>
              Under Maintenance
            </div>
            <div className="flex items-center mb-4">
              <div className={`w-5 h-5 rounded-full border-2 mr-3 flex items-center justify-center transition-all duration-200 ${selectedType === 'weekly'
                ? 'border-primary-500 bg-primary-500'
                : 'border-wellness-light-textMuted dark:border-wellness-dark-textMuted'
                }`}>
                {selectedType === 'weekly' && (
                  <div className="w-2 h-2 bg-white rounded-full"></div>
                )}
              </div>
              <h3 className="text-lg font-semibold text-wellness-light-text dark:text-wellness-dark-text">Weekly Plan</h3>
            </div>

            <div className="space-y-3">
              <p className="text-sm text-wellness-light-textSecondary dark:text-wellness-dark-textSecondary leading-relaxed">
                Get a comprehensive 7-day meal plan with varied meals and balanced nutrition throughout the week.
              </p>

              <div className="space-y-2">
                <h4 className="font-medium text-sm text-wellness-light-text dark:text-wellness-dark-text">Perfect for:</h4>
                <ul className="text-sm text-wellness-light-textSecondary dark:text-wellness-dark-textSecondary space-y-1.5">
                  <li className="flex items-center gap-2"><span className="w-1 h-1 rounded-full bg-accent-500"></span> Meal prep planning</li>
                  <li className="flex items-center gap-2"><span className="w-1 h-1 rounded-full bg-accent-500"></span> Grocery shopping lists</li>
                  <li className="flex items-center gap-2"><span className="w-1 h-1 rounded-full bg-accent-500"></span> Long-term nutrition goals</li>
                  <li className="flex items-center gap-2"><span className="w-1 h-1 rounded-full bg-accent-500"></span> Consistent eating habits</li>
                </ul>
              </div>

              <div className="bg-accent-50 dark:bg-accent-900/15 border border-accent-200 dark:border-accent-800/30 rounded-xl p-3 mt-4">
                <p className="text-sm text-accent-700 dark:text-accent-300">
                  <span className="font-semibold">📊 Comprehensive:</span> Balanced weekly nutrition
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Generation Button */}
        <div className="text-center space-y-4">
          <div>
            <Button
              onClick={handleGenerate}
              disabled={!selectedType || isLoading}
              size="lg"
              className="px-8 py-3"
            >
              {isLoading ? (
                <>
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Generating {selectedType} plan...
                </>
              ) : (
                <>
                  🧠 Generate {selectedType ? selectedType.charAt(0).toUpperCase() + selectedType.slice(1) : ''} Plan
                </>
              )}
            </Button>
            <p className="text-xs text-wellness-light-textMuted dark:text-wellness-dark-textMuted mt-3">
              Uses ML templates + deterministic nutrition calculations
            </p>
          </div>

          {selectedType && (
            <p className="text-sm text-wellness-light-textSecondary dark:text-wellness-dark-textSecondary mt-3">
              {selectedType === 'daily'
                ? `This will create a personalized meal plan for today`
                : `This will create a personalized meal plan starting from today`
              }
            </p>
          )}
        </div>

        {/* How it works */}
        <div className="mt-8 bg-wellness-light-elevated dark:bg-wellness-dark-elevated rounded-2xl p-5">
          <h4 className="font-semibold text-sm text-wellness-light-text dark:text-wellness-dark-text mb-3 text-left">💡 How it works</h4>
          <ul className="text-sm text-wellness-light-textSecondary dark:text-wellness-dark-textSecondary space-y-2 text-left">
            <li className="flex items-start gap-2"><span className="w-1 h-1 rounded-full bg-primary-500 mt-2 flex-shrink-0"></span> Plans are generated based on your profile, goals, and preferences</li>
            <li className="flex items-start gap-2"><span className="w-1 h-1 rounded-full bg-primary-500 mt-2 flex-shrink-0"></span> All meals respect your dietary restrictions and allergies</li>
            <li className="flex items-start gap-2"><span className="w-1 h-1 rounded-full bg-primary-500 mt-2 flex-shrink-0"></span> Nutrition targets are calculated for your specific needs</li>
            <li className="flex items-start gap-2"><span className="w-1 h-1 rounded-full bg-primary-500 mt-2 flex-shrink-0"></span> You can regenerate individual meals or entire days if needed</li>
          </ul>
        </div>
      </div>
    </Card>
  );
};

export default PlanTypeSelector;