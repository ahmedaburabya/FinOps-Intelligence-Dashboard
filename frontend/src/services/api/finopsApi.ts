// frontend/src/services/api/finopsApi.ts
import axiosInstance from './axiosInstance';
import type { BigQueryIngestResponse, PaginatedBigQueryDatasets } from '~/types/bigquery';

const FINOPS_BASE_PATH = '/finops'; // From backend main.py: prefix="/api/v1/finops"

export const finopsApi = {
  // Aggregated Cost Data Endpoints
  createAggregatedCostData: async (data: AggregatedCostDataCreate): Promise<AggregatedCostData> => {
    const response = await axiosInstance.post<AggregatedCostData>(
      `${FINOPS_BASE_PATH}/aggregated-cost`,
      data,
    );
    return response.data;
  },

  getAggregatedCostDataById: async (costDataId: number): Promise<AggregatedCostData> => {
    const response = await axiosInstance.get<AggregatedCostData>(
      `${FINOPS_BASE_PATH}/aggregated-cost/${costDataId}`,
    );
    return response.data;
  },

  getAggregatedCostDataList: async (params?: {
    skip?: number;
    limit?: number;
    service?: string;
    project?: string;
    sku?: string;
    start_date?: string; // datetime-local format 'YYYY-MM-DDTHH:mm:ss' or 'YYYY-MM-DD'
    end_date?: string; // datetime-local format 'YYYY-MM-DDTHH:mm:ss' or 'YYYY-MM-DD'
  }): Promise<PaginatedAggregatedCostData> => { // Updated return type
    const response = await axiosInstance.get<PaginatedAggregatedCostData>( // Updated generic type
      `${FINOPS_BASE_PATH}/aggregated-cost`,
      { params },
    );
    return response.data;
  },

  // FinOps Overview Endpoints
  getFinopsOverview: async (project?: string): Promise<FinopsOverview> => {
    const response = await axiosInstance.get<FinopsOverview>(`${FINOPS_BASE_PATH}/overview`, {
      params: { project },
    });
    return response.data;
  },

  // LLM Integration Endpoints
  generateSpendSummary: async (params?: {
    service?: string;
    project?: string;
    sku?: string;
    start_date?: string;
    end_date?: string;
  }): Promise<LLMInsight> => {
    const response = await axiosInstance.post<LLMInsight>(
      `${FINOPS_BASE_PATH}/generate-spend-summary`,
      null, // Request body is null for GET-like parameters
      { params },
    );
    return response.data;
  },

  createLLMInsight: async (data: LLMInsightCreate): Promise<LLMInsight> => {
    const response = await axiosInstance.post<LLMInsight>(`${FINOPS_BASE_PATH}/llm-insight`, data);
    return response.data;
  },

  // BigQuery Exploration & Ingestion Endpoints
  listBigQueryDatasets: async (params?: {
    page_size?: number;
    page_token?: string | null;
  }): Promise<PaginatedBigQueryDatasets> => {
    const response = await axiosInstance.get<PaginatedBigQueryDatasets>(
      `${FINOPS_BASE_PATH}/bigquery/datasets`,
      { params },
    );
    return response.data;
  },

  listBigQueryTables: async (datasetId: string): Promise<string[]> => {
    const response = await axiosInstance.get<string[]>(
      `${FINOPS_BASE_PATH}/bigquery/datasets/${datasetId}/tables`,
    );
    return response.data;
  },

  readBigQueryTableData: async (
    datasetId: string,
    tableId: string,
    limit?: number,
  ): Promise<any[]> => {
    const response = await axiosInstance.get<any[]>(
      `${FINOPS_BASE_PATH}/bigquery/datasets/${datasetId}/tables/${tableId}/data`,
      { params: { limit } },
    );
    return response.data;
  },

  ingestBigQueryBillingData: async (params: {
    dataset_id: string;
    table_id: string;
    start_date?: string; // Date format 'YYYY-MM-DD'
    end_date?: string; // Date format 'YYYY-MM-DD'
  }): Promise<BigQueryIngestResponse> => {
    const response = await axiosInstance.post<BigQueryIngestResponse>(
      `${FINOPS_BASE_PATH}/bigquery/ingest-billing-data`,
      null,
      { params },
    );
    return response.data;
  },

  getDistinctServices: async (): Promise<string[]> => {
    const response = await axiosInstance.get<string[]>(`${FINOPS_BASE_PATH}/services/distinct-db`);
    return response.data;
  },

  getDistinctProjects: async (): Promise<string[]> => {
    const response = await axiosInstance.get<string[]>(
      `${FINOPS_BASE_PATH}/services/distinct-projects`,
    );
    return response.data;
  },

  getDistinctSkus: async (): Promise<string[]> => {
    const response = await axiosInstance.get<string[]>(
      `${FINOPS_BASE_PATH}/services/distinct-skus`,
    );
    return response.data;
  },

  getAIInsight: async (request: AIInsightRequest): Promise<string> => {
    const response = await axiosInstance.post<string>(`${FINOPS_BASE_PATH}/insights/chat`, request);
    return response.data;
  },
};
