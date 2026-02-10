"""
Pydantic schemas for request and response validation.
These schemas define the data structures for API requests and responses,
ensuring data consistency and providing clear documentation for the API.
They are also used to serialize and deserialize data when interacting with
SQLAlchemy models.
"""

from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

# --- Aggregated Cost Data Schemas ---
class AggregatedCostDataBase(BaseModel):
    """
    Base Pydantic schema for aggregated cost data.
    Defines the common fields for creating or updating cost data.
    """
    service: str
    project: str
    sku: str
    time_period: datetime
    cost: float
    currency: str = "USD"
    usage_amount: Optional[float] = None
    usage_unit: Optional[str] = None

class AggregatedCostDataCreate(AggregatedCostDataBase):
    """
    Pydantic schema for creating a new aggregated cost data record.
    Inherits from AggregatedCostDataBase.
    """
    pass

class AggregatedCostData(AggregatedCostDataBase):
    """
    Pydantic schema for representing an aggregated cost data record read from the database.
    Includes database-generated fields like 'id' and timestamps.
    """
    id: int
    created_at: datetime
    updated_at: datetime
    
    # Configuration for Pydantic to work with SQLAlchemy models.
    # `from_attributes = True` (Pydantic V2) or `orm_mode = True` (Pydantic V1)
    # tells Pydantic to read data even if it is not a dict, but an ORM model.
    model_config = ConfigDict(from_attributes=True) # For Pydantic V2

# --- LLM Insight Schemas ---
class LLMInsightBase(BaseModel):
    """
    Base Pydantic schema for LLM insights.
    Defines common fields for creating or updating LLM insights.
    """
    insight_type: str
    insight_text: str
    related_finops_data_id: Optional[int] = None
    sentiment: Optional[str] = None

class LLMInsightCreate(LLMInsightBase):
    """
    Pydantic schema for creating a new LLM insight record.
    Inherits from LLMInsightBase.
    """
    pass

class LLMInsight(LLMInsightBase):
    """
    Pydantic schema for representing an LLM insight record read from the database.
    Includes database-generated fields like 'id' and timestamps.
    """
    id: int
    timestamp: datetime # Renamed from 'created_at' in the DB model for clarity in schema
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True) # For Pydantic V2

# --- Combined Schema for AggregatedCostData with related LLM Insights ---
class AggregatedCostDataWithInsights(AggregatedCostData):
    """
    Pydantic schema for representing aggregated cost data along with its related LLM insights.
    This demonstrates how to represent relationships in Pydantic.
    """
    llm_insights: list[LLMInsight] = []
