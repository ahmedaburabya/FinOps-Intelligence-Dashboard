// frontend/src/types/finops.d.ts

import { datetime } from "@angular/flex-layout";

export interface AggregatedCostDataBase {
  service: string;
  project?: string | null;
  sku: string;
  time_period: string; // Using string for datetime for simplicity, will parse if needed
  cost: number;
  currency?: string;
  usage_amount?: number | null;
  usage_unit?: string | null;
}

export interface AggregatedCostDataCreate extends AggregatedCostDataBase {}

export interface AggregatedCostData extends AggregatedCostDataBase {
  id: number;
  created_at: string;
  updated_at: string;
}

export interface LLMInsightBase {
  insight_type: string;
  insight_text: string;
  related_finops_data_id?: number | null;
  sentiment?: string | null;
}

export interface LLMInsightCreate extends LLMInsightBase {}

export interface LLMInsight extends LLMInsightBase {
  id: number;
  timestamp: string; // Using string for datetime for simplicity
  created_at: string;
  updated_at: string;
}

export interface AggregatedCostDataWithInsights extends AggregatedCostData {
  llm_insights: LLMInsight[];
}

export interface FinopsOverview {
  mtd_spend: number;
  burn_rate_estimated_monthly: number;
}
