import React, { useState } from 'react';
import { HealthGoals } from '../../services/api';
import Input from '../ui/Input';
import Select from '../ui/Select';
import Card from '../ui/Card';
import LoadingSpinner from '../LoadingSpinner';

interface GoalsFormProps {
  initialData?: Partial<HealthGoals>;
  onSubmit: (data: HealthGoals) => void;
  onNext?: () => void;
  onBack?: () => void;
  isLoading?: boolean;
}

export const GoalsForm: React.FC<GoalsFormProps> = ({
  initialData = {},
  onSubmit,
  onNext,
  onBack,
  isLoading = false,
}) => {
  const [formData, setFormData] = useState<HealthGoals>({
    primary_goal: initialData.primary_goal || 'maintenance',
    target_weight_kg: initialData.target_weight_kg || undefined,
    timeline_weeks: initialData.timeline_weeks || undefined,
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (formData.primary_goal === 'fat_loss' || formData.primary_goal === 'muscle_gain') {
      if (!formData.target_weight_kg) {
        newErrors.target_weight_kg = 'Target weight is required for weight goals';
      } else if (formData.target_weight_kg < 30 || formData.target_weight_kg > 300) {
        newErrors.target_weight_kg = 'Target weight must be between 30 and 300 kg';
      }

      if (!formData.timeline_weeks) {
        newErrors.timeline_weeks = 'Timeline is required for weight goals';
      } else if (formData.timeline_weeks < 1 || formData.timeline_weeks > 104) {
        newErrors.timeline_weeks = 'Timeline must be between 1 and 104 weeks (2 years)';
      }
    }

    if (formData.primary_goal === 'muscle_gain') {
      if (!formData.timeline_weeks) {
        newErrors.timeline_weeks = 'Timeline is required for muscle gain goals';
      } else if (formData.timeline_weeks < 4 || formData.timeline_weeks > 104) {
        newErrors.timeline_weeks = 'Timeline must be between 4 and 104 weeks';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (validateForm()) {
      onSubmit(formData);
      if (onNext) {
        onNext();
      }
    }
  };

  const handleInputChange = (field: keyof HealthGoals, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  const goalTypeOptions = [
    { value: 'fat_loss', label: 'Fat Loss' },
    { value: 'muscle_gain', label: 'Muscle Gain' },
    { value: 'maintenance', label: 'Maintain Current Weight' },
  ];

  const getGoalDescription = (goalType: string) => {
    switch (goalType) {
      case 'fat_loss':
        return 'Lose weight through a caloric deficit while maintaining muscle mass.';
      case 'muscle_gain':
        return 'Build muscle mass through optimized protein intake and strength training support.';
      case 'maintenance':
        return 'Maintain current weight while optimizing nutrition and health.';
      default:
        return '';
    }
  };

  const showWeightTarget = formData.primary_goal === 'fat_loss' || formData.primary_goal === 'muscle_gain';
  const showTimeline = formData.primary_goal !== 'maintenance';

  return (
    <Card className="max-w-4xl mx-auto border-neutral-200 dark:border-neutral-800 shadow-xl shadow-neutral-200/50 dark:shadow-none rounded-3xl overflow-hidden">
      <div className="p-8 sm:p-12 space-y-10">
        <div className="space-y-2 text-left">
          <h2 className="text-3xl font-bold text-neutral-900 dark:text-white">Health Goals</h2>
          <p className="text-neutral-500 dark:text-neutral-400">
            What would you like to achieve with your personalized diet plan?
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-12">
          {/* Section 1: Primary Objective */}
          <div className="space-y-6">
            <div className="flex items-center gap-3 border-b border-neutral-100 dark:border-neutral-800 pb-2 text-left">
              <div className="h-2 w-2 rounded-full bg-emerald-500" />
              <h3 className="text-sm font-bold uppercase tracking-widest text-neutral-400 text-left">Primary Objective</h3>
            </div>

            <div className="space-y-4 text-left">
              <Select
                label="What is your main goal?"
                id="goalType"
                value={formData.primary_goal}
                onChange={(e: React.ChangeEvent<HTMLSelectElement>) => handleInputChange('primary_goal', e.target.value)}
                options={goalTypeOptions}
                error={errors.goal_type}
                required
                fullWidth
              />
              {formData.primary_goal && (
                <div className="p-4 bg-emerald-50 dark:bg-emerald-900/20 rounded-2xl border border-emerald-100 dark:border-emerald-800 flex items-start gap-3">
                  <div className="mt-0.5 text-emerald-600 dark:text-emerald-400">
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <p className="text-sm text-emerald-800 dark:text-emerald-300 leading-relaxed font-medium">
                    {getGoalDescription(formData.primary_goal)}
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Section 2: Target Metrics (Conditional) */}
          {(showWeightTarget || showTimeline) && (
            <div className="space-y-6">
              <div className="flex items-center gap-3 border-b border-neutral-100 dark:border-neutral-800 pb-2 text-left">
                <div className="h-2 w-2 rounded-full bg-emerald-500" />
                <h3 className="text-sm font-bold uppercase tracking-widest text-neutral-400 text-left">Targets & Timeline</h3>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-8 text-left">
                {showWeightTarget && (
                  <Input
                    label="Target Weight (kg)"
                    id="targetWeight"
                    type="number"
                    value={formData.target_weight_kg || ''}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => handleInputChange('target_weight_kg',
                      e.target.value ? parseFloat(e.target.value) : undefined)}
                    placeholder="e.g. 65"
                    min="30"
                    max="300"
                    step="0.1"
                    error={errors.target_weight_kg}
                    helperText={formData.primary_goal === 'fat_loss' ? 'Desired weight to reach' : 'Desired bulk target'}
                    required
                    fullWidth
                  />
                )}
                {showTimeline && (
                  <Input
                    label="Timeline (weeks)"
                    id="timeline"
                    type="number"
                    value={formData.timeline_weeks || ''}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => handleInputChange('timeline_weeks',
                      e.target.value ? parseInt(e.target.value) : undefined)}
                    placeholder="e.g. 12"
                    min={formData.primary_goal === 'muscle_gain' ? "4" : "1"}
                    max="104"
                    error={errors.timeline_weeks}
                    helperText="Duration to achieve this goal"
                    required
                    fullWidth
                  />
                )}
              </div>
            </div>
          )}

          {/* Guidelines info box */}
          <div className="bg-neutral-50 dark:bg-neutral-800/50 rounded-[2rem] p-8 border border-neutral-100 dark:border-neutral-800 space-y-4">
            <h3 className="text-sm font-bold uppercase tracking-widest text-neutral-400 flex items-center gap-2">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Goal Guidelines
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-left">
              <div className="space-y-1">
                <p className="text-xs font-bold text-neutral-400">WEIGHT CONTROL</p>
                <p className="text-sm text-neutral-600 dark:text-neutral-300">Safe weight loss: 0.5-1 kg per week</p>
              </div>
              <div className="space-y-1">
                <p className="text-xs font-bold text-neutral-400">MUSCLE GROWTH</p>
                <p className="text-sm text-neutral-600 dark:text-neutral-300">Bulk target: 0.25-0.5 kg per week</p>
              </div>
            </div>
          </div>

          {/* Navigation */}
          <div className="flex items-center justify-between pt-8">
            <button
              type="button"
              onClick={onBack}
              disabled={isLoading}
              className="px-8 py-4 font-bold text-neutral-500 hover:text-neutral-700 transition-colors"
            >
              Back
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="px-12 py-4 bg-emerald-600 text-white rounded-2xl font-bold shadow-lg shadow-emerald-500/20 hover:bg-emerald-700 hover:shadow-emerald-500/40 transition-all active:scale-95 disabled:opacity-50 flex items-center justify-center gap-3"
            >
              <span>Continue</span>
              {isLoading ? (
                <LoadingSpinner size="sm" className="opacity-80" message='' />
              ) : (
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                </svg>
              )}
            </button>
          </div>
        </form>
      </div>
    </Card>
  );
};

export default GoalsForm;