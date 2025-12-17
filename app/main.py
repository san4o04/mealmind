from fastapi import FastAPI
from sqlalchemy import text

from app.infrastructure.db import engine

from app.api.v1.endpoints.profiles import router as profiles_router
from app.api.v1.endpoints.products import router as products_router
from app.api.v1.endpoints.meal_plans import router as meal_plans_router
from app.api.v1.endpoints.users import router as users_router
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints.auth import router as auth_router

app = FastAPI(title="MealMind API", version="0.1.0")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


API_PREFIX = "/api/v1"

app = FastAPI(title="MealMind API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users_router, prefix=API_PREFIX)
app.include_router(profiles_router, prefix=API_PREFIX)
app.include_router(products_router, prefix=API_PREFIX)
app.include_router(meal_plans_router, prefix=API_PREFIX)

app.include_router(auth_router, prefix=API_PREFIX)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/health/db")
def health_db():
    with engine.connect() as conn:
        value = conn.execute(text("SELECT 1")).scalar_one()
    return {"db": "ok", "select_1": value}
