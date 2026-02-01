from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(
    title="Cyber Range Orchestrator",
    description="Software-Defined Cyber Range Infrastructure Manager",
    version="0.1.0"
)

# Plugs /range routes into server
app.include_router(router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Cyber Range API is Online", "mode": "Mock" if True else "Prod"}