import React, { useState } from 'react';
import { LegacyWeeklyPlan } from '../../services/api';
import DailyPlanView from './DailyPlanView';
import NutritionSummary from './NutritionSummary';
import Card from '../ui/Card';

interface WeeklyPlanViewProps {
  plan: LegacyWeeklyPlan;
  onRegenerateMeal?: (dayIndex: number, mealType: string) => void;
  onRegenerateDay?: (dayIndex: number) => void;
  onRegenerateWeek?: () => void;
  regeneratingMeal?: { dayIndex: number; mealType: string } | null;
  regeneratingDay?: number | null;
  isRegeneratingWeek?: boolean;
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

const WeekAtAGlance: React.FC<{
  days: LegacyWeeklyPlan['days'];
  selectedDayIndex: number;
  onSelect: (index: number) => void;
}> = ({ days, selectedDayIndex, onSelect }) => (
  <Card className="p-5 sm:p-6 bg-wellness-light-elevated/50 dark:bg-wellness-dark-elevated/20 border-wellness-light-border/60 dark:border-wellness-dark-border/40">
    <SectionHeader title="Week at a Glance" icon="📊" className="mb-5" />
    <div className="grid grid-cols-7 gap-2 sm:gap-3">
      {days.map((day, index) => (
        <div
          key={index}
          className={`bg-white dark:bg-wellness-dark-card rounded-xl p-2 sm:p-3 border-2 cursor-pointer transition-all duration-300 hover:scale-[1.05] ${selectedDayIndex === index
            ? 'border-primary-500 dark:border-primary-400 shadow-glow-emerald bg-primary-50/10 dark:bg-primary-900/10'
            : 'border-transparent hover:border-wellness-light-border dark:hover:border-wellness-dark-border shadow-sm'
            }`}
          onClick={() => onSelect(index)}
        >
          <div className="text-center">
            <h4 className="font-bold text-wellness-light-text dark:text-wellness-dark-text mb-1.5 text-[10px] sm:text-xs uppercase tracking-tight">
              {new Date(day.date).toLocaleDateString('en-US', { weekday: 'short' })}
            </h4>
            <div className="space-y-1 text-[10px] sm:text-[11px]">
              <div className="text-blue-600 dark:text-blue-400 font-extrabold">
                {Math.round(day.daily_nutrition.total_calories)}
                <span className="text-[8px] font-normal ml-0.5 opacity-60">cal</span>
              </div>
              <div className="text-primary-600 dark:text-primary-400 font-bold">
                {Math.round(day.daily_nutrition.total_protein_g)}g P
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  </Card>
);

const WeeklyTipsCard: React.FC = () => (
  <Card className="p-5 sm:p-6 bg-blue-50/50 dark:bg-blue-900/10 border-blue-200/60 dark:border-blue-800/30">
    <SectionHeader title="Weekly Planning" icon="💡" className="text-blue-900 dark:text-blue-100 mb-5" />
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm text-blue-800 dark:text-blue-200">
      <div className="space-y-2">
        <h4 className="font-bold text-[11px] uppercase tracking-wider text-blue-900/40 dark:text-blue-100/30">Meal Prep Strategy</h4>
        <ul className="space-y-2">
          {['Sunday: Plan and shop for the week', 'Batch cook proteins and grains', 'Prep vegetables and snacks in advance'].map((tip, i) => (
            <li key={i} className="flex items-start gap-2.5"><span className="w-1.5 h-1.5 rounded-full bg-blue-500 mt-1.5 flex-shrink-0" /> {tip}</li>
          ))}
        </ul>
      </div>
      <div className="space-y-2">
        <h4 className="font-bold text-[11px] uppercase tracking-wider text-blue-900/40 dark:text-blue-100/30">Flexibility Tips</h4>
        <ul className="space-y-2">
          {['Swap similar meals between days', 'Adjust portion sizes based on hunger', 'Listen to your body and preferences'].map((tip, i) => (
            <li key={i} className="flex items-start gap-2.5"><span className="w-1.5 h-1.5 rounded-full bg-blue-500 mt-1.5 flex-shrink-0" /> {tip}</li>
          ))}
        </ul>
      </div>
    </div>
  </Card>
);

const WeeklyAiInsightsCard: React.FC<{ summary?: string; notes?: string }> = ({ summary, notes }) => {
  if (!summary && !notes) return null;
  return (
    <Card className="p-5 sm:p-6 bg-accent-50/50 dark:bg-accent-900/10 border-accent-200/60 dark:border-accent-800/30 h-full flex flex-col shadow-sm">
      <SectionHeader title="Weekly AI Insights" icon="🤖" className="text-accent-900 dark:text-accent-100 mb-5" />
      <div className="flex-1 space-y-5">
        {summary && (
          <div className="space-y-1.5">
            <h4 className="text-[11px] font-bold uppercase tracking-wider text-accent-700/60 dark:text-accent-300/40">
              Week Overview
            </h4>
            <p className="text-sm text-accent-800 dark:text-accent-200 leading-relaxed font-medium italic">
              "{summary}"
            </p>
          </div>
        )}
        {notes && (
          <div className="space-y-1.5">
            <h4 className="text-[11px] font-bold uppercase tracking-wider text-accent-700/60 dark:text-accent-300/40">
              Personalized Focus
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

export const WeeklyPlanView: React.FC<WeeklyPlanViewProps> = ({
  plan,
  onRegenerateMeal,
  onRegenerateDay,
  onRegenerateWeek,
  regeneratingMeal,
  regeneratingDay,
  isRegeneratingWeek = false,
  showRegenerate = true,
  onStartOver,
}) => {
  const [selectedDayIndex, setSelectedDayIndex] = useState(0);

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      weekday: 'long',
      month: 'short',
      day: 'numeric',
    });
  };

  const formatWeekRange = (startDate: string) => {
    const start = new Date(startDate);
    const end = new Date(start);
    end.setDate(start.getDate() + 6);

    return `${start.toLocaleDateString('en-US', {
      month: 'long',
      day: 'numeric'
    })} – ${end.toLocaleDateString('en-US', {
      month: 'long',
      day: 'numeric',
      year: 'numeric'
    })}`;
  };

  const selectedDay = plan.days[selectedDayIndex];
  const hasAiInsights = !!(plan.summary || plan.notes);

  return (
    <div className="max-w-7xl mx-auto space-y-8 animate-fade-in">

      {/* ─── 1. Header ───────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4 py-2 border-b border-wellness-light-border dark:border-wellness-dark-border">
        <div className="text-center sm:text-left">
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-wellness-light-text dark:text-wellness-dark-text flex items-center justify-center sm:justify-start gap-3">
            <span className="text-3xl">📅</span>
            Weekly Roadmap
          </h1>
          <div className="flex items-center justify-center sm:justify-start gap-2 mt-2">
            <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider bg-accent-100 dark:bg-accent-900/30 text-accent-700 dark:text-accent-300">
              7-Day Goal
            </span>
            <p className="text-sm font-medium text-wellness-light-textSecondary dark:text-wellness-dark-textSecondary opacity-80">
              Active for {formatWeekRange(plan.start_date)}
            </p>
          </div>
        </div>

        {showRegenerate && onRegenerateWeek && (
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
              onClick={() => onRegenerateWeek()}
              disabled={isRegeneratingWeek}
              className="group flex items-center justify-center px-5 py-2.5 text-sm font-semibold text-accent-700 dark:text-accent-300 bg-accent-50 dark:bg-accent-900/15 border border-accent-200/80 dark:border-accent-800/30 rounded-xl hover:bg-accent-100 dark:hover:bg-accent-900/25 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 w-full sm:w-auto hover:shadow-sm"
            >
              {isRegeneratingWeek ? (
                <>
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Processing...
                </>
              ) : (
                <>
                  <svg className="w-4 h-4 mr-2 transition-transform duration-300 group-hover:rotate-180" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  <span>Regenerate Entire Week</span>
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
            nutrition={plan.weekly_nutrition}
            title="Weekly Averages"
          />
        </div>
        {hasAiInsights && (
          <div className="lg:col-span-5 xl:col-span-4">
            <WeeklyAiInsightsCard summary={plan.summary} notes={plan.notes} />
          </div>
        )}
      </div>

      {/* ─── 3. Day Selection ──────────────────────────────── */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <SectionHeader title="Daily Schedules" icon="📅" className="mb-0" />
          <p className="text-xs font-bold uppercase tracking-widest text-wellness-light-textMuted dark:text-wellness-dark-textMuted hidden sm:block">
            Select a day to view details
          </p>
        </div>

        <div className="bg-white dark:bg-wellness-dark-card rounded-2xl border border-wellness-light-border dark:border-wellness-dark-border shadow-card dark:shadow-card-dark p-1.5 overflow-x-auto scrollbar-hide">
          <nav className="flex gap-1 min-w-max">
            {plan.days.map((day, index) => (
              <button
                key={index}
                onClick={() => setSelectedDayIndex(index)}
                className={`group py-3 px-4 sm:px-6 rounded-xl font-semibold text-xs sm:text-sm transition-all duration-300 flex-shrink-0 ${selectedDayIndex === index
                  ? 'bg-gradient-to-r from-primary-500 to-primary-600 text-white shadow-md scale-[1.02]'
                  : 'text-wellness-light-textSecondary dark:text-wellness-dark-textSecondary hover:bg-wellness-light-elevated dark:hover:bg-wellness-dark-elevated'
                  }`}
              >
                <div className="text-center">
                  <div className="uppercase tracking-widest text-[10px] opacity-70 mb-0.5">
                    {new Date(day.date).toLocaleDateString('en-US', { weekday: 'short' })}
                  </div>
                  <div className="flex items-center justify-center gap-1.5">
                    <span className="text-sm">{new Date(day.date).getDate()}</span>
                    <span className={`text-[10px] font-bold ${selectedDayIndex === index ? 'text-white/60' : 'text-primary-500 dark:text-primary-400'}`}>
                      {Math.round(day.daily_nutrition.total_calories)}
                    </span>
                  </div>
                </div>
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* ─── 4. Selected Day Analysis (DailyPlanView) ──────── */}
      {selectedDay && (
        <div className="pt-4 animate-slide-up">
          <DailyPlanView
            plan={selectedDay}
            onRegenerateMeal={onRegenerateMeal ? (mealType) => onRegenerateMeal(selectedDayIndex, mealType) : undefined}
            onRegenerateDay={onRegenerateDay ? () => onRegenerateDay(selectedDayIndex) : undefined}
            regeneratingMeal={
              regeneratingMeal?.dayIndex === selectedDayIndex ? regeneratingMeal.mealType : null
            }
            isRegeneratingDay={regeneratingDay === selectedDayIndex}
            showRegenerate={showRegenerate}
          />
        </div>
      )}

      {/* ─── 5. Bottom Dashboard Row ────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 pt-8 border-t border-wellness-light-border dark:border-wellness-dark-border">
        <WeekAtAGlance
          days={plan.days}
          selectedDayIndex={selectedDayIndex}
          onSelect={setSelectedDayIndex}
        />
        <WeeklyTipsCard />
      </div>
    </div>
  );
};

export default WeeklyPlanView;