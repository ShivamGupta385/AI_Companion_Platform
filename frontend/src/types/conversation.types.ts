export interface ConversationCreate {
  companion_id: string;
  conversation_type: string;
}

export interface Conversation {
  id: string;
  user_id: string;
  companion_id: string;
  conversation_type: string;
}