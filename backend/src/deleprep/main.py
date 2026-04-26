from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import auth, skills, tasks
from .database import engine, Base

Base.metadata.create_all(bind=engine)

app = FastAPI(title="DELE A2 Prep API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(skills.router)
app.include_router(tasks.router)

@app.get("/health")
def health_check():
    return {"status": "ok"}
