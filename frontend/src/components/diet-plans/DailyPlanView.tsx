import React from 'react';
import { LegacyDailyPlan } from '../../services/api';
import MealCard from './MealCard';
import NutritionSummary from './NutritionSummary';
import Card from '../ui/Card';

interface DailyPlanViewProps {
  plan: LegacyDailyPlan;
  onRegenerateMeal?: (mealType: string) => void;
  onRegenerateDay?: () => void;
  regeneratingMeal?: string | null;
  isRegeneratingDay?: boolean;
  showRegenerate?: boolean;
  onStartOver?: () => void;
}

/* ── Inline sub-components (Refined for Premium Dashboard) ───── */

const SectionHeader: React.FC<{ title: string; icon?: string; className?: string }> = ({ title, icon, className = '' }) => (
  <h2 className={`text-lg font-medium text-wellness-light-text dark:text-wellness-dark-text flex items-center gap-2 mb-4 ${className}`}>
    {icon && <span className="text-xl">{icon}</span>}
    {title}
  </h2>
);

const MealTimingCard: React.FC<{ hasSnacks: boolean }> = ({ hasSnacks }) => (
  <Card className="p-5 sm:p-6 bg-blue-50/50 dark:bg-blue-900/10 border-blue-200/60 dark:border-blue-800/30">
    <SectionHeader title="Meal Timing" icon="🕐" className="text-blue-900 dark:text-blue-100 mb-5" />
    <div className="space-y-4 text-sm text-left">
      {[
        { icon: '🌅', label: 'Breakfast', time: '7:00 – 9:00 AM' },
        { icon: '🌞', label: 'Lunch', time: '12:00 – 2:00 PM' },
        { icon: '🌙', label: 'Dinner', time: '6:00 – 8:00 PM' },
      ].map((t) => (
        <div key={t.label} className="flex items-center gap-4 group transition-transform duration-200 hover:translate-x-1">
          <div className="flex-shrink-0 w-10 h-10 rounded-xl bg-white dark:bg-wellness-dark-elevated shadow-sm flex items-center justify-center text-xl">
            {t.icon}
          </div>
          <div>
            <p className="font-semibold text-blue-900 dark:text-blue-100 leading-none">{t.label}</p>
            <p className="text-blue-700/80 dark:text-blue-300/70 mt-1">{t.time}</p>
          </div>
        </div>
      ))}
      {hasSnacks && (
        <div className="pt-4 mt-2 border-t border-blue-200/60 dark:border-blue-800/30">
          <div className="flex items-center gap-4">
            <div className="flex-shrink-0 w-10 h-10 rounded-xl bg-white dark:bg-wellness-dark-elevated shadow-sm flex items-center justify-center text-xl text-amber-500">
              🍎
            </div>
            <div>
              <p className="font-semibold text-blue-900 dark:text-blue-100 leading-none">Snacks</p>
              <p className="text-blue-700/80 dark:text-blue-300/70 mt-1">Between meals as needed</p>
            </div>
          </div>
        </div>
      )}
    </div>
  </Card>
);

const PrepTipsCard: React.FC = () => (
  <Card className="p-5 sm:p-6 bg-primary-50/50 dark:bg-primary-900/10 border-primary-200/60 dark:border-primary-800/30">
    <SectionHeader title="Preparation Tips" icon="💡" className="text-primary-900 dark:text-primary-100 mb-5" />
    <ul className="text-sm text-primary-800 dark:text-primary-200 space-y-3">
      {[
        'Review all recipes and create a shopping list',
        'Prep ingredients in advance (wash veg, marinate proteins)',
        'Cook grains and proteins in batches to save active time',
        'Aim for 8–10 glasses of water throughout the day',
        'Listen to your body and adjust portion sizes as needed',
      ].map((tip, i) => (
        <li key={i} className="flex items-start gap-3 py-1 border-b border-primary-200/40 dark:border-primary-800/20 last:border-0 group">
          <span className="w-1.5 h-1.5 rounded-full bg-primary-500 mt-2 flex-shrink-0 transition-transform duration-200 group-hover:scale-125" />
          <span className="leading-relaxed">{tip}</span>
        </li>
      ))}
    </ul>
  </Card>
);

const AiInsightsCard: React.FC<{ summary?: string; notes?: string }> = ({ summary, notes }) => {
  if (!summary && !notes) return null;
  return (
    <Card className="p-5 sm:p-6 bg-accent-50/50 dark:bg-accent-900/10 border-accent-200/60 dark:border-accent-800/30 h-full flex flex-col shadow-sm">
      <SectionHeader title="AI Nutritionist Insights" icon="🤖" className="text-accent-900 dark:text-accent-100 mb-5" />
      <div className="flex-1 space-y-6">
        {summary && (
          <div className="space-y-1.5">
            <h4 className="text-[11px] font-bold uppercase tracking-wider text-accent-700/60 dark:text-accent-300/40">
              Daily Overview
            </h4>
            <p className="text-sm text-accent-800 dark:text-accent-200 leading-relaxed font-medium italic">
              "{summary}"
            </p>
          </div>
        )}
        {notes && (
          <div className="space-y-1.5">
            <h4 className="text-[11px] font-bold uppercase tracking-wider text-accent-700/60 dark:text-accent-300/40">
              Pro-Active Guidance
            </h4>
            <div className="text-sm text-accent-800/90 dark:text-accent-200/90 space-y-2 leading-relaxed">
              {notes.split('. ').map((sentence, idx) => (
                sentence && <p key={idx}>{sentence.trim()}{sentence.endsWith('.') ? '' : '.'}</p>
              ))}
            </div>
          </div>
        )}
      </div>
    </Card>
  );
};

