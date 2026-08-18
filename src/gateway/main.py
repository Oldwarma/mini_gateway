# spec: SPEC-007
"""FastAPI 入口（详细设计 §10）。"""
from __future__ import annotations

import uvicorn
from fastapi import FastAPI

from .api.routes import router

app = FastAPI(title="智能体迷你网关", description="基于可追踪 Harness 架构的智能体网关", version="0.1.0")
app.include_router(router)


if __name__ == "__main__":
    uvicorn.run("src.gateway.main:app", host="0.0.0.0", port=8000, reload=False)
