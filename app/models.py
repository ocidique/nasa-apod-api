from pydantic import BaseModel, Field
from typing import Optional
from datetime import date


class APODResponse(BaseModel):
    """Model for APOD API response"""
    date: str = Field(..., description="The date of the APOD")
    title: str = Field(..., description="The title of the APOD")
    explanation: str = Field(..., description="The description/explanation of the APOD")
    url: str = Field(..., description="The URL of the APOD image or video")
    media_type: str = Field(..., description="The type of media (image or video)")
    hdurl: Optional[str] = Field(None, description="The URL of the high-definition version")
    copyright: Optional[str] = Field(None, description="The copyright information")
    
    # Additional fields for browsability
    next_date: Optional[str] = Field(None, description="URL to next APOD")
    prev_date: Optional[str] = Field(None, description="URL to previous APOD")


class APODListResponse(BaseModel):
    """Model for listing multiple APODs"""
    count: int = Field(..., description="Number of APODs returned")
    results: list[APODResponse] = Field(..., description="List of APOD entries")
