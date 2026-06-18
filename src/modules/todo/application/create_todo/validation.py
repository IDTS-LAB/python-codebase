from src.modules.todo.application.create_todo.command import CreateTodoCommand


def validate_create_todo_command(command: CreateTodoCommand) -> None:
    if not command.title.strip():
        raise ValueError("Todo title is required")