/* ── Main component ────────────────────────────────────────────── */

export const DailyPlanView: React.FC<DailyPlanViewProps> = ({
  plan,
  onRegenerateMeal,
  onRegenerateDay,
  regeneratingMeal,
  isRegeneratingDay = false,
  showRegenerate = true,
  onStartOver,
}) => {
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  const meals = [
    { type: 'breakfast', meal: plan.meals.breakfast },
    { type: 'lunch', meal: plan.meals.lunch },
    { type: 'dinner', meal: plan.meals.dinner },
  ];

  if (plan.meals.snacks) {
    if (Array.isArray(plan.meals.snacks)) {
      plan.meals.snacks.forEach((snack, index) => {
        meals.push({ type: `snack_${index + 1}`, meal: snack });
      });
    } else {
      meals.push({ type: 'snack', meal: plan.meals.snacks });
    }
  }

  const hasAiInsights = !!(plan.summary || plan.notes);

  return (
    <div className="max-w-7xl mx-auto space-y-8 animate-fade-in">

      {/* ─── 1. Header ───────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4 py-2 border-b border-wellness-light-border dark:border-wellness-dark-border">
        <div className="text-center sm:text-left">
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-wellness-light-text dark:text-wellness-dark-text flex items-center justify-center sm:justify-start gap-3">
            <span className="text-3xl">🍽️</span>
            Your Daily Plan
          </h1>
          <div className="flex items-center justify-center sm:justify-start gap-2 mt-2">
            <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300">
              Active Plan
            </span>
            <p className="text-sm font-medium text-wellness-light-textSecondary dark:text-wellness-dark-textSecondary opacity-80">
              Generated on {formatDate(plan.date)}
            </p>
          </div>
        </div>

        {showRegenerate && onRegenerateDay && (
          <div className="flex flex-col sm:flex-row gap-2 w-full sm:w-auto">
            {onStartOver && (
              <button
                onClick={onStartOver}
                className="flex items-center justify-center px-4 py-2.5 text-sm font-semibold text-wellness-light-textSecondary dark:text-wellness-dark-textSecondary bg-white dark:bg-wellness-dark-card border border-wellness-light-border dark:border-wellness-dark-border rounded-xl hover:bg-wellness-light-elevated dark:hover:bg-wellness-dark-elevated transition-all duration-200 hover:scale-[1.02] active:scale-[0.98] w-full sm:w-auto"
              >
                <svg className="w-4 h-4 mr-2 text-wellness-light-textMuted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                New Plan
              </button>
            )}
            <button
              onClick={() => onRegenerateDay()}
              disabled={isRegeneratingDay}
              className="group flex items-center justify-center px-5 py-2.5 text-sm font-semibold text-accent-700 dark:text-accent-300 bg-accent-50 dark:bg-accent-900/15 border border-accent-200/80 dark:border-accent-800/30 rounded-xl hover:bg-accent-100 dark:hover:bg-accent-900/25 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 w-full sm:w-auto hover:shadow-sm"
            >
              {isRegeneratingDay ? (
                <>
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Regenerating...
                </>
              ) : (
                <>
                  <svg className="w-4 h-4 mr-2 transition-transform duration-300 group-hover:rotate-180" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  <span>Full Day Regeneration</span>
                </>
              )}
            </button>
          </div>
        )}
      </div>

      {/* ─── 2. Top Dashboard Row ───────────────────────────── */}
      <div className={`grid grid-cols-1 ${hasAiInsights ? 'lg:grid-cols-12' : ''} gap-6`}>
        <div className={hasAiInsights ? 'lg:col-span-7 xl:col-span-8' : ''}>
          <NutritionSummary
            nutrition={plan.daily_nutrition}
            title="Macro Distribution"
          />
        </div>
        {hasAiInsights && (
          <div className="lg:col-span-5 xl:col-span-4">
            <AiInsightsCard summary={plan.summary} notes={plan.notes} />
          </div>
        )}
      </div>

      {/* ─── 3. Meals Grid (primary focus) ─────────────────── */}
      <section className="space-y-6">
        <div className="flex items-center justify-between">
          <SectionHeader title="Today's Meal Routine" icon="🥗" className="mb-0" />
          <div className="h-px flex-1 mx-6 bg-wellness-light-border dark:bg-wellness-dark-border hidden md:block" />
          <span className="text-xs font-bold uppercase tracking-widest text-wellness-light-textMuted dark:text-wellness-dark-textMuted whitespace-nowrap">
            {meals.length} Sessions Planned
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
          {meals.map(({ type, meal }) => (
            <MealCard
              key={type}
              meal={meal}
              mealType={type}
              onRegenerate={onRegenerateMeal ? () => onRegenerateMeal(type) : undefined}
              isRegenerating={regeneratingMeal === type}
              showRegenerate={showRegenerate}
            />
          ))}
        </div>
      </section>

      {/* ─── 4. Bottom Info Row ────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <MealTimingCard hasSnacks={!!plan.meals.snacks} />
        <PrepTipsCard />
      </div>
    </div>
  );
};

export default DailyPlanView;