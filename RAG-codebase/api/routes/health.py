from fastapi import APIRouter
from api.models.response import HealthResponse

router = APIRouter()

# ALB pings this every 30s.
# Must return 200 or ALB marks the target unhealthy
# and stops routing traffic to this container.
@router.get("/health", response_model=HealthResponse)
def health_check():
    return HealthResponse(status="ok", version="1.0.0")