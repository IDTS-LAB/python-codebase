from src.modules.todo.application.list_todo.query import GetTodosQuery


def validate_get_todos_query(query: GetTodosQuery) -> None:
    if query.user_id is None:
        raise ValueError("User id is required")
