"""
BigQuery integration service for fetching and processing Google Cloud billing data.
This module handles authentication with Google Cloud using a service account,
conne2cts to BigQuery, and provides functions to query the billing export dataset
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


class BigQueryService:
    """
    A service class to interact with Google Cloud BigQuery.
    Manages client initialization, query execution, and data transformation.
    """

    _instance = None  # Singleton instance

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
            # Load credentials from environment variables
            service_account_info = {
                "type": os.getenv("GOOGLE_TYPE"),
                "project_id": os.getenv("GOOGLE_PROJECT_ID"),
                "private_key_id": os.getenv("GOOGLE_PRIVATE_KEY_ID"),
                "private_key": os.getenv("GOOGLE_PRIVATE_KEY"),
                "client_email": os.getenv("GOOGLE_CLIENT_EMAIL"),
                "client_id": os.getenv("GOOGLE_CLIENT_ID"),
                "auth_uri": os.getenv("GOOGLE_AUTH_URI"),
                "token_uri": os.getenv("GOOGLE_TOKEN_URI"),
                "auth_provider_x509_cert_url": os.getenv("GOOGLE_AUTH_PROVIDER_X509_CERT_URL"),
                "client_x509_cert_url": os.getenv("GOOGLE_CLIENT_X509_CERT_URL"),
                "universe_domain": os.getenv("GOOGLE_UNIVERSE_DOMAIN"),
            }

            if service_account_info["private_key"]:
                service_account_info["private_key"] = service_account_info["private_key"].replace("\\n", "\n")

            credentials = service_account.Credentials.from_service_account_info(
                service_account_info,
                scopes=["https://www.googleapis.com/auth/cloud-platform"],
            )
            # Initialize the BigQuery client
            self.client = bigquery.Client(
                credentials=credentials, project=credentials.project_id
            )
            logger.info(
                f"BigQuery client initialized successfully for project: {credentials.project_id}"
            )
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
            results = query_job.result()  # Waits for job to complete

            # Convert RowIterator to a list of dictionaries
            rows = []
            for row in results:
                rows.append(dict(row.items()))
            logger.info(f"Executed BigQuery query and fetched {len(rows)} rows.")
            return rows
        except Exception as e:
            logger.error(f"Failed to execute BigQuery query: {e}")
            raise

    def _table_has_column(
        self, project_id: str, dataset_id: str, table_id: str, column_name: str
    ) -> bool:
        """
        Checks if a BigQuery table has a specific column using INFORMATION_SCHEMA.
        """
        query = f"""
        SELECT EXISTS(
            SELECT 1
            FROM `{project_id}`.{dataset_id}.INFORMATION_SCHEMA.COLUMNS
            WHERE table_name = '{table_id}' AND column_name = '{column_name}'
        );
        """
        try:
            results = self.execute_query(query)
            # The result is typically a list with one dictionary, with a boolean value
            return results[0]["f0_"] if results else False
        except Exception as e:
            logger.error(
                f"Error checking for column '{column_name}' in table '{table_id}': {e}"
            )
            return False

    def list_bigquery_datasets(self) -> List[str]:
        """
        Lists all datasets in the project accessible by the service account.
        """
        try:
            datasets = list(self.client.list_datasets())
            logger.info(f"Found {len(datasets)} datasets.")
            return [ds.dataset_id for ds in datasets]
        except Exception as e:
            logger.error(f"Error listing BigQuery datasets: {e}")
            raise

    def list_bigquery_tables(self, dataset_id: str) -> List[str]:
        """
        Lists all tables within a specified BigQuery dataset.
        """
        try:
            dataset_ref = self.client.dataset(dataset_id)
            tables = list(self.client.list_tables(dataset_ref))
            logger.info(f"Found {len(tables)} tables in dataset '{dataset_id}'.")
            return [table.table_id for table in tables]
        except Exception as e:
            logger.error(
                f"Error listing BigQuery tables in dataset '{dataset_id}': {e}"
            )
            raise

    def read_bigquery_table_data(
        self, dataset_id: str, table_id: str, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Reads data directly from a specified BigQuery table.
        """
        bigquery_table_full_id = f"{self.client.project}.{dataset_id}.{table_id}"
        query = f"SELECT * FROM `{bigquery_table_full_id}`"
        if limit is not None:
            query += f" LIMIT {limit}"

        logger.info(
            f"Executing BigQuery query to read data from table {bigquery_table_full_id}"
        )
        return self.execute_query(query)

    def get_billing_data_for_aggregation(
        self,
        dataset_id: str,
        table_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[schemas.AggregatedCostDataCreate]:
        """
        Fetches raw billing data from BigQuery and aggregates it for FinOps analysis.

        This function performs multi-dimensional cost aggregation by `service`, `project`, `sku`,
        and `usage_start_time` (truncated to daily for `time_period`).

        Args:
            dataset_id: The ID of the BigQuery dataset containing the billing data.
            table_id: The ID of the BigQuery table containing the billing data.
            start_date: Optional start date for filtering billing data.
            end_date: Optional end date for filtering billing data.

        Returns:
            A list of Pydantic `AggregatedCostDataCreate` objects.
        """
        # Construct the full table ID dynamically
        bigquery_billing_table_full_id = (
            f"{self.client.project}.{dataset_id}.{table_id}"
        )

        # Determine the date column for filtering based on table partitioning
        use_partition_date = self._table_has_column(
            project_id=self.client.project,
            dataset_id=dataset_id,
            table_id=table_id,
            column_name="_PARTITIONDATE",
        )

        date_filter_column = (
            "_PARTITIONDATE" if use_partition_date else "usage_start_time"
        )
        logger.info(f"Using {date_filter_column} for date filtering in BigQuery query.")

        # Build the WHERE clause dynamically
        # where_clauses = ["cost_type = 'USAGE'"] # Always filter by cost_type - REMOVED FOR DEBUGGING
        where_clauses = []

        if start_date:
            where_clauses.append(
                f"{date_filter_column} >= '{start_date.strftime('%Y-%m-%d')}'"
            )
        else:
            # If no start_date, default to a very old date for filtering partitioned tables,
            # or just don't add a start filter for usage_start_time
            if use_partition_date:
                where_clauses.append(f"{date_filter_column} >= '1970-01-01'")

        if end_date:
            where_clauses.append(
                f"{date_filter_column} <= '{end_date.strftime('%Y-%m-%d')}'"
            )
        else:
            # If no end_date, default to today for filtering partitioned tables,
            # or just don't add an end filter for usage_start_time
            if use_partition_date:
                where_clauses.append(
                    f"{date_filter_column} <= '{datetime.now().strftime('%Y-%m-%d')}'"
                )

        where_clause_str = " AND ".join(where_clauses)
        if where_clause_str:
            where_clause_str = f"WHERE {where_clause_str}"

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
            `{bigquery_billing_table_full_id}`
        {where_clause_str}
        GROUP BY
            service, project, sku, time_period, currency, usage.unit
        ORDER BY
            time_period, project, service, sku
        """

        logger.debug(f"BigQuery aggregation query:\n{query}")  # Log the generated query
        logger.info(
            f"Executing BigQuery billing aggregation query for {start_date} to {end_date} from table {bigquery_billing_table_full_id}"
        )
        results = self.execute_query(query)

        aggregated_data = []
        for row in results:
            try:
                aggregated_data.append(
                    schemas.AggregatedCostDataCreate(
                        service=row["service"],
                        project=row["project"],
                        sku=row["sku"],
                        time_period=datetime.combine(
                            row["time_period"], datetime.min.time()
                        ),  # Convert date to datetime
                        cost=float(row["cost"]),
                        currency=row["currency"],
                        usage_amount=(
                            float(row["usage_amount"])
                            if row["usage_amount"] is not None
                            else None
                        ),
                        usage_unit=row["usage_unit"],
                    )
                )
            except Exception as e:
                logger.error(f"Error transforming BigQuery row to schema: {row} - {e}")
                raise  # Raise the exception to make transformation errors explicit

        return aggregated_data


# Instantiate the BigQueryService as a singleton
bigquery_service = BigQueryService()
