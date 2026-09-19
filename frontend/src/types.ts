export type ScreenType = 'initial' | 'console';

export type TransitionDirection = 'push' | 'push_back';

export type CoolingAction = 'HYBRID' | 'LIQUID' | 'AIR';

export type CedarStatus = 'APPROVED' | 'BLOCKED';

export type RiskLevel = 'Low' | 'Medium' | 'High';

export interface TelemetryVectors {
  temperature_deviation: string;
  water_usage: string;
  liquid_outlet_temp: string;
  cooling_efficiency: string;
}

export interface CedarSafetyVerdict {
  risk_score: string;
  intervention_applied: string;
  reason: string;
}

export interface RewardBreakdown {
  thermal_stability: string;
  energy_penalty: string;
  water_conservation: string;
  equipment_strain: string;
}

export interface DecisionDispatch {
  step: number;
  timeUTC: string;
  action: CoolingAction;
  status: CedarStatus;
  riskLevel: RiskLevel;
  cedarReason: string;
  strategyReason: string;
  safetyFilterReason: string;
  telemetryVectors: TelemetryVectors;
  cedarSafetyVerdict: CedarSafetyVerdict;
  rewardBreakdown: RewardBreakdown;
  details?: {
    liquidRatio?: string;
    airRatio?: string;
    powerSaved?: string;
  };
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'agent';
  text: string;
  timestamp: string;
}

export interface ApiDecision {
  timestamp: string;
  step_id: number;
  state: {
    temperature_deviation: number;
    water_usage: number;
    liquid_outlet_temp: number;
    cooling_efficiency: number;
  };
  action: number | string;
  action_label: string;
  reward_breakdown: Record<string, unknown>;
  strategy_reason: string | null;
  safety_filter_verdict: {
    intervention_applied: boolean;
    reason: string;
    risk_level: string;
    risk_score: number;
  };
  cedar_verdict: { allowed: boolean; reason: string };
}
