/**
 * Goal Validation Utility
 * 
 * Calculates medically safe weight change targets based on CDC/WHO guidelines:
 *   - Safe weight loss: 0.5–1.0 kg/week
 *   - Safe muscle gain: 0.25–0.5 kg/week
 *   - Minimum healthy BMI: 18.5
 *   - Maximum weight loss: ~10% of body weight per 6-month cycle
 */

export interface GoalValidationInput {
  currentWeight: number;   // kg
  targetWeight: number;    // kg
  timelineWeeks: number;
  primaryGoal: 'fat_loss' | 'muscle_gain' | 'maintenance';
  heightCm: number;
  age: number;
  gender: 'male' | 'female' | 'other';
}

export interface GoalValidationResult {
  isRealistic: boolean;
  warnings: string[];
  adjustedTargetWeight: number;
  adjustedTimelineWeeks: number;
  weeklyRateKg: number;
  safeMaxWeeklyRate: number;
  safeMinWeeklyRate: number;
  minHealthyWeight: number;
}

/** Calculate the minimum healthy weight for a given height (BMI = 18.5) */
function minHealthyWeight(heightCm: number): number {
  const heightM = heightCm / 100;
  return Math.round(18.5 * heightM * heightM * 10) / 10;
}

export function validateGoal(input: GoalValidationInput): GoalValidationResult {
  const {
    currentWeight,
    targetWeight,
    timelineWeeks,
    primaryGoal,
    heightCm,
  } = input;

  const warnings: string[] = [];
  let adjustedTarget = targetWeight;
  let adjustedWeeks = timelineWeeks;
  const minWeight = minHealthyWeight(heightCm);

  // --- Rate limits (kg per week) ---
  let safeMinRate: number;
  let safeMaxRate: number;

  if (primaryGoal === 'fat_loss') {
    safeMinRate = 0.25; // minimum meaningful loss
    safeMaxRate = 1.0;  // CDC max safe loss
  } else if (primaryGoal === 'muscle_gain') {
    safeMinRate = 0.1;
    safeMaxRate = 0.5;
  } else {
    // maintenance — no weight change expected
    return {
      isRealistic: true,
      warnings: [],
      adjustedTargetWeight: currentWeight,
      adjustedTimelineWeeks: timelineWeeks,
      weeklyRateKg: 0,
      safeMaxWeeklyRate: 0,
      safeMinWeeklyRate: 0,
      minHealthyWeight: minWeight,
    };
  }

  const weightDelta = Math.abs(currentWeight - targetWeight);
  const weeklyRate = timelineWeeks > 0 ? weightDelta / timelineWeeks : weightDelta;
  let isRealistic = true;

  // --- Direction checks ---
  if (primaryGoal === 'fat_loss' && targetWeight >= currentWeight) {
    warnings.push(
      `For fat loss your target weight (${targetWeight} kg) should be less than your current weight (${currentWeight} kg).`
    );
    isRealistic = false;
    adjustedTarget = Math.max(currentWeight - (safeMaxRate * timelineWeeks), minWeight);
  }

  if (primaryGoal === 'muscle_gain' && targetWeight <= currentWeight) {
    warnings.push(
      `For muscle gain your target weight (${targetWeight} kg) should be more than your current weight (${currentWeight} kg).`
    );
    isRealistic = false;
    adjustedTarget = currentWeight + (safeMaxRate * timelineWeeks);
  }

  // --- Underweight guard (fat loss only) ---
  if (primaryGoal === 'fat_loss' && targetWeight < minWeight) {
    warnings.push(
      `Your target weight (${targetWeight} kg) would put you below a healthy BMI of 18.5. The minimum safe weight for your height (${heightCm} cm) is ${minWeight} kg.`
    );
    isRealistic = false;
    adjustedTarget = minWeight;
  }

  // --- Rate-too-fast check ---
  if (weeklyRate > safeMaxRate) {
    const safeDelta = safeMaxRate * timelineWeeks;
    const safeTarget =
      primaryGoal === 'fat_loss'
        ? Math.max(currentWeight - safeDelta, minWeight)
        : currentWeight + safeDelta;
    const neededWeeks = Math.ceil(weightDelta / safeMaxRate);

    warnings.push(
      `Your plan requires losing/gaining ${weeklyRate.toFixed(2)} kg/week, which exceeds the safe limit of ${safeMaxRate} kg/week. ` +
      `We recommend either adjusting your target to ${safeTarget.toFixed(1)} kg in ${timelineWeeks} weeks, or extending to ${neededWeeks} weeks.`
    );
    isRealistic = false;
    // Adjust: keep user's target weight if safe, but extend timeline
    if (primaryGoal === 'fat_loss' && targetWeight >= minWeight) {
      adjustedTarget = targetWeight;
      adjustedWeeks = neededWeeks;
    } else if (primaryGoal === 'muscle_gain') {
      adjustedTarget = targetWeight;
      adjustedWeeks = neededWeeks;
    } else {
      adjustedTarget = safeTarget;
      adjustedWeeks = timelineWeeks;
    }
  }

  // --- Extreme total weight change (>10% body weight) in a very short window ---
  // Only flag this if the weekly rate is ALSO above safe limits.
  // If the weekly rate is safe (≤1 kg/week), the 10% total is fine over a longer period.
  if (primaryGoal === 'fat_loss') {
    const maxFirstPhase = currentWeight * 0.10; // 10% of body weight
    if (weightDelta > maxFirstPhase && timelineWeeks <= 8 && weeklyRate > safeMaxRate) {
      warnings.push(
        `Losing more than 10% of your body weight (${maxFirstPhase.toFixed(1)} kg) in ${timelineWeeks} weeks is not recommended. Consider a longer timeline or a smaller initial target.`
      );
      if (isRealistic) {
        isRealistic = false;
        adjustedTarget = Math.max(currentWeight - maxFirstPhase, minWeight);
      }
    }
  }

  return {
    isRealistic,
    warnings,
    adjustedTargetWeight: Math.round(adjustedTarget * 10) / 10,
    adjustedTimelineWeeks: Math.max(adjustedWeeks, primaryGoal === 'muscle_gain' ? 4 : 1),
    weeklyRateKg: Math.round(weeklyRate * 100) / 100,
    safeMaxWeeklyRate: safeMaxRate,
    safeMinWeeklyRate: safeMinRate,
    minHealthyWeight: minWeight,
  };
}
