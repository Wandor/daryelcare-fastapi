"""FastAPI entry point for the ReadyKids CMA portal."""

import os
from contextlib import asynccontextmanager
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from app.database import init_pool, close_pool
from app.routes.applications import router

load_dotenv()

PUBLIC_DIR = Path(__file__).resolve().parent.parent / "public"


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_pool()
    yield
    await close_pool()


app = FastAPI(title="ReadyKids CMA", lifespan=lifespan)

app.include_router(router)
app.mount("/static", StaticFiles(directory=str(PUBLIC_DIR)), name="static")


@app.get("/register")
async def register_page():
    return FileResponse(PUBLIC_DIR / "childminder-registration-complete.html")


@app.get("/admin")
async def admin_page():
    return FileResponse(PUBLIC_DIR / "cma-portal-v2.html")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "3000"))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
