"""
API endpoints for FinOps data and LLM insights.
This module defines the routes and their corresponding logic for
interacting with aggregated cost data, AI-generated insights, and BigQuery.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Any, Dict
from datetime import datetime, date
import asyncio # Import asyncio for running blocking calls in a thread pool

from app import crud, schemas
from app.database import get_db
from app.services.llm import llm_service
from app.services.bigquery import bigquery_service # Import the bigquery_service instance

# APIRouter creates path operations for FinOps module
router = APIRouter()

# --- Aggregated Cost Data Endpoints (from PostgreSQL) ---
@router.post("/aggregated-cost", response_model=schemas.AggregatedCostData, status_code=201, 
             summary="Create new aggregated cost data record (into PostgreSQL)",
             response_description="The newly created aggregated cost data record.")
def create_aggregated_cost_data(
    cost_data: schemas.AggregatedCostDataCreate, 
    db: Session = Depends(get_db)
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

@router.get("/aggregated-cost/{cost_data_id}", response_model=schemas.AggregatedCostData,
            summary="Retrieve aggregated cost data by ID (from PostgreSQL)",
            response_description="The aggregated cost data record matching the provided ID.")
def read_aggregated_cost_data(cost_data_id: int, db: Session = Depends(get_db)):
    """
    Retrieves a single aggregated cloud cost data record by its unique identifier from PostgreSQL.
    
    - **cost_data_id**: The unique ID of the aggregated cost data record.
    """
    db_cost_data = crud.get_aggregated_cost_data_by_id(db=db, cost_data_id=cost_data_id)
    if db_cost_data is None:
        raise HTTPException(status_code=404, detail="Aggregated cost data not found")
    return db_cost_data

@router.get("/aggregated-cost", response_model=List[schemas.AggregatedCostData],
            summary="Retrieve multiple aggregated cost data records with filters (from PostgreSQL)",
            response_description="A list of aggregated cost data records matching the filters.")
def read_aggregated_cost_data_list(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    service: Optional[str] = Query(None, description="Filter by Google Cloud service"),
    project: Optional[str] = Query(None, description="Filter by Google Cloud project ID"),
    sku: Optional[str] = Query(None, description="Filter by Stock Keeping Unit (SKU)"),
    start_date: Optional[datetime] = Query(None, description="Filter records from this date (inclusive)"),
    end_date: Optional[datetime] = Query(None, description="Filter records up to this date (inclusive)"),
    db: Session = Depends(get_db)
):
    """
    Retrieves a list of aggregated cloud cost data records from PostgreSQL.
    Supports pagination and filtering by service, project, SKU, and time range.
    """
    cost_data_list = crud.get_aggregated_cost_data(
        db=db, 
        skip=skip, 
        limit=limit, 
        service=service, 
        project=project, 
        sku=sku,
        start_date=start_date,
        end_date=end_date
    )
    return cost_data_list

# --- FinOps Overview Endpoints (from PostgreSQL) ---
@router.get("/overview", 
             summary="Get high-level FinOps overview (MTD Spend, Burn Rate from PostgreSQL)",
             response_description="Key financial metrics including Month-to-Date spend and projected burn rate.")
def get_finops_overview(
    project: Optional[str] = Query(None, description="Optional: Filter overview by Google Cloud project ID"),
    db: Session = Depends(get_db)
):
    """
    Provides a high-level overview of financial metrics from PostgreSQL, including:
    - **Month-to-Date (MTD) Spend**: Total cost incurred in the current calendar month.
    - **Burn Rate**: An estimated monthly spend based on recent daily average consumption (e.g., last 30 days).
    
    Results can be filtered by a specific Google Cloud project.
    """
    mtd_spend = crud.get_mtd_spend(db=db, project=project)
    burn_rate = crud.get_burn_rate(db=db, project=project) # Defaults to 30 days
    
    return {
        "mtd_spend": mtd_spend,
        "burn_rate_estimated_monthly": burn_rate
    }

# --- LLM Integration Endpoints ---
@router.post("/generate-spend-summary", response_model=schemas.LLMInsight, status_code=201,
             summary="Generate an AI-driven spend summary using LLM",
             response_description="The newly created LLM insight record containing the spend summary.")
async def generate_ai_spend_summary( # Changed to async
    project: Optional[str] = Query(None, description="Optional: Filter data by Google Cloud project ID for summary generation"),
    start_date: Optional[datetime] = Query(None, description="Optional: Start date for the period to summarize"),
    end_date: Optional[datetime] = Query(None, description="Optional: End date for the period to summarize"),
    db: Session = Depends(get_db)
):
    """
    Triggers the LLM to generate a natural language summary of cloud spend for a given period and/or project.
    The generated summary is stored as an LLMInsight and returned.
    """
    # 1. Retrieve relevant aggregated cost data from PostgreSQL
    aggregated_data = crud.get_aggregated_cost_data(
        db=db, 
        project=project, 
        start_date=start_date, 
        end_date=end_date,
        limit=1000 # Limit data passed to LLM to avoid excessive context or cost
    )

    if not aggregated_data:
        raise HTTPException(status_code=404, detail="No aggregated cost data found for the specified criteria to generate a summary.")

    # 2. Call the LLM service to generate the summary
    summary_text = await llm_service.generate_spend_summary(aggregated_data) # Added await

    # 3. Store the generated insight in the database
    insight_create = schemas.LLMInsightCreate(
        insight_type="spend_summary",
        insight_text=summary_text,
        related_finops_data_id=None # Can be linked to specific data if aggregated
    )
    db_insight = crud.create_llm_insight(db=db, insight=insight_create)
    
    return db_insight

@router.post("/llm-insight", response_model=schemas.LLMInsight, status_code=201,
             summary="Create a new LLM-generated insight",
             response_description="The newly created LLM insight record.")
def create_llm_insight(
    insight: schemas.LLMInsightCreate, 
    db: Session = Depends(get_db)
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

# --- BigQuery Exploration & Ingestion Endpoints ---
@router.get("/bigquery/datasets", summary="List all accessible BigQuery datasets", response_model=List[str])
async def list_gcp_bigquery_datasets(): # Changed to async
    """
    Retrieves a list of all BigQuery datasets that the configured service account
    has access to in the GCP project.
    """
    try:
        loop = asyncio.get_running_loop()
        datasets = await loop.run_in_executor(None, bigquery_service.list_bigquery_datasets)
        return datasets
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list BigQuery datasets: {e}")

@router.get("/bigquery/datasets/{dataset_id}/tables", summary="List all tables in a BigQuery dataset", response_model=List[str])
async def list_gcp_bigquery_tables(dataset_id: str): # Changed to async
    """
    Retrieves a list of all tables within a specified BigQuery dataset that the
    configured service account has access to.
    - **dataset_id**: The ID of the BigQuery dataset.
    """
    try:
        loop = asyncio.get_running_loop()
        tables = await loop.run_in_executor(None, bigquery_service.list_bigquery_tables, dataset_id)
        return tables
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list BigQuery tables in dataset '{dataset_id}': {e}")

@router.get("/bigquery/datasets/{dataset_id}/tables/{table_id}/data", summary="Read data directly from a BigQuery table", response_model=List[Dict[str, Any]])
async def read_bigquery_table_data(
    dataset_id: str,
    table_id: str,
    limit: Optional[int] = Query(None, ge=1, description="Optional: Limit the number of rows to return.")
):
    """
    Reads a limited number of rows directly from a specified BigQuery table.
    - **dataset_id**: The ID of the BigQuery dataset.
    - **table_id**: The ID of the BigQuery table.
    - **limit**: Maximum number of rows to return.
    """
    try:
        loop = asyncio.get_running_loop()
        data = await loop.run_in_executor(None, bigquery_service.read_bigquery_table_data, dataset_id, table_id, limit)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read data from BigQuery table '{dataset_id}.{table_id}': {e}")

@router.post("/bigquery/ingest-billing-data", status_code=201, 
             summary="Ingest BigQuery billing data into PostgreSQL",
             response_description="Number of records ingested into PostgreSQL.")
async def ingest_bigquery_billing_data( # Changed to async
    dataset_id: str = Query(..., description="BigQuery dataset ID, e.g., 'finopsDS'"),
    table_id: str = Query(..., description="BigQuery table ID, e.g., 'gcp_billing_export_resource_v1_...'"),
    start_date: Optional[date] = Query(None, description="Optional: Start date for billing data ingestion (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="Optional: End date for billing data ingestion (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """
    Fetches billing data from the specified BigQuery table and ingests it into
    the PostgreSQL `aggregated_cost_data` table.
    """
    try:
        loop = asyncio.get_running_loop()
        billing_data = await loop.run_in_executor(
            None, 
            bigquery_service.get_billing_data_for_aggregation,
            dataset_id,
            table_id,
            start_date,
            end_date
        )
        
        ingested_count = 0
        if billing_data:
            # CRUD operations are blocking, so also run in executor
            await loop.run_in_executor(None, crud.bulk_create_aggregated_cost_data, db, billing_data)
            ingested_count = len(billing_data)
        
        return {"message": f"Successfully ingested {ingested_count} records from BigQuery into PostgreSQL."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to ingest BigQuery data: {e}")