import React, { useState } from 'react';
import { UserProfile } from '../../services/api';
import Button from '../ui/Button';
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
    <Card className="max-w-2xl mx-auto">
      <div className="p-6">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6 text-left">Basic Information</h2>
        <p className="text-gray-600 dark:text-gray-300 mb-8 text-left">
          Tell us about yourself so we can create a personalized diet plan.
        </p>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Name */}
          <div>
            <label htmlFor="name" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 text-left">
              Full Name *
            </label>
            <Input
              id="name"
              type="text"
              value={formData.name}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => handleInputChange('name', e.target.value)}
              placeholder="Enter your full name"
              error={errors.name}
              required
            />
          </div>

          {/* Age and Gender */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label htmlFor="age" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 text-left">
                Age *
              </label>
              <Input
                id="age"
                type="number"
                value={formData.age}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => handleInputChange('age', parseInt(e.target.value) || 0)}
                placeholder="25"
                min="13"
                max="120"
                error={errors.age}
                required
              />
            </div>

            <div>
              <label htmlFor="gender" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 text-left">
                Gender *
              </label>
              <Select
                id="gender"
                value={formData.gender}
                onChange={(e: React.ChangeEvent<HTMLSelectElement>) => handleInputChange('gender', e.target.value)}
                options={genderOptions}
                error={errors.gender}
                required
              />
            </div>
          </div>

          {/* Height and Weight */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label htmlFor="height" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 text-left">
                Height (cm) *
              </label>
              <Input
                id="height"
                type="number"
                value={formData.height_cm}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => handleInputChange('height_cm', parseInt(e.target.value))}
                placeholder="170"
                min="100"
                max="250"
                error={errors.height_cm}
                required
              />
            </div>

            <div>
              <label htmlFor="weight" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 text-left">
                Weight (kg) *
              </label>
              <Input
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
              />
            </div>
          </div>

          {/* Activity Level */}
          <div>
            <label htmlFor="activity" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 text-left">
              Activity Level *
            </label>
            <Select
              id="activity"
              value={formData.activity_level}
              className='text-left'
              onChange={(e: React.ChangeEvent<HTMLSelectElement>) => handleInputChange('activity_level', e.target.value)}
              options={activityOptions}
              error={errors.activity_level}
              helperText={formData.activity_level ? getActivityDescription(formData.activity_level) : 'Select your typical activity level'}
              required
            />
          </div>

          {/* Optional Body Composition */}
          <div className="border-t pt-6">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4 text-left">
              Body Composition (Optional)
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4 text-left">
              These measurements help us create more accurate recommendations.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label htmlFor="bodyFat" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 text-left">
                  Body Fat Percentage (%)
                </label>
                <Input
                  id="bodyFat"
                  type="number"
                  value={formData.body_fat_percentage || ''}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => handleInputChange('body_fat_percentage', 
                    e.target.value ? parseFloat(e.target.value) : undefined)}
                  placeholder="15"
                  min="3"
                  max="50"
                  step="0.1"
                  error={errors.body_fat_percentage}
                />
              </div>

              <div>
                <label htmlFor="muscleMass" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 text-left">
                  Muscle Mass (kg)
                </label>
                <Input
                  id="muscleMass"
                  type="number"
                  value={formData.muscle_mass_kg || ''}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => handleInputChange('muscle_mass_kg', 
                    e.target.value ? parseFloat(e.target.value) : undefined)}
                  placeholder="35"
                  min="10"
                  max="100"
                  step="0.1"
                  error={errors.muscle_mass_kg}
                />
              </div>
            </div>
          </div>

          {/* Submit Button */}
          <div className="flex justify-end pt-6">
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

export default BasicInfoForm;