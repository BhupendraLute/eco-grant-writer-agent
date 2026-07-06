/**
 * TypeScript type definitions for the Eco Grant Writer frontend.
 * These mirror the FastAPI backend's Pydantic models.
 */

// ---------------------------------------------------------------------------
// Agent State
// ---------------------------------------------------------------------------

export interface AgentState {
  phase: Phase;
  organization_name: string;
  project_summary: string;
  location: string;
  budget_amount: number;
  currency: string;
  currency_symbol: string;
  ngo_registration_id: string;
  project_duration: string;
  volunteers_count: number;
  intake_complete: boolean;
  target_grant: string;
  grant_confirmed: boolean;
  mandatory_sections: string[];
  sections_drafted: Record<string, string>;
  current_section: string;
  drafted_proposal: string;
  is_compliant: boolean;
  security_approved: boolean;
}

export type Phase = "welcome" | "intake" | "matching" | "drafting" | "review" | "complete";

// ---------------------------------------------------------------------------
// API Types
// ---------------------------------------------------------------------------

export interface SessionResponse {
  session_id: string;
}

export interface ChatRequest {
  session_id: string;
  message: string;
  interrupt_id?: string | null;
}

export interface ChatResponse {
  message: string;
  options: string[];
  option_to_val: Record<string, string>;
  state: AgentState;
  interrupt_id: string | null;
}

export interface Grant {
  id: string;
  name: string;
  funder: string;
  max_funding: string;
  focus_areas: string[];
}

export interface GrantsResponse {
  grants: Grant[];
}

// ---------------------------------------------------------------------------
// UI Types
// ---------------------------------------------------------------------------

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  options: string[];
  option_to_val: Record<string, string>;
  timestamp: number;
}

export interface PhaseInfo {
  key: Phase;
  label: string;
  icon: string;
}

export const PHASES: PhaseInfo[] = [
  { key: "intake", label: "Intake Interview", icon: "clipboard" },
  { key: "matching", label: "Grant Matching", icon: "search" },
  { key: "drafting", label: "Section Drafting", icon: "pen-tool" },
  { key: "review", label: "Compliance Review", icon: "shield-check" },
  { key: "complete", label: "Proposal Complete", icon: "check-circle" },
];

export interface Template {
  icon: string;
  title: string;
  desc: string;
  prompt: string;
}

export const TEMPLATES: Template[] = [
  {
    icon: "mountain-snow",
    title: "River Cleanup",
    desc: "Ganga ghats restoration in Varanasi",
    prompt:
      "We are CleanWaters NGO based in Varanasi. We want to clean up and restore the Ganga River ghats by removing plastic waste and debris. Our budget is around 15,00,000 INR. We have about 200 local volunteers ready to participate. Our NGO Darpan registration ID is Darpan-12345.",
  },
  {
    icon: "trees",
    title: "Urban Forest",
    desc: "Nagar Van development in Delhi",
    prompt:
      "GreenCity Foundation wants to develop an urban forest (Nagar Van) in a municipal park in South Delhi. We plan to plant 5,000 indigenous saplings over 2 years. Our budget estimate is 40,00,000 INR. We have partnerships with 3 local schools for the maintenance program.",
  },
  {
    icon: "book-open",
    title: "Climate Education",
    desc: "Youth workshops in Jaipur schools",
    prompt:
      "EcoYouth India wants to run Yuva Jal Vayu climate awareness workshops in 20 government high schools across Jaipur, Rajasthan. The program duration is 6 months with a budget of 8,00,000 INR. We will develop curriculum materials and train 50 student ambassadors.",
  },
];

// ---------------------------------------------------------------------------
// Default State
// ---------------------------------------------------------------------------

export const DEFAULT_STATE: AgentState = {
  phase: "intake",
  organization_name: "",
  project_summary: "",
  location: "",
  budget_amount: 0,
  currency: "INR",
  currency_symbol: "₹",
  ngo_registration_id: "",
  project_duration: "",
  volunteers_count: 0,
  intake_complete: false,
  target_grant: "",
  grant_confirmed: false,
  mandatory_sections: [],
  sections_drafted: {},
  current_section: "",
  drafted_proposal: "",
  is_compliant: false,
  security_approved: false,
};
