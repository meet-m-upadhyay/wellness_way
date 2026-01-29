import React, { useState } from 'react';
import { DietPreferences } from '../../services/api';
import Button from '../ui/Button';
import Input from '../ui/Input';
import Select from '../ui/Select';
import Card from '../ui/Card';
import LoadingSpinner from '../LoadingSpinner';

interface PreferencesFormProps {
  initialData?: Partial<DietPreferences>;
  onSubmit: (data: DietPreferences) => void;
  onNext?: () => void;
  onBack?: () => void;
  isLoading?: boolean;
}

export const PreferencesForm: React.FC<PreferencesFormProps> = ({
  initialData = {},
  onSubmit,
  onNext,
  onBack,
  isLoading = false,
}) => {
  const [formData, setFormData] = useState<DietPreferences>({
    diet_type: initialData.diet_type || 'vegetarian',
    allergies: initialData.allergies || [],
    foods_to_avoid: initialData.foods_to_avoid || [],
    meals_per_day: initialData.meals_per_day || 3,
    budget_constraints: initialData.budget_constraints || '',
    lifestyle_constraints: initialData.lifestyle_constraints || '',
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [newAllergy, setNewAllergy] = useState('');
  const [newFoodToAvoid, setNewFoodToAvoid] = useState('');

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    // Basic validation - most fields are optional
    if (formData.allergies.length > 20) {
      newErrors.allergies = 'Too many allergies listed (maximum 20)';
    }

    if (formData.foods_to_avoid.length > 30) {
      newErrors.foods_to_avoid = 'Too many foods to avoid listed (maximum 30)';
    }

    if (formData.budget_constraints && formData.budget_constraints.length > 500) {
      newErrors.budget_constraints = 'Budget constraints description too long (maximum 500 characters)';
    }

    if (formData.lifestyle_constraints && formData.lifestyle_constraints.length > 500) {
      newErrors.lifestyle_constraints = 'Lifestyle constraints description too long (maximum 500 characters)';
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

  const handleInputChange = (field: keyof DietPreferences, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  const addAllergy = () => {
    if (newAllergy.trim() && !formData.allergies.includes(newAllergy.trim())) {
      handleInputChange('allergies', [...formData.allergies, newAllergy.trim()]);
      setNewAllergy('');
    }
  };

  const removeAllergy = (allergy: string) => {
    handleInputChange('allergies', formData.allergies.filter(a => a !== allergy));
  };

  const addFoodToAvoid = () => {
    if (newFoodToAvoid.trim() && !formData.foods_to_avoid.includes(newFoodToAvoid.trim())) {
      handleInputChange('foods_to_avoid', [...formData.foods_to_avoid, newFoodToAvoid.trim()]);
      setNewFoodToAvoid('');
    }
  };

  const removeFoodToAvoid = (food: string) => {
    handleInputChange('foods_to_avoid', formData.foods_to_avoid.filter(f => f !== food));
  };

  const dietaryStyleOptions = [
    { value: 'vegetarian', label: 'Vegetarian (No meat)' },
    { value: 'non_vegetarian', label: 'Non-Vegetarian (Includes meat)' },
    { value: 'vegan', label: 'Vegan (No animal products)' },
  ];

  const getDietaryStyleDescription = (style: string) => {
    switch (style) {
      case 'vegetarian':
        return 'Plant-based diet that excludes meat but may include dairy and eggs.';
      case 'non_vegetarian':
        return 'Includes all food groups including meat, poultry, and fish.';
      case 'vegan':
        return 'Plant-based diet that excludes all animal products.';
      default:
        return '';
    }
  };

  const commonAllergies = [
    'Peanuts', 'Tree nuts', 'Shellfish', 'Fish', 'Eggs', 'Milk', 'Soy', 'Wheat', 'Sesame'
  ];

  return (
    <Card className="max-w-2xl mx-auto">
      <div className="p-6">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6 text-left">Diet Preferences</h2>
        <p className="text-gray-600 dark:text-gray-300 mb-8 text-left">
          Tell us about your dietary preferences, restrictions, and lifestyle needs.
        </p>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Dietary Style */}
          <div>
            <label htmlFor="dietaryStyle" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 text-left">
              Dietary Style *
            </label>
            <Select
              id="dietaryStyle"
              value={formData.diet_type}
              onChange={(e: React.ChangeEvent<HTMLSelectElement>) => handleInputChange('diet_type', e.target.value)}
              options={dietaryStyleOptions}
              error={errors.dietary_style}
              required
            />
            {formData.diet_type && (
              <p className="mt-2 text-sm text-gray-600 dark:text-gray-400 text-left">
                {getDietaryStyleDescription(formData.diet_type)}
              </p>
            )}
          </div>

          {/* Allergies */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 text-left">
              Food Allergies
            </label>
            <div className="space-y-3">
              <div className="flex gap-2">
                <Input
                  type="text"
                  value={newAllergy}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setNewAllergy(e.target.value)}
                  placeholder="Enter an allergy"
                  onKeyPress={(e: React.KeyboardEvent<HTMLInputElement>) => e.key === 'Enter' && (e.preventDefault(), addAllergy())}
                />
                <Button
                  type="button"
                  variant="outline"
                  onClick={addAllergy}
                  disabled={!newAllergy.trim()}
                >
                  Add
                </Button>
              </div>
              
              {/* Common allergies quick add */}
              <div>
                <p className="text-xs text-gray-500 dark:text-gray-400 mb-2 text-left">Quick add common allergies:</p>
                <div className="flex flex-wrap gap-2">
                  {commonAllergies.map(allergy => (
                    <button
                      key={allergy}
                      type="button"
                      onClick={() => {
                        if (!formData.allergies.includes(allergy)) {
                          handleInputChange('allergies', [...formData.allergies, allergy]);
                        }
                      }}
                      className="px-2 py-1 text-xs bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-md transition-colors"
                      disabled={formData.allergies.includes(allergy)}
                    >
                      {allergy}
                    </button>
                  ))}
                </div>
              </div>

              {/* Current allergies */}
              {formData.allergies.length > 0 && (
                <div>
                  <p className="text-sm text-gray-700 dark:text-gray-300 mb-2">Current allergies:</p>
                  <div className="flex flex-wrap gap-2">
                    {formData.allergies.map(allergy => (
                      <span
                        key={allergy}
                        className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300"
                      >
                        {allergy}
                        <button
                          type="button"
                          onClick={() => removeAllergy(allergy)}
                          className="ml-2 text-red-600 dark:text-red-400 hover:text-red-800 dark:hover:text-red-200"
                        >
                          ×
                        </button>
                      </span>
                    ))}
                  </div>
                </div>
              )}
              {errors.allergies && (
                <p className="text-sm text-red-600 dark:text-red-400">{errors.allergies}</p>
              )}
            </div>
          </div>

          {/* Foods to Avoid */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 text-left">
              Foods to Avoid (Preferences)
            </label>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-3 text-left">
              Foods you prefer not to eat (different from allergies)
            </p>
            <div className="space-y-3">
              <div className="flex gap-2">
                <Input
                  type="text"
                  value={newFoodToAvoid}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setNewFoodToAvoid(e.target.value)}
                  placeholder="Enter a food to avoid"
                  onKeyPress={(e: React.KeyboardEvent<HTMLInputElement>) => e.key === 'Enter' && (e.preventDefault(), addFoodToAvoid())}
                />
                <Button
                  type="button"
                  variant="outline"
                  onClick={addFoodToAvoid}
                  disabled={!newFoodToAvoid.trim()}
                >
                  Add
                </Button>
              </div>

              {/* Current foods to avoid */}
              {formData.foods_to_avoid.length > 0 && (
                <div>
                  <p className="text-sm text-gray-700 dark:text-gray-300 mb-2">Foods to avoid:</p>
                  <div className="flex flex-wrap gap-2">
                    {formData.foods_to_avoid.map(food => (
                      <span
                        key={food}
                        className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300"
                      >
                        {food}
                        <button
                          type="button"
                          onClick={() => removeFoodToAvoid(food)}
                          className="ml-2 text-yellow-600 dark:text-yellow-400 hover:text-yellow-800 dark:hover:text-yellow-200"
                        >
                          ×
                        </button>
                      </span>
                    ))}
                  </div>
                </div>
              )}
              {errors.foods_to_avoid && (
                <p className="text-sm text-red-600 dark:text-red-400">{errors.foods_to_avoid}</p>
              )}
            </div>
          </div>

          {/* Budget Constraints */}
          <div>
            <label htmlFor="budget" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 text-left">
              Budget Constraints (Optional)
            </label>
            <textarea
              id="budget"
              value={formData.budget_constraints}
              onChange={(e) => handleInputChange('budget_constraints', e.target.value)}
              placeholder="e.g., Low budget, prefer affordable ingredients, avoid expensive items..."
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-blue-500 dark:focus:border-blue-400 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 placeholder-gray-500 dark:placeholder-gray-400"
              maxLength={500}
            />
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              {(formData.budget_constraints || '').length}/500 characters
            </p>
            {errors.budget_constraints && (
              <p className="text-sm text-red-600 dark:text-red-400">{errors.budget_constraints}</p>
            )}
          </div>

          {/* Lifestyle Constraints */}
          <div>
            <label htmlFor="lifestyle" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 text-left">
              Lifestyle Constraints (Optional)
            </label>
            <textarea
              id="lifestyle"
              value={formData.lifestyle_constraints}
              onChange={(e) => handleInputChange('lifestyle_constraints', e.target.value)}
              placeholder="e.g., Busy schedule, prefer quick meals, no cooking on weekdays, meal prep friendly..."
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-blue-500 dark:focus:border-blue-400 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 placeholder-gray-500 dark:placeholder-gray-400"
              maxLength={500}
            />
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              {(formData.lifestyle_constraints || '').length}/500 characters
            </p>
            {errors.lifestyle_constraints && (
              <p className="text-sm text-red-600 dark:text-red-400">{errors.lifestyle_constraints}</p>
            )}
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

export default PreferencesForm;