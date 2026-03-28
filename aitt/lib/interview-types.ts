export type InterviewGroup =
  | "Leadership & Influence"
  | "Conflict & Collaboration"
  | "Problem Solving & Technical Judgment"
  | "Failure & Resilience"
  | "Achievement & Impact"
  | "Adaptability & Growth";

export type FollowUpIntent =
  | "clarify_situation"
  | "clarify_task"
  | "clarify_action"
  | "clarify_result"
  | "reduce_we_language"
  | "tighten_rambling"
  | "reframe_no_example"
  | "support_emotional"
  | "praise_strong";

export type StarScores = {
  situation: number;
  task: number;
  action: number;
  result: number;
};

export type FeedbackPayload = {
  overall: string;
  strengths: string[];
  improvements: string[];
  improved_answer: string;
};

export type StartSessionRequest = {
  mode?: "behavioral";
  group?: InterviewGroup;
  level?: "intern" | "new_grad";
  question_id?: string | null;
  question?: string | null;
  metadata?: Record<string, unknown>;
};

export type GenerateTurnRequest = {
  candidate_answer: string;
  session_id?: string | null;
  question_id?: string | null;
  question?: string | null;
  group?: InterviewGroup;
  level?: "intern" | "new_grad";
  force_engine?: "local_primary" | "nanogpt_backup" | "heuristic_dev" | null;
  temperature?: number;
  top_k?: number;
  max_new_tokens?: number;
};

export type GenerateTurnResponse = {
  engine: string;
  session_id: string | null;
  question_id: string | null;
  question: string;
  group: InterviewGroup | string;
  tags: string[];
  candidate_answer: string;
  interviewer_text: string;
  follow_up_question: string;
  follow_up_intent: FollowUpIntent;
  scores: StarScores;
  feedback: FeedbackPayload;
  confidence: number;
};

export type SessionTurn = {
  id: number;
  turn_index: number;
  question_id: string | null;
  question: string;
  candidate_answer: string;
  engine: string;
  prompt_version: string | null;
  raw_model_json?: unknown;
  repaired_json?: unknown;
  response: GenerateTurnResponse;
  created_at: string;
};

export type InterviewSession = {
  session_id: string;
  mode: string;
  question_id: string | null;
  question_family_id: string | null;
  group: InterviewGroup | string;
  level: "intern" | "new_grad";
  tags: string[];
  question: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  turns: SessionTurn[];
};
