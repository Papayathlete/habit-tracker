from __future__ import annotations

from datetime import date, timedelta

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, desc
from sqlalchemy.exc import IntegrityError

from .db import Base, engine, SessionLocal
from .models import HabitLog

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")

# 最小運用：起動時にテーブル作成
Base.metadata.create_all(bind=engine)

HABITS = ["英作文", "運動", "瞑想"]


def today() -> date:
    return date.today()


def last_n_days(n: int) -> list[date]:
    t = today()
    return [t - timedelta(days=i) for i in range(n)]


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    days = list(reversed(last_n_days(7)))  # 古い→新しいで表示
    t = today()

    with SessionLocal() as db:
        logs = db.execute(
            select(HabitLog)
            .where(HabitLog.log_date.in_(days), HabitLog.habit.in_(HABITS))
            .order_by(desc(HabitLog.log_date), HabitLog.habit)
        ).scalars().all()

    # (date, habit) -> done の辞書にしてテンプレで参照しやすくする
    status: dict[str, bool] = {}
    for l in logs:
        status[f"{l.log_date.isoformat()}::{l.habit}"] = l.done

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "habits": HABITS,
            "days": days,
            "today": t,
            "status": status,
        },
    )


@app.post("/log")
def log_habit(
    habit: str = Form(...),
    done: str = Form(...),  # "yes" or "no"
):
    if habit not in HABITS:
        return RedirectResponse(url="/?error=bad_habit", status_code=303)

    done_bool = True if done == "yes" else False
    t = today()

    with SessionLocal() as db:
        # まず既存を探して上書き（Upsert風）
        existing = db.execute(
            select(HabitLog).where(HabitLog.log_date == t, HabitLog.habit == habit)
        ).scalar_one_or_none()

        if existing:
            existing.done = done_bool
            db.commit()
        else:
            db.add(HabitLog(log_date=t, habit=habit, done=done_bool))
            try:
                db.commit()
            except IntegrityError:
                # 競合した場合の保険：再取得して上書き
                db.rollback()
                existing = db.execute(
                    select(HabitLog).where(HabitLog.log_date == t, HabitLog.habit == habit)
                ).scalar_one()
                existing.done = done_bool
                db.commit()

    return RedirectResponse(url="/", status_code=303)
