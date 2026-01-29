import React, { useState } from 'react';
import { HealthGoals } from '../../services/api';
import Button from '../ui/Button';
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
    <Card className="max-w-2xl mx-auto">
      <div className="p-6">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6 text-left">Health Goals</h2>
        <p className="text-gray-600 dark:text-gray-300 mb-8 text-left">
          What would you like to achieve with your diet plan?
        </p>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Goal Type */}
          <div>
            <label htmlFor="goalType" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 text-left">
              Primary Goal *
            </label>
            <Select
              id="goalType"
              value={formData.primary_goal}
              onChange={(e: React.ChangeEvent<HTMLSelectElement>) => handleInputChange('primary_goal', e.target.value)}
              options={goalTypeOptions}
              error={errors.goal_type}
              required
            />
            {formData.primary_goal && (
              <p className="mt-2 text-sm text-gray-600 dark:text-gray-400 text-left">
                {getGoalDescription(formData.primary_goal)}
              </p>
            )}
          </div>

          {/* Target Weight (conditional) */}
          {showWeightTarget && (
            <div>
              <label htmlFor="targetWeight" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 text-left">
                Target Weight (kg) *
              </label>
              <Input
                id="targetWeight"
                type="number"
                value={formData.target_weight_kg || ''}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => handleInputChange('target_weight_kg', 
                  e.target.value ? parseFloat(e.target.value) : undefined)}
                placeholder="65"
                min="30"
                max="300"
                step="0.1"
                error={errors.target_weight_kg}
                required
              />
              <p className="mt-1 text-sm text-gray-500 dark:text-gray-400 text-left">
                {formData.primary_goal === 'fat_loss' 
                  ? 'Enter your desired weight to lose to'
                  : 'Enter your desired weight to gain to'
                }
              </p>
            </div>
          )}

          {/* Timeline (conditional) */}
          {showTimeline && (
            <div>
              <label htmlFor="timeline" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 text-left">
                Timeline (weeks) *
              </label>
              <Input
                id="timeline"
                type="number"
                value={formData.timeline_weeks || ''}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => handleInputChange('timeline_weeks', 
                  e.target.value ? parseInt(e.target.value) : undefined)}
                placeholder="12"
                min={formData.primary_goal === 'muscle_gain' ? "4" : "1"}
                max="104"
                error={errors.timeline_weeks}
                required
              />
              <p className="mt-1 text-sm text-gray-500 dark:text-gray-400 text-left">
                {formData.primary_goal === 'fat_loss' && 'Recommended: 0.5-1 kg per week (safe weight loss)'}
                {formData.primary_goal === 'muscle_gain' && 'Recommended: Minimum 4 weeks for noticeable results'}
              </p>
            </div>
          )}

          {/* Goal Information */}
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
            <h3 className="text-sm font-medium text-blue-900 dark:text-blue-200 mb-2">
              💡 Goal Guidelines
            </h3>
            <ul className="text-sm text-blue-800 dark:text-blue-300 space-y-1">
              <li>• Safe weight loss: 0.5-1 kg per week</li>
              <li>• Healthy weight gain: 0.25-0.5 kg per week</li>
              <li>• Muscle gain works best with adequate protein and strength training</li>
              <li>• Maintenance focuses on balanced nutrition and health optimization</li>
            </ul>
          </div>

          {/* Navigation Buttons */}
          <div className="flex justify-between pt-6">
            <Button
              type="button"
              variant="outline"
              onClick={onBack}
              disabled={isLoading}
            >
              Back
            </Button>
            <Button
              type="submit"
              disabled={isLoading}
              className="px-8 py-2 flex items-center"
            >
              Continue
              {isLoading && <LoadingSpinner size="sm" className="ml-2" message=''/>}
            </Button>
          </div>
        </form>
      </div>
    </Card>
  );
};

export default GoalsForm;