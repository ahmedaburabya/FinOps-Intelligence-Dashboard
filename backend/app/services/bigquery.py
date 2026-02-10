"""
BigQuery integration service for fetching and processing Google Cloud billing data.
This module handles authentication with Google Cloud using a service account,
connects to BigQuery, and provides functions to query the billing export dataset
and transform the data into a usable format.
"""

import os
from google.cloud import bigquery
from google.oauth2 import service_account
import logging
from datetime import datetime, date
from typing import List, Dict, Any, Optional

from app import schemas

logger = logging.getLogger(__name__)

# --- Configuration for BigQuery ---
# The path to the Google Cloud service account key file, loaded from .env
# This file is essential for authenticating with Google Cloud services like BigQuery.
GOOGLE_APPLICATION_CREDENTIALS_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

# Placeholder for your BigQuery billing export table ID.
# This should be in the format: `project_id.dataset_id.gcp_billing_export_v1_<billing_account_id>`
# You MUST replace this with your actual BigQuery billing export table ID.
BIGQUERY_BILLING_TABLE_ID = os.getenv("BIGQUERY_BILLING_TABLE_ID") 

if not GOOGLE_APPLICATION_CREDENTIALS_PATH:
    raise ValueError("GOOGLE_APPLICATION_CREDENTIALS environment variable is not set. "
                     "Please provide the path to your service account key file.")
if not os.path.exists(GOOGLE_APPLICATION_CREDENTIALS_PATH):
    raise FileNotFoundError(f"Service account key file not found at: {GOOGLE_APPLICATION_CREDENTIALS_PATH}")
if not BIGQUERY_BILLING_TABLE_ID:
    logger.warning("BIGQUERY_BILLING_TABLE_ID environment variable is not set. "
                   "BigQuery queries will not be functional until configured.")


class BigQueryService:
    """
    A service class to interact with Google Cloud BigQuery.
    Manages client initialization, query execution, and data transformation.
    """
    _instance = None # Singleton instance

    def __new__(cls):
        """
        Implements a singleton pattern to ensure only one BigQuery client instance is created.
        """
        if cls._instance is None:
            cls._instance = super(BigQueryService, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """
        Initializes the BigQuery client using service account credentials.
        """
        try:
            # Load credentials from the service account key file
            credentials = service_account.Credentials.from_service_account_file(
                GOOGLE_APPLICATION_CREDENTIALS_PATH,
                scopes=["https://www.googleapis.com/auth/cloud-platform"]
            )
            # Initialize the BigQuery client
            self.client = bigquery.Client(credentials=credentials, project=credentials.project_id)
            logger.info(f"BigQuery client initialized successfully for project: {credentials.project_id}")
        except Exception as e:
            logger.error(f"Failed to initialize BigQuery client: {e}")
            raise

    def execute_query(self, query_string: str) -> List[Dict[str, Any]]:
        """
        Executes a SQL query against BigQuery and returns the results as a list of dictionaries.
        
        Args:
            query_string: The SQL query to execute.
            
        Returns:
            A list of dictionaries, where each dictionary represents a row of the query result.
        """
        try:
            query_job = self.client.query(query_string)
            results = query_job.result() # Waits for job to complete
            
            # Convert RowIterator to a list of dictionaries
            rows = []
            for row in results:
                rows.append(dict(row.items()))
            logger.info(f"Executed BigQuery query and fetched {len(rows)} rows.")
            return rows
        except Exception as e:
            logger.error(f"Failed to execute BigQuery query: {e}")
            raise

    def get_billing_data_for_aggregation(
        self, 
        start_date: Optional[date] = None, 
        end_date: Optional[date] = None
    ) -> List[schemas.AggregatedCostDataCreate]:
        """
        Fetches raw billing data from BigQuery and aggregates it for FinOps analysis.
        
        This function performs multi-dimensional cost aggregation by `service`, `project`, `sku`,
        and `usage_start_time` (truncated to daily for `time_period`).
        
        Args:
            start_date: Optional start date for filtering billing data.
            end_date: Optional end date for filtering billing data.
            
        Returns:
            A list of Pydantic `AggregatedCostDataCreate` objects.
        """
        if not BIGQUERY_BILLING_TABLE_ID:
            logger.error("BIGQUERY_BILLING_TABLE_ID is not configured. Cannot fetch billing data.")
            return []

        # Define the base query for aggregation
        query = f"""
        SELECT
            service.description AS service,
            project.id AS project,
            sku.description AS sku,
            DATE(usage_start_time) AS time_period,
            SUM(cost) AS cost,
            currency AS currency,
            SUM(usage.amount) AS usage_amount,
            usage.unit AS usage_unit
        FROM
            `{BIGQUERY_BILLING_TABLE_ID}`
        WHERE
            _PARTITIONDATE >= '{start_date.strftime('%Y-%m-%d') if start_date else '1970-01-01'}'
            AND _PARTITIONDATE <= '{end_date.strftime('%Y-%m-%d') if end_date else datetime.now().strftime('%Y-%m-%d')}'
            AND cost_type = 'USAGE' -- Filter out taxes, adjustments, etc.
        GROUP BY
            service, project, sku, time_period, currency, usage.unit
        ORDER BY
            time_period, project, service, sku
        """
        
        logger.info(f"Executing BigQuery billing aggregation query for {start_date} to {end_date}")
        results = self.execute_query(query)
        
        aggregated_data = []
        for row in results:
            try:
                aggregated_data.append(schemas.AggregatedCostDataCreate(
                    service=row['service'],
                    project=row['project'],
                    sku=row['sku'],
                    time_period=datetime.combine(row['time_period'], datetime.min.time()), # Convert date to datetime
                    cost=float(row['cost']),
                    currency=row['currency'],
                    usage_amount=float(row['usage_amount']) if row['usage_amount'] is not None else None,
                    usage_unit=row['usage_unit']
                ))
            except Exception as e:
                logger.error(f"Error transforming BigQuery row to schema: {row} - {e}")
                continue
                
        return aggregated_data

# Instantiate the BigQueryService as a singleton
bigquery_service = BigQueryService()
