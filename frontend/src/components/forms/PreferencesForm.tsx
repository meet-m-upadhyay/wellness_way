import React, { useState } from 'react';
import { DietPreferences } from '../../services/api';
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
    cuisine: initialData.cuisine || 'indian',
    reuse_ingredients: initialData.reuse_ingredients || false,
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
    <Card className="max-w-4xl mx-auto border-neutral-200 dark:border-neutral-800 shadow-xl shadow-neutral-200/50 dark:shadow-none rounded-3xl overflow-hidden">
      <div className="p-8 sm:p-12 space-y-10">
        <div className="space-y-2 text-left">
          <h2 className="text-3xl font-bold text-neutral-900 dark:text-white">Diet & Preferences</h2>
          <p className="text-neutral-500 dark:text-neutral-400 text-left">
            Customize your nutrition plan to fit your lifestyle and dietary needs.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-12">
          {/* Section 1: Dietary Style */}
          <div className="space-y-6">
            <div className="flex items-center gap-3 border-b border-neutral-100 dark:border-neutral-800 pb-2 text-left">
              <div className="h-2 w-2 rounded-full bg-emerald-500" />
              <h3 className="text-sm font-bold uppercase tracking-widest text-neutral-400 text-left">Section 1: Dietary Style</h3>
            </div>

            <div className="space-y-4 text-left">
              <Select
                label="Primary Dietary Style"
                id="dietaryStyle"
                value={formData.diet_type}
                onChange={(e: React.ChangeEvent<HTMLSelectElement>) => handleInputChange('diet_type', e.target.value)}
                options={dietaryStyleOptions}
                error={errors.dietary_style}
                required
                fullWidth
              />
              {formData.diet_type && (
                <div className="p-4 bg-emerald-50 dark:bg-emerald-900/20 rounded-2xl border border-emerald-100 dark:border-emerald-800 flex items-start gap-3">
                  <div className="mt-0.5 text-emerald-600 dark:text-emerald-400">
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <p className="text-sm text-emerald-800 dark:text-emerald-300 leading-relaxed font-medium">
                    {getDietaryStyleDescription(formData.diet_type)}
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Section 2: Food Allergies */}
          <div className="space-y-6 text-left">
            <div className="flex items-center gap-3 border-b border-neutral-100 dark:border-neutral-800 pb-2 text-left">
              <div className="h-2 w-2 rounded-full bg-red-500" />
              <h3 className="text-sm font-bold uppercase tracking-widest text-neutral-400 text-left">Section 2: Food Allergies</h3>
            </div>

            <div className="space-y-4">
              <div className="flex flex-col gap-1.5">
                <label className="text-sm font-semibold text-neutral-700 dark:text-neutral-300">Add Allergies</label>
                <div className="flex gap-2">
                  <Input
                    id="newAllergy"
                    type="text"
                    value={newAllergy}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setNewAllergy(e.target.value)}
                    onKeyPress={(e: React.KeyboardEvent<HTMLInputElement>) => e.key === 'Enter' && (e.preventDefault(), addAllergy())}
                    placeholder="e.g. Peanuts, Shellfish"
                    fullWidth
                  />
                  <button
                    type="button"
                    onClick={addAllergy}
                    disabled={!newAllergy.trim()}
                    className="px-6 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 rounded-xl font-bold hover:bg-red-100 transition-colors border border-red-100 dark:border-red-800 disabled:opacity-50"
                  >
                    Add
                  </button>
                </div>
              </div>

              <div className="space-y-3">
                <p className="text-xs font-bold text-neutral-400 uppercase tracking-tighter">Quick Add:</p>
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
                      disabled={formData.allergies.includes(allergy)}
                      className="px-3 py-1.5 text-xs font-semibold bg-neutral-50 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-400 rounded-full border border-neutral-200 dark:border-neutral-700 hover:bg-neutral-100 transition-colors disabled:bg-emerald-50 disabled:text-emerald-600 disabled:border-emerald-100"
                    >
                      + {allergy}
                    </button>
                  ))}
                </div>
              </div>

              {formData.allergies.length > 0 && (
                <div className="pt-2">
                  <div className="flex flex-wrap gap-2.5">
                    {formData.allergies.map(allergy => (
                      <span
                        key={allergy}
                        className="inline-flex items-center gap-2 px-4 py-2 bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 rounded-full text-xs font-bold border border-red-100 dark:border-red-800 animate-scale-in"
                      >
                        {allergy}
                        <button
                          type="button"
                          onClick={() => removeAllergy(allergy)}
                          className="hover:bg-red-200 dark:hover:bg-red-800 rounded-full p-0.5 transition-colors"
                        >
                          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                          </svg>
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

          {/* Section 3: Foods to Avoid */}
          <div className="space-y-6 text-left">
            <div className="flex items-center gap-3 border-b border-neutral-100 dark:border-neutral-800 pb-2 text-left">
              <div className="h-2 w-2 rounded-full bg-amber-500" />
              <h3 className="text-sm font-bold uppercase tracking-widest text-neutral-400 text-left">Section 3: Foods to Avoid</h3>
            </div>

            <div className="space-y-4">
              <div className="flex flex-col gap-1.5">
                <label className="text-sm font-semibold text-neutral-700 dark:text-neutral-300">Exclude Foods</label>
                <p className="text-xs text-neutral-500 mb-1">Items you prefer to skip, but aren't allergic to.</p>
                <div className="flex gap-2">
                  <Input
                    id="newAvoid"
                    type="text"
                    value={newFoodToAvoid}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setNewFoodToAvoid(e.target.value)}
                    onKeyPress={(e: React.KeyboardEvent<HTMLInputElement>) => e.key === 'Enter' && (e.preventDefault(), addFoodToAvoid())}
                    placeholder="e.g. Cilantro, Mushrooms"
                    fullWidth
                  />
                  <button
                    type="button"
                    onClick={addFoodToAvoid}
                    disabled={!newFoodToAvoid.trim()}
                    className="px-6 bg-amber-50 dark:bg-amber-900/20 text-amber-600 dark:text-amber-400 rounded-xl font-bold hover:bg-amber-100 transition-colors border border-amber-100 dark:border-amber-800 disabled:opacity-50"
                  >
                    Add
                  </button>
                </div>
              </div>

              {formData.foods_to_avoid.length > 0 && (
                <div className="pt-2">
                  <div className="flex flex-wrap gap-2.5">
                    {formData.foods_to_avoid.map(food => (
                      <span
                        key={food}
                        className="inline-flex items-center gap-2 px-4 py-2 bg-neutral-100 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300 rounded-full text-xs font-bold border border-neutral-200 dark:border-neutral-700"
                      >
                        {food}
                        <button
                          type="button"
                          onClick={() => removeFoodToAvoid(food)}
                          className="hover:bg-neutral-200 dark:hover:bg-neutral-700 rounded-full p-0.5 transition-colors"
                        >
                          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                          </svg>
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

          {/* Section 4: Lifestyle & Budget Constraints */}
          <div className="space-y-6 text-left">
            <div className="flex items-center gap-3 border-b border-neutral-100 dark:border-neutral-800 pb-2 text-left">
              <div className="h-2 w-2 rounded-full bg-blue-500" />
              <h3 className="text-sm font-bold uppercase tracking-widest text-neutral-400 text-left">Section 4: Lifestyle & Budget</h3>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div className="space-y-2">
                <div className="flex items-end justify-between">
                  <label htmlFor="budget" className="text-sm font-semibold text-neutral-700 dark:text-neutral-300">Budget Constraints</label>
                  <span className="text-[10px] font-bold text-neutral-400 uppercase">{(formData.budget_constraints || '').length}/500</span>
                </div>
                <textarea
                  id="budget"
                  value={formData.budget_constraints}
                  onChange={(e) => handleInputChange('budget_constraints', e.target.value)}
                  placeholder="e.g. Economical, student budget, prefer local markets..."
                  rows={4}
                  className="w-full px-4 py-3 bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-2xl text-neutral-900 dark:text-white placeholder-neutral-400 focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all outline-none resize-none"
                  maxLength={500}
                />
              </div>

              <div className="space-y-2">
                <div className="flex items-end justify-between">
                  <label htmlFor="lifestyle" className="text-sm font-semibold text-neutral-700 dark:text-neutral-300">Lifestyle Constraints</label>
                  <span className="text-[10px] font-bold text-neutral-400 uppercase">{(formData.lifestyle_constraints || '').length}/500</span>
                </div>
                <textarea
                  id="lifestyle"
                  value={formData.lifestyle_constraints}
                  onChange={(e) => handleInputChange('lifestyle_constraints', e.target.value)}
                  placeholder="e.g. Minimal cooking time, meal prep friendly, busy weekdays..."
                  rows={4}
                  className="w-full px-4 py-3 bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-2xl text-neutral-900 dark:text-white placeholder-neutral-400 focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all outline-none resize-none"
                  maxLength={500}
                />
              </div>
            </div>
          </div>

          {/* Section 5: Plan Customization */}
          <div className="space-y-6 text-left">
            <div className="flex items-center gap-3 border-b border-neutral-100 dark:border-neutral-800 pb-2 text-left">
              <div className="h-2 w-2 rounded-full bg-purple-500" />
              <h3 className="text-sm font-bold uppercase tracking-widest text-neutral-400 text-left">Section 5: Plan Customization</h3>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div className="space-y-4">
                <Select
                  label="Preferred Cuisine"
                  id="cuisine"
                  value={formData.cuisine}
                  onChange={(e: React.ChangeEvent<HTMLSelectElement>) => handleInputChange('cuisine', e.target.value)}
                  options={[
                    { value: 'indian', label: 'Indian' },
                    { value: 'continental', label: 'Continental' },
                    { value: 'mediterranean', label: 'Mediterranean' },
                    { value: 'asian', label: 'Asian' },
                    { value: 'mexican', label: 'Mexican' },
                  ]}
                  fullWidth
                />
                <p className="text-xs text-neutral-500">
                  Plans will be tailored to this cuisine's typical flavors and ingredients.
                </p>
              </div>

              <div className="space-y-4">
                <Input
                  label="Meals Per Day"
                  id="mealsPerDay"
                  type="number"
                  value={formData.meals_per_day}
                  disabled
                  fullWidth
                />
                <p className="text-xs text-neutral-500 italic">
                  Multiple meals support is coming soon! For now, we optimize for 3 balanced meals.
                </p>
              </div>
            </div>

            <div className="p-6 bg-purple-50 dark:bg-purple-900/20 rounded-2xl border border-purple-100 dark:border-purple-800 space-y-4">
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <h4 className="text-sm font-bold text-purple-900 dark:text-purple-100">Reuse Daily Ingredients</h4>
                  <p className="text-xs text-purple-700 dark:text-purple-300">
                    Saves time and reduces waste by repeating base ingredients (e.g., Chicken, Paneer, Tofu) across daily meals.
                  </p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    className="sr-only peer"
                    checked={formData.reuse_ingredients}
                    onChange={(e) => handleInputChange('reuse_ingredients', e.target.checked)}
                  />
                  <div className="w-11 h-6 bg-neutral-200 peer-focus:outline-none dark:bg-neutral-700 rounded-full peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-neutral-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
                </label>
              </div>
            </div>
          </div>

          {/* Navigation Buttons */}
          <div className="flex justify-between pt-8 border-t border-neutral-100 dark:border-neutral-800">
            <button
              type="button"
              onClick={onBack}
              disabled={isLoading}
              className="px-8 py-4 font-bold text-neutral-400 hover:text-neutral-600 dark:hover:text-neutral-200 transition-colors"
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
        </form >
      </div >
    </Card >
  );
};

export default PreferencesForm;