from fastapi import FastAPI

from core import lifespan
from modules.todo.presentation.routers import todo_router
from modules.user.presentation.routers import user_router

app = FastAPI(title="Todo Modulith API", version="1.0.0", lifespan=lifespan)

# Include Module Routers
app.include_router(user_router)
app.include_router(todo_router)


@app.get("/health")
def health_check():
    return {"status": "healthy"}
