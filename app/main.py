import os
from pathlib import Path

if os.name == 'nt':
    msys_path = Path(r"C:\msys64\mingw64\bin")
    if msys_path.exists():
        os.add_dll_directory(str(msys_path))
else:
    pass

from fastapi import FastAPI, Request, Depends, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

from datetime import datetime, time, date, timedelta
from calendar import monthrange

from .database import Base, engine, get_db, SessionLocal
from . import models
from .authentification import get_user_by_username, verify_password, init_admin_user, create_user
from .config import settings

app = FastAPI()

Base.metadata.create_all(bind=engine)

app.add_middleware(SessionMiddleware, secret_key = settings.SECRET_KEY)

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")



#========================login page functions========================

@app.on_event("startup")
def on_startup():
    engine.dispose()

    db = SessionLocal()
    try:
        init_admin_user(db)
    finally:
        db.close()

def get_current_user(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return db.query(models.User).filter(models.User.id == user_id).first()

@app.get("/", response_class = HTMLResponse)
def root(request: Request):
    if request.session.get("user_id"):
        return RedirectResponse(url = "/dashboard")
    return RedirectResponse(url = "/login")


@app.get("/login", response_class=HTMLResponse)
def show_login(request: Request):
    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "error": None
        }
    )

@app.post("/login", response_class = HTMLResponse)
def do_login(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = get_user_by_username(db, username.strip().lower())
    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error": "Invalid username or password"
            },
            status_code = status.HTTP_401_UNAUTHORIZED
        )
    request.session["user_id"] = user.id
    return RedirectResponse(url = "/dashboard", status_code = status.HTTP_302_FOUND)

@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url = "/login", status_code = status.HTTP_302_FOUND)



#========================main menu functions========================

@app.get("/dashboard", response_class = HTMLResponse)
def dashboard(request: Request, current_user = Depends(get_current_user)):
    print("DEBUG USER:", current_user.username, "is_admin = ", current_user.is_admin)
    if current_user is None:
        return RedirectResponse(url = "/login", status_code= status.HTTP_302_FOUND)
    return templates.TemplateResponse(
        "dashboard.html",
        {
         "request": request,
         "user": current_user
        }
    )

@app.get("/users/new", response_class = HTMLResponse)
def show_create_user(request: Request, current_user = Depends(get_current_user)):
    if not current_user or not current_user.is_admin:
        return RedirectResponse("/dashboard", status_code=302)
    return templates.TemplateResponse("create_user.html", {"request": request, "error": None})

