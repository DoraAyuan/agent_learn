import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router


def create_app() -> FastAPI:
    """
    创建并配置FastAPI应用实例

    Returns:
        配置完成的FastAPI实例
    """
    app = FastAPI(
        title="Skills Agent API",
        description="AI Agent 技能管理系统的 REST API",
        version="1.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router, prefix="/api/v1")

    @app.get("/")
    async def root():
        return {
            "service": "Skills Agent API",
            "version": "1.0.0",
            "docs": "/docs",
        }

    return app


app = create_app()


if __name__ == "__main__":
    uvicorn.run(
        "app.server:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
    )
