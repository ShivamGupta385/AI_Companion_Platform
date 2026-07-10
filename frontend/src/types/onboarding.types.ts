export interface OnboardingRequest {
  baseline_data: {
    nickname: string;
    age: number;
    current_focus: string;
    preferred_tone: string;
    goals: string;
    interests: string;
    favorite_topics: string;
    current_challenge: string;
    country: string;
  };
}

export interface OnboardingResponse {
  id: string;
  user_id: string;
  baseline_data: {
    nickname: string;
    age: number;
    current_focus: string;
    preferred_tone: string;
    goals: string;
    interests: string;
    favorite_topics: string;
    current_challenge: string;
    country: string;
  };
  created_at: string;
}