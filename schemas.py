from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List

# Vibe Station schemas

class Pricing(BaseModel):
    type: str = Field(..., description="one-time | subscription | negotiation")
    amount: Optional[float] = Field(None, ge=0)
    currency: str = Field("USD")

class Links(BaseModel):
    external_url: Optional[HttpUrl] = None
    github_url: Optional[HttpUrl] = None
    embed_url: Optional[HttpUrl] = None
    zip_url: Optional[HttpUrl] = None

class AIInsights(BaseModel):
    summary: Optional[str] = None
    pitch: Optional[str] = None
    landing_copy: Optional[str] = None
    deck_outline: Optional[List[str]] = None
    tags: List[str] = []
    readiness_score: Optional[float] = Field(None, ge=0, le=100)
    market_fit_score: Optional[float] = Field(None, ge=0, le=100)
    suggestions: Optional[List[str]] = None

class Project(BaseModel):
    name: str
    description: Optional[str] = None
    tech_stack: List[str] = []
    category: Optional[str] = None
    pricing: Optional[Pricing] = None
    status: str = Field("MVP", description="MVP | prototype | commercial-ready")
    links: Optional[Links] = None
    thumbnails: List[str] = []
