"""
API endpoints for FinOps data and LLM insights.
This module defines the routes and their corresponding logic for
interacting with aggregated cost data, AI-generated insights, and BigQuery.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Any, Dict
from datetime import datetime, date
import asyncio  # Import asyncio for running blocking calls in a thread pool
import logging  # Import logging
from starlette.concurrency import run_in_threadpool

logger = logging.getLogger(__name__)  # Initialize logger

from app import crud, schemas
from app.database import get_db
from app.services.llm import llm_service
from app.services.bigquery import (
    bigquery_service,
)  # Import the bigquery_service instance

# APIRouter creates path operations for FinOps module
router = APIRouter()


# --- Aggregated Cost Data Endpoints (from PostgreSQL) ---
@router.post(
    "/aggregated-cost",
    response_model=schemas.AggregatedCostData,
    status_code=201,
    summary="Create new aggregated cost data record (into PostgreSQL)",
    response_description="The newly created aggregated cost data record.",
)
def create_aggregated_cost_data(
    cost_data: schemas.AggregatedCostDataCreate, db: Session = Depends(get_db)
):
    """
    Creates a new record of aggregated cloud cost data in the PostgreSQL database.

    This endpoint allows the submission of processed and aggregated cost metrics
    from various dimensions (Service, Project, SKU, Time-period) into the system.

    - **service**: The Google Cloud service (e.g., 'Compute Engine').
    - **project**: The Google Cloud project ID.
    - **sku**: The Stock Keeping Unit.
    - **time_period**: The timestamp for the aggregated period.
    - **cost**: The aggregated cost for the period.
    - **currency**: The currency of the cost (default: "USD").
    - **usage_amount**: Optional amount of usage for the SKU.
    - **usage_unit**: Optional unit of usage (e.g., 'hour', 'GB').
    """
    db_cost_data = crud.create_aggregated_cost_data(db=db, cost_data=cost_data)
    return db_cost_data


@router.get(
    "/aggregated-cost/{cost_data_id}",
    response_model=schemas.AggregatedCostData,
    summary="Retrieve aggregated cost data by ID (from PostgreSQL)",
    response_description="The aggregated cost data record matching the provided ID.",
)
def read_aggregated_cost_data(cost_data_id: int, db: Session = Depends(get_db)):
    """
    Retrieves a single aggregated cloud cost data record by its unique identifier from PostgreSQL.

    - **cost_data_id**: The unique ID of the aggregated cost data record.
    """
    db_cost_data = crud.get_aggregated_cost_data_by_id(db=db, cost_data_id=cost_data_id)
    if db_cost_data is None:
        raise HTTPException(status_code=404, detail="Aggregated cost data not found")
    return db_cost_data


@router.get(
    "/aggregated-cost",
    response_model=schemas.PaginatedAggregatedCostData,  # Updated response model
    summary="Retrieve paginated aggregated cost data records with filters (from PostgreSQL)",
    response_description="A paginated list of aggregated cost data records matching the filters, including total count.",
)
def read_aggregated_cost_data_list(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(
        100, ge=1, le=1000, description="Maximum number of records to return"
    ),
    service: Optional[str] = Query(None, description="Filter by Google Cloud service"),
    project: Optional[str] = Query(
        None, description="Filter by Google Cloud project ID"
    ),
    sku: Optional[str] = Query(None, description="Filter by Stock Keeping Unit (SKU)"),
    start_date: Optional[datetime] = Query(
        None, description="Filter records from this date (inclusive)"
    ),
    end_date: Optional[datetime] = Query(
        None, description="Filter records up to this date (inclusive)"
    ),
    db: Session = Depends(get_db),
):
    """
    Retrieves a paginated list of aggregated cloud cost data records from PostgreSQL.
    Supports pagination and filtering by service, project, SKU, and time range.
    """
    cost_data_list, total_count = (
        crud.get_aggregated_cost_data(  # Unpack data and count
            db=db,
            skip=skip,
            limit=limit,
            service=service,
            project=project,
            sku=sku,
            start_date=start_date,
            end_date=end_date,
        )
    )
    return {
        "items": cost_data_list,
        "total_count": total_count,
    }  # Return in new schema format


# --- FinOps Overview Endpoints (from PostgreSQL) ---
@router.get(
    "/overview",
    summary="Get high-level FinOps overview (MTD Spend, Burn Rate from PostgreSQL)",
    response_description="Key financial metrics including Month-to-Date spend and projected burn rate.",
)
def get_finops_overview(
    project: Optional[str] = Query(
        None, description="Optional: Filter overview by Google Cloud project ID"
    ),
    db: Session = Depends(get_db),
):
    """
    Provides a high-level overview of financial metrics from PostgreSQL, including:
    - **Month-to-Date (MTD) Spend**: Total cost incurred in the current calendar month.
    - **Burn Rate**: An estimated monthly spend based on recent daily average consumption (e.g., last 30 days).
    - **Daily Burn Rate (MTD)**: Average daily spend in the current month.
    - **Projected Month-End Spend**: Estimated total spend for the current month.

    Results can be filtered by a specific Google Cloud project.
    """
    mtd_spend = crud.get_mtd_spend(db=db, project=project)
    burn_rate = crud.get_burn_rate(db=db, project=project)  # Defaults to 30 days
    daily_burn_rate_mtd = crud.get_daily_burn_rate_mtd(db=db, project=project)
    projected_month_end_spend = crud.get_projected_month_end_spend(
        db=db, project=project
    )  # New calculation

    return {
        "mtd_spend": mtd_spend,
        "burn_rate_estimated_monthly": burn_rate,
        "daily_burn_rate_mtd": daily_burn_rate_mtd,
        "projected_month_end_spend": projected_month_end_spend,  # Include new metric
    }


# --- LLM Integration Endpoints ---
@router.post(
    "/generate-spend-summary",
    response_model=schemas.LLMInsight,
    status_code=201,
    summary="Generate an AI-driven spend summary using LLM",
    response_description="The newly created LLM insight record containing the spend summary.",
)
async def generate_ai_spend_summary(
    service: Optional[str] = Query(None, description="Filter by Google Cloud service"),
    project: Optional[str] = Query(
        None, description="Filter by Google Cloud project ID"
    ),
    sku: Optional[str] = Query(None, description="Filter by Stock Keeping Unit (SKU)"),
    start_date: Optional[datetime] = Query(
        None, description="Filter records from this date (inclusive)"
    ),
    end_date: Optional[datetime] = Query(
        None, description="Filter records up to this date (inclusive)"
    ),
    db: Session = Depends(get_db),
):
    """
    Triggers the LLM to generate a natural language summary of cloud spend for a given period and/or project.
    The generated summary is stored as an LLMInsight and returned.
    Data is fetched from PostgreSQL based on the provided query parameters.
    """
    # 1. Retrieve ALL relevant aggregated cost data from PostgreSQL based on filters (no skip/limit)
    aggregated_data = crud.get_aggregated_cost_data(
        db=db,
        skip=0,  # Ensure no skip
        limit=None,  # Ensure all data is fetched (no limit)
        service=service,
        project=project,
        sku=sku,
        start_date=start_date,
        end_date=end_date,
    )

    if not aggregated_data:
        raise HTTPException(
            status_code=404,
            detail="No aggregated cost data found for the specified criteria to generate a summary.",
        )

    # 2. Call the LLM service to generate the summary
    summary_text = await llm_service.generate_spend_summary(
        aggregated_data,
        project=project,  # Pass project filter to LLM service for context
        start_date=start_date,  # Pass start_date filter to LLM service for context
        end_date=end_date,  # Pass end_date filter to LLM service for context
    )

    # 3. Store the generated insight in the database
    insight_create = schemas.LLMInsightCreate(
        insight_type="spend_summary",
        insight_text=summary_text,
        related_finops_data_id=None,
    )
    db_insight = crud.create_llm_insight(db=db, insight=insight_create)

    return db_insight


@router.post(
    "/llm-insight",
    response_model=schemas.LLMInsight,
    status_code=201,
    summary="Create a new LLM-generated insight",
    response_description="The newly created LLM insight record.",
)
def create_llm_insight(
    insight: schemas.LLMInsightCreate, db: Session = Depends(get_db)
):
    """
    Creates a new record for an AI-generated insight.

    This endpoint is used to store insights derived from LLMs, such as
    spend summaries, anomaly detections, or cost optimization recommendations.

    - **insight_type**: Category of the insight (e.g., 'spend_summary', 'anomaly_detection').
    - **insight_text**: The full text of the insight.
    - **related_finops_data_id**: Optional ID linking to specific aggregated cost data.
    - **sentiment**: Optional sentiment associated with the insight.
    """
    db_insight = crud.create_llm_insight(db=db, insight=insight)
    return db_insight


@router.post(
    "/insights/chat",
    response_model=str,  # LLM typically returns a string
    summary="Get AI-driven insights based on natural language query or insight type",
    description="Provides AI-generated analysis, summaries, anomaly detection, "
    "predictions, or recommendations based on aggregated cost data and user input.",
)
async def get_ai_chat_insight(
    request: schemas.AIInsightRequest,
    db: Session = Depends(get_db),
):
    """
    Handles requests for various AI-driven FinOps insights.
    - **query**: User's natural language question or specific request.
    - **insight_type**: Specifies the desired type of insight (e.g., 'natural_query', 'summary', 'anomaly', 'prediction', 'recommendation').
    - **project, service, sku, start_date, end_date**: Optional filters to refine the data context for the AI.
    """
    # 1. Fetch relevant aggregated cost data based on filters
    aggregated_data = crud.get_aggregated_cost_data(
        db=db,
        skip=0,
        limit=None,  # Fetch all relevant data for AI analysis
        service=request.service,
        project=request.project,
        sku=request.sku,
        start_date=request.start_date,
        end_date=request.end_date,
    )

    if not aggregated_data and request.insight_type != "natural_query":
        # For natural queries, the LLM might be able to answer generally even without specific data.
        # For other insight types, data is crucial.
        raise HTTPException(
            status_code=404,
            detail="No aggregated cost data found for the specified criteria to generate insight.",
        )

    # 2. Call the LLM service to get the insight
    try:
        llm_response = await llm_service.get_ai_insight(
            insight_type=request.insight_type,
            query=request.query or "",  # Ensure query is not None
            aggregated_data=aggregated_data,
            project=request.project,
            start_date=request.start_date,
            end_date=request.end_date,
        )
        return llm_response
    except Exception as e:
        logger.error(f"Failed to get AI insight: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to generate AI insight: {e}"
        )


# --- BigQuery Exploration & Ingestion Endpoints ---
@router.get(
    "/services/distinct-db",
    response_model=List[str],
    summary="Get list of distinct services from PostgreSQL",
    description="Retrieves a list of distinct service descriptions available in the PostgreSQL aggregated cost data.",
)
def get_distinct_services_from_postgresql(db: Session = Depends(get_db)):
    """
    Retrieves a list of unique service names from the PostgreSQL aggregated cost data table.
    This is useful for populating dropdowns or filters in the frontend.
    """
    try:
        distinct_services = crud.get_distinct_services_from_db(db)
        return distinct_services
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve distinct services from PostgreSQL: {e}",
        )


@router.get(
    "/services/distinct-projects",
    response_model=List[str],
    summary="Get list of distinct project IDs from PostgreSQL",
    description="Retrieves a list of distinct project IDs available in the PostgreSQL aggregated cost data.",
)
def get_distinct_projects_from_postgresql(db: Session = Depends(get_db)):
    """
    Retrieves a list of unique project IDs from the PostgreSQL aggregated cost data table.
    This is useful for populating dropdowns or filters in the frontend.
    """
    try:
        distinct_projects = crud.get_distinct_projects_from_db(db)
        return distinct_projects
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve distinct project IDs from PostgreSQL: {e}",
        )


@router.get(
    "/services/distinct-skus",
    response_model=List[str],
    summary="Get list of distinct SKUs from PostgreSQL",
    description="Retrieves a list of distinct SKUs available in the PostgreSQL aggregated cost data.",
)
def get_distinct_skus_from_postgresql(db: Session = Depends(get_db)):
    """
    Retrieves a list of unique SKUs from the PostgreSQL aggregated cost data table.
    This is useful for populating dropdowns or filters in the frontend.
    """
    try:
        distinct_skus = crud.get_distinct_skus_from_db(db)
        return distinct_skus
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve distinct SKUs from PostgreSQL: {e}",
        )


@router.get(
    "/bigquery/datasets",
    summary="List all accessible BigQuery datasets",
    response_model=schemas.PaginatedBigQueryDatasets,  # Updated response model
)
async def list_gcp_bigquery_datasets(
    page_size: int = Query(
        100, ge=1, le=1000, description="Number of datasets per page"
    ),
    page_token: Optional[str] = Query(
        None, description="Token for the next page of results"
    ),
):
    """
    Retrieves a paginated list of BigQuery datasets that the configured service account
    has access to in the GCP project.
    """
    try:
        # Pass page_size and page_token to the service method
        paginated_response = await run_in_threadpool(
            bigquery_service.list_bigquery_datasets, page_size, page_token
        )
        return paginated_response
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to list BigQuery datasets: {e}"
        )


@router.get(
    "/bigquery/datasets/{dataset_id}/tables",
    summary="List all tables in a BigQuery dataset",
    response_model=List[str],
)
async def list_gcp_bigquery_tables(dataset_id: str):  # Changed to async
    """
    Retrieves a list of all tables within a specified BigQuery dataset that the
    configured service account has access to.
    - **dataset_id**: The ID of the BigQuery dataset.
    """
    try:
        tables = await run_in_threadpool(
            bigquery_service.list_bigquery_tables, dataset_id
        )
        return tables
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list BigQuery tables in dataset '{dataset_id}': {e}",
        )


@router.get(
    "/bigquery/datasets/{dataset_id}/tables/{table_id}/data",
    summary="Read data directly from a BigQuery table",
    response_model=List[Dict[str, Any]],
)
async def read_bigquery_table_data(
    dataset_id: str,
    table_id: str,
    limit: Optional[int] = Query(
        None, ge=1, description="Optional: Limit the number of rows to return."
    ),
):
    """
    Reads a limited number of rows directly from a specified BigQuery table.
    - **dataset_id**: The ID of the BigQuery dataset.
    - **table_id**: The ID of the BigQuery table.
    - **limit**: Maximum number of rows to return.
    """
    try:
        data = await run_in_threadpool(
            bigquery_service.read_bigquery_table_data, dataset_id, table_id, limit
        )
        return data
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read data from BigQuery table '{dataset_id}.{table_id}': {e}",
        )


@router.post(
    "/bigquery/ingest-billing-data",
    status_code=201,
    summary="Ingest BigQuery billing data into PostgreSQL",
    response_description="Number of records ingested into PostgreSQL.",
)
async def ingest_bigquery_billing_data(  # Changed to async
    dataset_id: str = Query(..., description="BigQuery dataset ID, e.g., 'finopsDS'"),
    table_id: str = Query(
        ..., description="BigQuery table ID, e.g., 'gcp_billing_export_resource_v1_...'"
    ),
    start_date: Optional[date] = Query(
        None, description="Optional: Start date for billing data ingestion (YYYY-MM-DD)"
    ),
    end_date: Optional[date] = Query(
        None, description="Optional: End date for billing data ingestion (YYYY-MM-DD)"
    ),
    db: Session = Depends(get_db),
):
    """
    Fetches billing data from the specified BigQuery table and ingests it into
    the PostgreSQL `aggregated_cost_data` table.
    """
    try:
        billing_data = await run_in_threadpool(
            bigquery_service.get_billing_data_for_aggregation,
            dataset_id,
            table_id,
            start_date,
            end_date,
        )

        ingested_count = 0
        if billing_data:
            # CRUD operations are blocking, so also run in threadpool
            await run_in_threadpool(
                crud.bulk_create_aggregated_cost_data, db, billing_data
            )
            ingested_count = len(billing_data)

        return {
            "message": f"Successfully ingested {ingested_count} records from BigQuery into PostgreSQL."
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to ingest BigQuery data: {e}"
        )
