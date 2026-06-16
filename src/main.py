from fastapi import FastAPI

from src.core import lifespan
from src.modules.todo.presentation.routers.todo_router import router as todo_router
from src.modules.user.presentation.routers.user_router import router as user_router

app = FastAPI(
    title="Todo Modulith API", 
    version="1.0.0", 
    lifespan=lifespan.lifespan,
)

# Include Module Routers
app.include_router(user_router)
app.include_router(todo_router)


@app.get("/health")
def health_check():
    return {"status": "healthy"}
