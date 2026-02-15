// frontend/src/hooks/useFinopsData.ts
import { useState, useEffect, useCallback } from 'react';
import { finopsApi } from '../services';
import type { AggregatedCostData, FinopsOverview } from '../types/finops';
import type { ApiError } from '../types/common';

// Custom hook for fetching FinOps Overview data
export const useFinopsOverview = (project?: string) => {
  const [overview, setOverview] = useState<FinopsOverview | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<ApiError | null>(null);

  const fetchOverview = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await finopsApi.getFinopsOverview(project);
      setOverview(data);
    } catch (err: any) {
      setError({
        detail: err.response?.data?.detail || 'Failed to fetch FinOps overview.',
        status_code: err.response?.status,
      });
    } finally {
      setLoading(false);
    }
  }, [project]);

  useEffect(() => {
    fetchOverview();
  }, [fetchOverview]);

  return { overview, loading, error, refetchOverview: fetchOverview };
};

// Custom hook for fetching Aggregated Cost Data
export const useAggregatedCostData = (params?: {
  skip?: number;
  limit?: number;
  service?: string;
  project?: string;
  sku?: string;
  start_date?: string;
  end_date?: string;
}) => {
  const [costData, setCostData] = useState<AggregatedCostData[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<ApiError | null>(null);

  const fetchCostData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await finopsApi.getAggregatedCostDataList(params);
      setCostData(data);
    } catch (err: any) {
      setError({
        detail: err.response?.data?.detail || 'Failed to fetch aggregated cost data.',
        status_code: err.response?.status,
      });
    } finally {
      setLoading(false);
    }
  }, [params]);

  useEffect(() => {
    fetchCostData();
  }, [params?.skip, params?.limit]);

  return { costData, loading, error, refetchCostData: fetchCostData };
};
