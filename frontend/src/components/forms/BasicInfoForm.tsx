import React, { useState } from 'react';
import { UserProfile } from '../../services/api';
import Input from '../ui/Input';
import Select from '../ui/Select';
import Card from '../ui/Card';
import LoadingSpinner from '../LoadingSpinner';

interface BasicInfoFormProps {
  initialData?: Partial<UserProfile>;
  onSubmit: (data: UserProfile) => void;
  onNext?: () => void;
  isLoading?: boolean;
}

export const BasicInfoForm: React.FC<BasicInfoFormProps> = ({
  initialData = {},
  onSubmit,
  onNext,
  isLoading = false,
}) => {
  const [formData, setFormData] = useState<UserProfile>({
    name: initialData.name || '',
    age: initialData.age || 25,
    gender: initialData.gender || 'male',
    height_cm: initialData.height_cm || 170,
    weight_kg: initialData.weight_kg || 70,
    body_fat_percentage: initialData.body_fat_percentage || undefined,
    muscle_mass_kg: initialData.muscle_mass_kg || undefined,
    activity_level: initialData.activity_level || 'moderately_active',
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Name is required';
    } else if (formData.name.trim().length < 2) {
      newErrors.name = 'Name must be at least 2 characters';
    }

    if (formData.age < 13 || formData.age > 120) {
      newErrors.age = 'Age must be between 13 and 120';
    }

    if (formData.height_cm < 100 || formData.height_cm > 250) {
      newErrors.height_cm = 'Height must be between 100 and 250 cm';
    }

    if (formData.weight_kg < 30 || formData.weight_kg > 300) {
      newErrors.weight_kg = 'Weight must be between 30 and 300 kg';
    }

    if (formData.body_fat_percentage !== undefined) {
      if (formData.body_fat_percentage < 3 || formData.body_fat_percentage > 50) {
        newErrors.body_fat_percentage = 'Body fat percentage must be between 3% and 50%';
      }
    }

    if (formData.muscle_mass_kg !== undefined) {
      if (formData.muscle_mass_kg < 10 || formData.muscle_mass_kg > 100) {
        newErrors.muscle_mass_kg = 'Muscle mass must be between 10 and 100 kg';
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

  const handleInputChange = (field: keyof UserProfile, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  const genderOptions = [
    { value: 'male', label: 'Male' },
    { value: 'female', label: 'Female' },
    { value: 'other', label: 'Other' },
  ];

  const activityOptions = [
    { value: 'sedentary', label: 'Sedentary' },
    { value: 'lightly_active', label: 'Lightly Active' },
    { value: 'moderately_active', label: 'Moderately Active' },
    { value: 'very_active', label: 'Very Active' },
    { value: 'extremely_active', label: 'Extremely Active' },
  ];

  const getActivityDescription = (level: string) => {
    switch (level) {
      case 'sedentary':
        return 'Little to no exercise';
      case 'lightly_active':
        return 'Light exercise 1-3 days/week';
      case 'moderately_active':
        return 'Moderate exercise 3-5 days/week';
      case 'very_active':
        return 'Hard exercise 6-7 days/week';
      case 'extremely_active':
        return 'Very hard exercise, physical job';
      default:
        return '';
    }
  };

  return (
    <Card className="max-w-4xl mx-auto border-neutral-200 dark:border-neutral-800 shadow-xl shadow-neutral-200/50 dark:shadow-none rounded-3xl overflow-hidden">
      <div className="p-8 sm:p-12 space-y-10">
        <div className="space-y-2 text-left">
          <h2 className="text-3xl font-bold text-neutral-900 dark:text-white">Basic Information</h2>
          <p className="text-neutral-500 dark:text-neutral-400">
            Tell us about yourself so we can create a personalized diet plan.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-12">
          {/* Section 1: Personal Information */}
          <div className="space-y-6 text-left">
            <div className="flex items-center gap-3 border-b border-neutral-100 dark:border-neutral-800 pb-2 text-left">
              <div className="h-2 w-2 rounded-full bg-emerald-500" />
              <h3 className="text-sm font-bold uppercase tracking-widest text-neutral-400 text-left">Personal Information</h3>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="md:col-span-1">
                <Input
                  label="Full Name"
                  id="name"
                  type="text"
                  value={formData.name}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => handleInputChange('name', e.target.value)}
                  placeholder="e.g. John Doe"
                  error={errors.name}
                  required
                  fullWidth
                />
              </div>
              <div>
                <Input
                  label="Age"
                  id="age"
                  type="number"
                  value={formData.age}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => handleInputChange('age', parseInt(e.target.value) || 0)}
                  placeholder="25"
                  min="13"
                  max="120"
                  error={errors.age}
                  required
                  fullWidth
                />
              </div>
              <div>
                <Select
                  label="Gender"
                  id="gender"
                  value={formData.gender}
                  onChange={(e: React.ChangeEvent<HTMLSelectElement>) => handleInputChange('gender', e.target.value)}
                  options={genderOptions}
                  error={errors.gender}
                  required
                  fullWidth
                />
              </div>
            </div>
          </div>

          {/* Section 2: Body Metrics */}
          <div className="space-y-6 text-left">
            <div className="flex items-center gap-3 border-b border-neutral-100 dark:border-neutral-800 pb-2 text-left">
              <div className="h-2 w-2 rounded-full bg-emerald-500" />
              <h3 className="text-sm font-bold uppercase tracking-widest text-neutral-400 text-left">Body Metrics</h3>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Input
                label="Height (cm)"
                id="height"
                type="number"
                value={formData.height_cm}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => handleInputChange('height_cm', parseInt(e.target.value))}
                placeholder="170"
                min="100"
                max="250"
                error={errors.height_cm}
                required
                fullWidth
              />
              <Input
                label="Weight (kg)"
                id="weight"
                type="number"
                value={formData.weight_kg}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => handleInputChange('weight_kg', parseFloat(e.target.value))}
                placeholder="70"
                min="30"
                max="300"
                step="0.1"
                error={errors.weight_kg}
                required
                fullWidth
              />
            </div>
          </div>

          {/* Section 3: Activity Level */}
          <div className="space-y-6 text-left">
            <div className="flex items-center gap-3 border-b border-neutral-100 dark:border-neutral-800 pb-2 text-left">
              <div className="h-2 w-2 rounded-full bg-emerald-500" />
              <h3 className="text-sm font-bold uppercase tracking-widest text-neutral-400 text-left">Lifestyle</h3>
            </div>

            <div>
              <Select
                label="Typical Activity Level"
                id="activity"
                value={formData.activity_level}
                onChange={(e: React.ChangeEvent<HTMLSelectElement>) => handleInputChange('activity_level', e.target.value)}
                options={activityOptions}
                error={errors.activity_level}
                required
                fullWidth
              />
              {formData.activity_level && (
                <div className="mt-4 p-4 bg-neutral-50 dark:bg-neutral-800/50 rounded-2xl border border-neutral-100 dark:border-neutral-800 flex items-start gap-3">
                  <div className="mt-0.5 text-emerald-500">
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <p className="text-sm text-neutral-600 dark:text-neutral-400 leading-relaxed italic">
                    {getActivityDescription(formData.activity_level)}
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Section 4: Optional Metrics */}
          <div className="space-y-6 text-left">
            <div className="flex items-center gap-3 border-b border-neutral-100 dark:border-neutral-800 pb-2 text-left">
              <div className="h-2 w-2 rounded-full bg-neutral-300 dark:bg-neutral-700" />
              <h3 className="text-sm font-bold uppercase tracking-widest text-neutral-400 text-left">Advanced Metrics (Optional)</h3>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Input
                label="Body Fat Percentage (%)"
                id="bodyFat"
                type="number"
                value={formData.body_fat_percentage || ''}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => handleInputChange('body_fat_percentage',
                  e.target.value ? parseFloat(e.target.value) : undefined)}
                placeholder="e.g. 15"
                min="3"
                max="50"
                step="0.1"
                error={errors.body_fat_percentage}
                fullWidth
              />
              <Input
                label="Muscle Mass (kg)"
                id="muscleMass"
                type="number"
                value={formData.muscle_mass_kg || ''}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => handleInputChange('muscle_mass_kg',
                  e.target.value ? parseFloat(e.target.value) : undefined)}
                placeholder="e.g. 35"
                min="10"
                max="100"
                step="0.1"
                error={errors.muscle_mass_kg}
                fullWidth
              />
            </div>
          </div>

          {/* Navigation */}
          <div className="flex justify-end pt-8">
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

export default BasicInfoForm;