# app/routers/statistics.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import crud, schemas
from ..database import get_db
from ..dependencies import ActiveUser

router = APIRouter(
    prefix="/statistics",
    tags=["إحصائيات (Statistics)"],
)

@router.get("/", response_model=schemas.ReportStats)
def get_report_statistics(
    db: Session = Depends(get_db),
    current_user: schemas.UserRead = Depends(ActiveUser),
):
    """
    جلب إحصائيات مجمعة للتقارير.
    """
    return crud.get_user_report_stats(db=db, user_id=current_user.id)
