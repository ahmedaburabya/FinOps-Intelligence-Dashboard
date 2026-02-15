"""
CRUD (Create, Read, Update, Delete) operations for SQLAlchemy models.
This module provides functions to interact with the database, abstracting
away the direct SQLAlchemy session management from the API endpoints.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from typing import List, Optional

from app import models, schemas


# --- CRUD for AggregatedCostData ---
def get_aggregated_cost_data_by_id(db: Session, cost_data_id: int):
    """
    Retrieves a single aggregated cost data record by its ID.
    """
    return (
        db.query(models.AggregatedCostData)
        .filter(models.AggregatedCostData.id == cost_data_id)
        .first()
    )


def get_aggregated_cost_data(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    service: Optional[str] = None,
    project: Optional[str] = None,
    sku: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
):
    """
    Retrieves multiple aggregated cost data records with optional filtering.
    """
    query = db.query(models.AggregatedCostData)
    if service:
        query = query.filter(models.AggregatedCostData.service == service)
    if project:
        query = query.filter(models.AggregatedCostData.project == project)
    if sku:
        query = query.filter(models.AggregatedCostData.sku == sku)
    if start_date:
        query = query.filter(models.AggregatedCostData.time_period >= start_date)
    if end_date:
        query = query.filter(models.AggregatedCostData.time_period <= end_date)

    return query.offset(skip).limit(limit).all()


def create_aggregated_cost_data(
    db: Session, cost_data: schemas.AggregatedCostDataCreate
):
    """
    Creates a new aggregated cost data record in the database.
    """
    db_cost_data = models.AggregatedCostData(**cost_data.model_dump())
    db.add(db_cost_data)
    db.commit()
    db.refresh(db_cost_data)
    return db_cost_data


def bulk_create_aggregated_cost_data(
    db: Session, cost_data_list: List[schemas.AggregatedCostDataCreate]
):
    """
    Performs a bulk insertion of multiple aggregated cost data records into the database.
    This is more efficient than inserting records one by one.
    """
    db_objects = [
        models.AggregatedCostData(**item.model_dump()) for item in cost_data_list
    ]
    db.add_all(db_objects)
    db.commit()
    # Refreshing all objects after bulk insert might be resource-intensive for very large lists.
    # For simplicity, we'll return the list of created objects without individual refreshes.
    return db_objects


# --- CRUD for LLMInsight ---
def get_llm_insight_by_id(db: Session, insight_id: int):
    """
    Retrieves a single LLM insight record by its ID.
    """
    return (
        db.query(models.LLMInsight).filter(models.LLMInsight.id == insight_id).first()
    )


def get_llm_insights(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    insight_type: Optional[str] = None,
    related_finops_data_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
):
    """
    Retrieves multiple LLM insight records with optional filtering.
    """
    query = db.query(models.LLMInsight)
    if insight_type:
        query = query.filter(models.LLMInsight.insight_type == insight_type)
    if related_finops_data_id:
        query = query.filter(
            models.LLMInsight.related_finops_data_id == related_finops_data_id
        )
    if start_date:
        query = query.filter(models.LLMInsight.timestamp >= start_date)
    if end_date:
        query = query.filter(models.LLMInsight.timestamp <= end_date)

    return query.offset(skip).limit(limit).all()


def create_llm_insight(db: Session, insight: schemas.LLMInsightCreate):
    """
    Creates a new LLM insight record in the database.
    """
    db_insight = models.LLMInsight(**insight.model_dump())
    db.add(db_insight)
    db.commit()
    db.refresh(db_insight)
    return db_insight


# --- Aggregation Functions (FinOps Engine Core Logic) ---
def get_mtd_spend(db: Session, project: Optional[str] = None):
    """
    Calculates Month-to-Date (MTD) spend.
    Assumes `time_period` in `AggregatedCostData` is at least daily.
    """
    current_month_start = datetime.utcnow().replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    )
    query = db.query(func.sum(models.AggregatedCostData.cost)).filter(
        models.AggregatedCostData.time_period >= current_month_start
    )
    if project:
        query = query.filter(models.AggregatedCostData.project == project)

    mtd_spend = query.scalar()
    return mtd_spend if mtd_spend is not None else 0.0


def get_burn_rate(db: Session, days: int = 30, project: Optional[str] = None):
    """
    Calculates a simple burn rate over the last 'days' (e.g., 30 days).
    """
    from datetime import timedelta

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    query = db.query(func.sum(models.AggregatedCostData.cost)).filter(
        models.AggregatedCostData.time_period >= start_date,
        models.AggregatedCostData.time_period <= end_date,
    )
    if project:
        query = query.filter(models.AggregatedCostData.project == project)

    total_spend = query.scalar()
    if total_spend is None:
        return 0.0

    # Average daily spend over the period
    avg_daily_spend = total_spend / days
    # Simple projection for monthly burn rate
    monthly_burn_rate = avg_daily_spend * 30
    return monthly_burn_rate
