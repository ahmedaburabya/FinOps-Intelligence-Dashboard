// frontend/src/types/common.d.ts

export interface ApiResponse<T> {
  data: T;
  message?: string;
  status?: number;
}

export interface ApiError {
  detail: string;
  code?: string;
  status_code?: number;
}

export interface PaginationParams {
  skip?: number;
  limit?: number;
}
