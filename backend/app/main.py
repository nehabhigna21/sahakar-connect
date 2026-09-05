import os

from fastapi.middleware.cors import CORSMiddleware
#CORSMiddleware — need to let a browser-based frontend call this API

from fastapi import FastAPI
#FastAPI — the core framework class.

from . import models
#models — your database table definitions (likely SQLAlchemy models)


from .database import engine

from .routers import auth as auth_router
from .routers import (
    bandit_routes,
    bookings,
    catalog,
    forecast_routes,
    grievances,
    payments_routes,
    piggybank_routes,
    reviews,
    workers,
)

# This scans models.py for every class inheriting from Base and creates
# the matching SQL table if it doesn't already exist in bluedot.db.
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Bluedot API", version="0.1.0")

# Browsers block a webpage on one origin (localhost:5173, our React app)
# from calling an API on another origin (localhost:8000, this server)
# unless the server explicitly allows it - that's what CORS is for.
# FRONTEND_URL is the deployed frontend's real origin (set as an env var
# on the host, e.g. https://sahakar-connect.vercel.app) - kept separate
# from localhost/tunnel origins so those still work in local dev too.
_frontend_url = os.environ.get("FRONTEND_URL", "")
_extra_origins = [_frontend_url] if _frontend_url else []

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", *_extra_origins],
    # Cloudflare Tunnel gives the frontend a fresh *.trycloudflare.com
    # origin each time it's started - regex covers that without needing
    # a restart every time the tunnel URL changes.
    allow_origin_regex=r"https://.*\.trycloudflare\.com",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(catalog.router)
app.include_router(workers.router)
app.include_router(bookings.router)
app.include_router(reviews.router)
app.include_router(bandit_routes.router)
app.include_router(piggybank_routes.router)
app.include_router(forecast_routes.router)
app.include_router(grievances.router)
app.include_router(payments_routes.router)


@app.get("/")
def root():
    return {"status": "ok", "service": "bluedot-api"}
