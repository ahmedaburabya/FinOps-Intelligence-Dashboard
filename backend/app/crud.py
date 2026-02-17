"""
CRUD (Create, Read, Update, Delete) operations for SQLAlchemy models.
This module provides functions to interact with the database, abstracting
away the direct SQLAlchemy session management from the API endpoints.
"""

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta  # timedelta added here
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
    limit: Optional[int] = 100,
    service: Optional[str] = None,
    project: Optional[str] = None,
    sku: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> tuple[List[models.AggregatedCostData], int]:  # Updated return type
    """
    Retrieves multiple aggregated cost data records with optional filtering,
    including total count for pagination.
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

    total_count = query.count()  # Get total count before applying skip/limit

    query = query.offset(skip)
    if limit is not None:
        query = query.limit(limit)

    return query.all(), total_count  # Return both data and count


def create_aggregated_cost_data(
    db: Session, cost_data: schemas.AggregatedCostDataCreate
):
    """
    Creates a new aggregated cost data record or updates an existing one if a conflict occurs.
    This implements an "upsert" strategy based on the unique constraint (service, project, sku, time_period).
    """
    # Prepare the insert statement with on_conflict_do_update clause
    insert_stmt = insert(models.AggregatedCostData).values(**cost_data.model_dump())

    on_conflict_stmt = insert_stmt.on_conflict_do_update(
        index_elements=["service", "project", "sku", "time_period"],
        set_={
            "cost": insert_stmt.excluded.cost,
            "currency": insert_stmt.excluded.currency,
            "usage_amount": insert_stmt.excluded.usage_amount,
            "usage_unit": insert_stmt.excluded.usage_unit,
            "updated_at": datetime.utcnow(),  # Explicitly update updated_at
        },
    ).returning(
        models.AggregatedCostData
    )  # Return the updated/inserted object

    # Execute the upsert statement
    result = db.execute(on_conflict_stmt)
    db_cost_data = result.scalars().first()  # Get the resulting object

    db.commit()
    db.refresh(db_cost_data)  # Refresh to ensure all fields are loaded, including id
    return db_cost_data


def bulk_create_aggregated_cost_data(
    db: Session, cost_data_list: List[schemas.AggregatedCostDataCreate]
):
    """
    Performs a bulk insertion or update of multiple aggregated cost data records into the database.
    This uses an "upsert" strategy for efficiency and to handle duplicate entries based on
    the unique constraint (service, project, sku, time_period).
    """
    if not cost_data_list:
        return []

    # Prepare a list of dictionaries from the Pydantic models
    values_to_insert = [item.model_dump() for item in cost_data_list]

    # Create an insert statement with on_conflict_do_update
    insert_stmt = insert(models.AggregatedCostData).values(values_to_insert)

    on_conflict_stmt = insert_stmt.on_conflict_do_update(
        index_elements=["service", "project", "sku", "time_period"],
        set_={
            "cost": insert_stmt.excluded.cost,
            "currency": insert_stmt.excluded.currency,
            "usage_amount": insert_stmt.excluded.usage_amount,
            "usage_unit": insert_stmt.excluded.usage_unit,
            "updated_at": datetime.utcnow(),  # Explicitly update updated_at
        },
    ).returning(models.AggregatedCostData)

    # Execute the upsert statement
    result = db.execute(on_conflict_stmt)
    db.commit()

    # Fetch the results after commit. For bulk operations, scalars().all() is often used.
    # Note: refresh might not be directly applicable to all items in a bulk upsert
    # without re-querying or explicitly handling the returned values.
    # We are returning the objects that were either inserted or updated.
    return result.scalars().all()


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


def get_daily_burn_rate_mtd(db: Session, project: Optional[str] = None):
    """
    Calculates the average daily spend in the current month (Daily Burn Rate MTD).
    Daily Burn Rate = MTD Spend / Number of Days Elapsed in current month.
    """
    mtd_spend = get_mtd_spend(db, project)  # Reuse existing MTD calculation

    now_utc = datetime.utcnow()
    current_month_start = now_utc.replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    )

    # Calculate number of days elapsed in current month
    # This includes the current day.
    num_days_elapsed = (now_utc.date() - current_month_start.date()).days + 1

    if num_days_elapsed == 0:  # Avoid division by zero if it's somehow day 0
        return 0.0

    daily_burn_rate = mtd_spend / num_days_elapsed
    return daily_burn_rate


def get_projected_month_end_spend(db: Session, project: Optional[str] = None):
    """
    Calculates the projected total spend for the current month.
    Projected Total = MTD Spend + (Daily Burn Rate (MTD) * Days Remaining)
    """
    mtd_spend = get_mtd_spend(db, project)
    daily_burn_rate_mtd = get_daily_burn_rate_mtd(db, project)

    now_utc = datetime.utcnow()
    # Calculate days remaining in current month
    # Get the first day of the next month
    next_month = now_utc.replace(day=28) + timedelta(
        days=4
    )  # move to the 28th, then +4 to ensure we're in next month
    month_end = next_month.replace(day=1) - timedelta(
        days=1
    )  # last day of current month

    days_remaining = (month_end.date() - now_utc.date()).days

    projected_total = mtd_spend + (daily_burn_rate_mtd * days_remaining)
    return projected_total


def get_distinct_services_from_db(db: Session) -> List[str]:
    """
    Retrieves a list of distinct service names from the AggregatedCostData table.
    """
    # Query for distinct values of the 'service' column
    # The 'service' column in AggregatedCostData model is a String
    distinct_services = (
        db.query(models.AggregatedCostData.service)
        .distinct()
        .order_by(models.AggregatedCostData.service)
        .all()
    )
    # Extract the service names from the list of Row objects
    return [service[0] for service in distinct_services]


def get_distinct_projects_from_db(db: Session) -> List[str]:
    """
    Retrieves a list of distinct project IDs from the AggregatedCostData table.
    """
    distinct_projects = (
        db.query(models.AggregatedCostData.project)
        .distinct()
        .filter(
            models.AggregatedCostData.project.isnot(None)
        )  # Filter out None/NULL projects
        .order_by(models.AggregatedCostData.project)
        .all()
    )
    return [project[0] for project in distinct_projects]


def get_distinct_skus_from_db(db: Session) -> List[str]:
    """
    Retrieves a list of distinct SKUs from the AggregatedCostData table.
    """
    distinct_skus = (
        db.query(models.AggregatedCostData.sku)
        .distinct()
        .filter(models.AggregatedCostData.sku.isnot(None))  # Filter out None/NULL SKUs
        .order_by(models.AggregatedCostData.sku)
        .all()
    )
    return [sku[0] for sku in distinct_skus]
