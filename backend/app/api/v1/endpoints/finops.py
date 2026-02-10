"""
API endpoints for FinOps data and LLM insights.
This module defines the routes and their corresponding logic for
interacting with aggregated cost data and AI-generated insights.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app import crud, schemas
from app.database import get_db

# APIRouter creates path operations for FinOps module
router = APIRouter()

# --- Aggregated Cost Data Endpoints ---
@router.post("/aggregated-cost", response_model=schemas.AggregatedCostData, status_code=201, 
             summary="Create new aggregated cost data record",
             response_description="The newly created aggregated cost data record.")
def create_aggregated_cost_data(
    cost_data: schemas.AggregatedCostDataCreate, 
    db: Session = Depends(get_db)
):
    """
    Creates a new record of aggregated cloud cost data.
    
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
            summary="Retrieve aggregated cost data by ID",
            response_description="The aggregated cost data record matching the provided ID.")
def read_aggregated_cost_data(cost_data_id: int, db: Session = Depends(get_db)):
    """
    Retrieves a single aggregated cloud cost data record by its unique identifier.
    
    - **cost_data_id**: The unique ID of the aggregated cost data record.
    """
    db_cost_data = crud.get_aggregated_cost_data_by_id(db=db, cost_data_id=cost_data_id)
    if db_cost_data is None:
        raise HTTPException(status_code=404, detail="Aggregated cost data not found")
    return db_cost_data

@router.get("/aggregated-cost", response_model=List[schemas.AggregatedCostData],
            summary="Retrieve multiple aggregated cost data records with filters",
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
    Retrieves a list of aggregated cloud cost data records.
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

# --- FinOps Overview Endpoints ---
@router.get("/overview", 
             summary="Get high-level FinOps overview (MTD Spend, Burn Rate)",
             response_description="Key financial metrics including Month-to-Date spend and projected burn rate.")
def get_finops_overview(
    project: Optional[str] = Query(None, description="Optional: Filter overview by Google Cloud project ID"),
    db: Session = Depends(get_db)
):
    """
    Provides a high-level overview of financial metrics, including:
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

# --- LLM Insight Endpoints ---
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

@router.get("/llm-insight/{insight_id}", response_model=schemas.LLMInsight,
            summary="Retrieve LLM-generated insight by ID",
            response_description="The LLM insight record matching the provided ID.")
def read_llm_insight(insight_id: int, db: Session = Depends(get_db)):
    """
    Retrieves a single AI-generated insight record by its unique identifier.
    
    - **insight_id**: The unique ID of the LLM insight record.
    """
    db_insight = crud.get_llm_insight_by_id(db=db, insight_id=insight_id)
    if db_insight is None:
        raise HTTPException(status_code=404, detail="LLM insight not found")
    return db_insight

@router.get("/llm-insight", response_model=List[schemas.LLMInsight],
            summary="Retrieve multiple LLM-generated insights with filters",
            response_description="A list of LLM insights matching the filters.")
def read_llm_insights_list(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    insight_type: Optional[str] = Query(None, description="Filter by type of insight"),
    related_finops_data_id: Optional[int] = Query(None, description="Filter by related aggregated cost data ID"),
    start_date: Optional[datetime] = Query(None, description="Filter insights generated from this date (inclusive)"),
    end_date: Optional[datetime] = Query(None, description="Filter insights generated up to this date (inclusive)"),
    db: Session = Depends(get_db)
):
    """
    Retrieves a list of AI-generated insights.
    Supports pagination and filtering by insight type, related FinOps data, and date range.
    """
    llm_insights_list = crud.get_llm_insights(
        db=db, 
        skip=skip, 
        limit=limit, 
        insight_type=insight_type, 
        related_finops_data_id=related_finops_data_id,
        start_date=start_date,
        end_date=end_date
    )
    return llm_insights_list
