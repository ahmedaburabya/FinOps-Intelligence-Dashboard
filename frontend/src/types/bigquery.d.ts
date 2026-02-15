// frontend/src/types/bigquery.d.ts

export type BigQueryDatasetId = string;
export type BigQueryTableId = string;
export type BigQueryTableDataRow = { [key: string]: any };

export interface BigQueryIngestResponse {
  message: string;
}
