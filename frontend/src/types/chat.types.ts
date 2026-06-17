export interface Message {
  id: string;
  sender_type: string;
  message_text: string;
}

export interface ChatRequest {
  conversation_id: string;
  message: string;
}

export interface ChatResponse {
  response: string;
}