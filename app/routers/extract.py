from fastapi import APIRouter, HTTPException

from app.models import ExtractRequest, ExtractResponse
from app.services.ai_service import (
    AiBadResponseError,
    AiExtractionError,
    AiUnavailableError,
    extract_tasks,
)

router = APIRouter(tags=["extract"])


@router.post("/api/extract", response_model=ExtractResponse)
def extract(payload: ExtractRequest):
    try:
        result = extract_tasks(payload.text)
        if len(result.tasks) > 10:
            raise HTTPException(
                status_code=502, detail="AI extraction failed."
            ) from None
        return result
    except AiUnavailableError:
        raise HTTPException(
            status_code=503, detail="AI service is not configured."
        ) from None
    except AiBadResponseError:
        raise HTTPException(
            status_code=502, detail="AI extraction failed."
        ) from None
    except AiExtractionError:
        raise HTTPException(
            status_code=502, detail="AI extraction failed."
        ) from None
