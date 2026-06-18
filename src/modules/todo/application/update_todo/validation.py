from src.modules.todo.application.update_todo.command import UpdateTodoCommand


def validate_update_todo_command(command: UpdateTodoCommand) -> None:
    if (
        command.title is None
        and command.description is None
        and command.is_completed is None
    ):
        raise ValueError("At least one todo field must be provided")

    if command.title is not None and not command.title.strip():
        raise ValueError("Todo title is required")
