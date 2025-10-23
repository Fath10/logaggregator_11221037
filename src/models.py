from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, validator
from enum import Enum


class EventPayload(BaseModel):
    class Config:
        extra = "allow"


class Event(BaseModel):
    topic: str = Field(..., min_length=1, max_length=255, description="Event topic")
    event_id: str = Field(..., min_length=1, max_length=255, description="Unique event identifier")
    timestamp: str = Field(..., description="ISO8601 timestamp")
    source: str = Field(..., min_length=1, max_length=255, description="Event source")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Event payload data")
    
    @validator('timestamp')
    def validate_timestamp(cls, v):
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
            return v
        except ValueError:
            raise ValueError('timestamp must be in ISO8601 format')
    
    class Config:
        json_schema_extra = {
            "example": {
                "topic": "user.login",
                "event_id": "evt-12345-abcde",
                "timestamp": "2025-10-23T10:30:00Z",
                "source": "auth-service",
                "payload": {
                    "user_id": "user-123",
                    "ip_address": "192.168.1.1",
                    "success": True
                }
            }
        }


class EventBatch(BaseModel):
    events: List[Event] = Field(..., min_items=1, description="List of events")


class PublishResponse(BaseModel):
    received: int
    accepted: int
    duplicates: int
    message: str


class EventsResponse(BaseModel):
    topic: str
    count: int
    events: List[Event]


class StatsResponse(BaseModel):
    received: int
    unique_processed: int
    duplicate_dropped: int
    topics: List[str]
    uptime_seconds: float
    uptime_human: str
