from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from datetime import datetime, date
from typing import Optional
from app.models import APODResponse, APODListResponse
from app.service import nasa_service
from app.config import settings


app = FastAPI(
    title="NASA APOD API",
    description="A RESTful API for browsing NASA's Astronomy Picture of the Day",
    version="1.0.0",
    docs_url="/",
    redoc_url="/redoc"
)


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    await nasa_service.initialize()
    # Preload recent APODs in background
    await nasa_service.preload_recent_apods(days=7)


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    await nasa_service.close()


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.get("/api/apod", response_model=APODResponse, tags=["APOD"])
async def get_apod(date_param: Optional[str] = None):
    """
    Get Astronomy Picture of the Day
    
    - **date_param**: Optional date in YYYY-MM-DD format. Defaults to today.
    
    Returns the APOD for the specified date with navigation links to next/prev.
    """
    try:
        # Parse date if provided
        if date_param:
            try:
                target_date = datetime.strptime(date_param, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid date format. Use YYYY-MM-DD"
                )
        else:
            target_date = date.today()
        
        # Validate date range
        if target_date < nasa_service.APOD_START_DATE:
            raise HTTPException(
                status_code=400,
                detail=f"Date must be on or after {nasa_service.APOD_START_DATE.isoformat()}"
            )
        
        if target_date > date.today():
            raise HTTPException(
                status_code=400,
                detail="Cannot request future dates"
            )
        
        # Fetch APOD data
        apod_data = await nasa_service.fetch_apod(target_date)
        
        # Add navigation links
        next_date = nasa_service.get_next_date(target_date)
        prev_date = nasa_service.get_prev_date(target_date)
        
        apod_data["next_date"] = f"/api/apod?date={next_date.isoformat()}" if next_date else None
        apod_data["prev_date"] = f"/api/apod?date={prev_date.isoformat()}" if prev_date else None
        
        return APODResponse(**apod_data)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching APOD: {str(e)}"
        )


@app.get("/api/apod/today", response_model=APODResponse, tags=["APOD"])
async def get_today_apod():
    """
    Get today's Astronomy Picture of the Day
    
    This is a convenience endpoint that always returns today's APOD.
    """
    return await get_apod(date_param=None)


@app.get("/api/apod/{date_str}", response_model=APODResponse, tags=["APOD"])
async def get_apod_by_date(date_str: str):
    """
    Get APOD by date (alternative endpoint format)
    
    - **date_str**: Date in YYYY-MM-DD format
    
    RESTful endpoint for accessing APOD by date as a path parameter.
    """
    return await get_apod(date_param=date_str)


@app.get("/api/apod/list/cached", response_model=APODListResponse, tags=["APOD"])
async def list_cached_apods():
    """
    List all cached APODs
    
    Returns a list of all APODs currently available in the cache.
    This provides fast browsing of previously fetched APODs.
    """
    try:
        dates = await nasa_service.get_available_dates()
        
        results = []
        for date_str in dates[:50]:  # Limit to 50 most recent
            try:
                target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                apod_data = await nasa_service.fetch_apod(target_date)
                
                # Add navigation links
                next_date = nasa_service.get_next_date(target_date)
                prev_date = nasa_service.get_prev_date(target_date)
                
                apod_data["next_date"] = f"/api/apod?date={next_date.isoformat()}" if next_date else None
                apod_data["prev_date"] = f"/api/apod?date={prev_date.isoformat()}" if prev_date else None
                
                results.append(APODResponse(**apod_data))
            except Exception:
                continue
        
        return APODListResponse(count=len(results), results=results)
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error listing cached APODs: {str(e)}"
        )


@app.post("/api/apod/preload", tags=["Admin"])
async def preload_apods(background_tasks: BackgroundTasks, days: int = 30):
    """
    Preload APODs into cache
    
    - **days**: Number of days to preload (default: 30)
    
    This endpoint triggers a background task to preload APODs into the cache.
    Useful for warming up the cache or loading historical data.
    """
    if days < 1 or days > 365:
        raise HTTPException(
            status_code=400,
            detail="Days must be between 1 and 365"
        )
    
    background_tasks.add_task(nasa_service.preload_recent_apods, days=days)
    
    return {
        "status": "preload started",
        "days": days,
        "message": f"Preloading {days} days of APOD data in background"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )
