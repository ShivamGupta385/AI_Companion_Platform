export interface OnboardingRequest {
  baseline_data: {
    age: number;
    occupation: string;
    country: string;
    goals: string;
    interests: string;
  };
}

export interface OnboardingResponse {
  id: string;
  user_id: string;
  baseline_data: {
    age: number;
    occupation: string;
    country: string;
    goals: string;
    interests: string;
  };
  created_at: string;
}