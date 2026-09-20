from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import router
from app.api.admin_endpoints import admin_router
import os

app = FastAPI(title="Policy Reasoning Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")
app.include_router(admin_router, prefix="/api/admin")

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    from fastapi.responses import Response
    return Response(status_code=204)

# Ensure UI directory exists, then mount it
ui_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ui")
os.makedirs(ui_dir, exist_ok=True)
app.mount("/", StaticFiles(directory=ui_dir, html=True), name="ui")
