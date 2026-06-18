from src.modules.user.application.detail_user.query import DetailUserQuery


def validate_detail_user_query(query: DetailUserQuery) -> None:
    if query.user_id is None:
        raise ValueError("User id is required")
