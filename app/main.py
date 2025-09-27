# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import auth, tasks, notes, habits, payments, ai, statistics
from .database import engine, Base 

# تهيئة FastAPI
app = FastAPI(
    title="TaskAI Backend API",
    description="واجهة برمجية خلفية لإدارة المهام والعادات والملاحظات",
    version="1.0.0",
)

# تفعيل CORS
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,   
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

app.include_router(auth.router)
app.include_router(tasks.router)
app.include_router(notes.router)
app.include_router(habits.router)
app.include_router(payments.router)
app.include_router(ai.router)
app.include_router(statistics.router)

@app.get("/")
def read_root():
    return {"message": "مرحباً بك في TaskAI Backend API - FastAPI قيد التشغيل!"}