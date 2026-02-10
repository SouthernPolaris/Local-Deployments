from app.api.routes import router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Cyber Range Orchestrator",
    description="Software-Defined Cyber Range Infrastructure Manager",
    version="0.1.0",
)

origins = [
    "http://localhost:5173",  # Vite frontend
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "Cyber Range API is Online", "mode": "Mock" if True else "Prod"}