@app.post("/users/new")
def create_new_user(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    if not current_user or not current_user.is_admin:
        raise HTTPException(status_code=403)
    if get_user_by_username(db,username):
        return templates.TemplateResponse("create_user.html", {"request": request, "error": "Invalid: Username already exists"})

    create_user(db, username = username, password = password, is_admin = True)
    return RedirectResponse("/dashboard", status_code = 302)



#========================page 1 quiz========================

@app.get("/observation/page1", response_class = HTMLResponse)
def show_observation_page1(request: Request):
    return templates.TemplateResponse("page1.html", {"request": request})

@app.post("/observation/page1")
def submit_observation_page1(request: Request, date_str: str = Form(...), profession: str = Form(...), section: str = Form(...), salon: str = Form(...), db: Session = Depends(get_db)):
    parsed_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    current_user_id = request.session.get("user_id")
    new_obs = models.Observation(user_id = current_user_id, date = parsed_date, profession = profession, section = section, salon = salon)

    db.add(new_obs)
    db.commit()
    db.refresh(new_obs)

    request.session["current_observation_id"] = new_obs.id
    return RedirectResponse(url = "/observation/page2", status_code=302)



#========================page 2 quiz========================

@app.get("/observation/page2", response_class = HTMLResponse)
def show_page2(request: Request):
    return templates.TemplateResponse("page2.html", {"request" : request})

@app.post("/observation/page2")
def submit_page2(request: Request, apa_curenta: str = Form(...), sapun_lichid: str = Form(...), prosop_hartie: str = Form(...), dezinfectant: str = Form(...), pictograme: str = Form(...), pregatire_maini: str = Form(...), db: Session = Depends(get_db)):
    observation_id = request.session.get("current_observation_id")

    if not observation_id:
        return RedirectResponse("/dashboard", status_code = 302)
    page2_check = models.Page2Check(observation_id=observation_id, apa_curenta=apa_curenta, sapun_lichid=sapun_lichid, prosop_hartie=prosop_hartie, dezinfectant=dezinfectant, pictograme=pictograme, pregatire_maini=pregatire_maini)

    db.add(page2_check)
    db.commit()

    return RedirectResponse("/observation/page3", status_code = 302)



#========================page 3 quiz========================

@app.get("/observation/page3", response_class=HTMLResponse)
def show_page3(request: Request):
    return templates.TemplateResponse("page3.html", {"request": request})

@app.post("/observation/page3")
async def submit_page3(request: Request, db: Session = Depends(get_db)):
    observation_id = request.session.get("current_observation_id")

    if not observation_id:
        return RedirectResponse("/dashboard", status_code = 302)

    form_data = await request.form()

    for step in range(1,6):
        mandatory_val = form_data.get(f"step{step}_mandatory")
        is_mandatory = mandatory_val == "mandatory"

        method = form_data.get(f"step{step}_method") or None
        rating = form_data.get(f"step{step}_rating") or None

        final_step = models.FinalStep(
            observation_id = observation_id,
            step_number = step,
            is_mandatory = is_mandatory,
            method = method,
            rating = rating,
        )
        db.add(final_step)

    db.commit()

    return RedirectResponse("/dashboard", status_code = 302)



#========================second dash========================

@app.get("/statistics", response_class = HTMLResponse)
def statistics_dashboard(request: Request):
    return templates.TemplateResponse("statistics_dashboard.html", {"request": request})



#========================statistics page 2========================

@app.get("/statistics/page2", response_class=HTMLResponse)
def statistics_page2(
    request: Request,
    year: int | None = None,
    month: int | None = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    today = date.today()
    year = year or today.year
    month = month or today.month

    start_date = date(year, month, 1)
    end_date = date(year, month, monthrange(year, month)[1])

    if not current_user:
        return RedirectResponse("/login", status_code=302)

    base_query = (
        db.query(models.Observation, models.Page2Check)
        .join(models.Page2Check)
        .filter(models.Observation.date >= start_date)
        .filter(models.Observation.date <= end_date)
        .order_by(models.Observation.date)
    )

    if not current_user.is_admin:
        base_query = base_query.filter(
            models.Observation.user_id == current_user.id
        )

    results = base_query.all()

    return templates.TemplateResponse(
        "stats_page2.html",
        {
            "request": request,
            "results": results,
            "year": year,
            "month": month,
        }
    )

@app.get("/statistics/page2/pdf")
def export_page2_pdf(
    request: Request,
    year: int,
    month: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    try:
        from weasyprint import HTML
    except ImportError as e:
        return Response(content=f"PDF Library Error: {str(e)}", status_code=500)

    start_date = date(year, month, 1)
    end_date = date(year, month, monthrange(year, month)[1])

    base_query = (
        db.query(models.Observation)
        .join(models.Page2Check)
        .filter(models.Observation.date >= start_date)
        .filter(models.Observation.date <= end_date)
        .order_by(models.Observation.date)
    )

    if not current_user.is_admin:
        base_query = base_query.filter(
            models.Observation.user_id == current_user.id
        )

    results = base_query.all()

    html_content = templates.get_template(
        "stats_page2_pdf.html"
    ).render(
        results=results,
        year=year,
        month=month,
        generated_at=datetime.now().strftime("%d.%m.%Y %H:%M"),
        user=current_user,
    )

    pdf = HTML(string=html_content).write_pdf()

    return Response(
        pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'attachment; filename="raport_pagina2_{year}_{month}.pdf"'
            )
        },
    )



#========================statistics for page 3========================

@app.get("/statistics/page3", response_class=HTMLResponse)
def stats_page3(
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    days: int = 30,
):

    end_date = date.today()
    start_date = end_date - timedelta(days=days - 1)

    obs_query = (
        db.query(models.Observation)
        .filter(models.Observation.date >= start_date)
        .filter(models.Observation.date <= end_date)
    )

    if not current_user.is_admin:
        obs_query = obs_query.filter(
            models.Observation.user_id == current_user.id
        )

    observations = obs_query.order_by(
        models.Observation.date.desc()
    ).all()

    obs_ids = [o.id for o in observations]
    total_recordings = len(obs_ids)

    if total_recordings == 0:
        return templates.TemplateResponse(
            "stats_page3.html",
            {
                "request": request,
                "days": days,
                "start_date": start_date,
                "end_date": end_date,
                "total_recordings": 0,
                "perfect_records": 0,
                "overall_percent": 0,
                "good_hospital": False,
                "step_stats": {
                    i: {"total": 0, "C": 0, "fail": 0, "percent": 0}
                    for i in range(1, 6)
                },
            }
        )

    steps = (
        db.query(models.FinalStep)
        .filter(models.FinalStep.observation_id.in_(obs_ids))
        .filter(models.FinalStep.is_mandatory == True)
        .all()
    )

    steps_by_obs = {}
    for s in steps:
        steps_by_obs.setdefault(s.observation_id, []).append(s)

    perfect_records = 0
    for obs_id in obs_ids:
        obs_steps = steps_by_obs.get(obs_id, [])
        if not obs_steps:
            continue
        if all(st.rating == "C" for st in obs_steps):
            perfect_records += 1

    overall_percent = round((perfect_records / total_recordings) * 100, 1)
    good_hospital = overall_percent >= 80.0

    step_stats = {
        i: {"total": 0, "C": 0, "fail": 0, "percent": 0}
        for i in range(1, 6)
    }

    for s in steps:
        if s.step_number not in step_stats:
            continue
        step_stats[s.step_number]["total"] += 1
        if s.rating == "C":
            step_stats[s.step_number]["C"] += 1
        else:
            step_stats[s.step_number]["fail"] += 1

    for i in range(1, 6):
        total = step_stats[i]["total"]
        c = step_stats[i]["C"]
        step_stats[i]["percent"] = round((c / total) * 100, 1) if total else 0

    return templates.TemplateResponse(
        "stats_page3.html",
        {
            "request": request,
            "days": days,
            "start_date": start_date,
            "end_date": end_date,
            "total_recordings": total_recordings,
            "perfect_records": perfect_records,
            "overall_percent": overall_percent,
            "good_hospital": good_hospital,
            "step_stats": step_stats,
        }
    )

