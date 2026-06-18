TODO_RESOURCE = "todo"
USER_RESOURCE = "user"
ROLE_RESOURCE = "role"
PERMISSION_RESOURCE = "permission"

CREATE_ACTION = "create"
READ_ACTION = "read"
UPDATE_ACTION = "update"
DELETE_ACTION = "delete"
ME_ACTION = "me"

DEFAULT_USER_ROLE = "user"
ADMIN_ROLE = "admin"


def permission_key(resource: str, action: str) -> str:
    return f"{resource}:{action}"


DEFAULT_POLICIES = (
    ("p", ADMIN_ROLE, "*"),
    ("p", DEFAULT_USER_ROLE, permission_key(TODO_RESOURCE, CREATE_ACTION)),
    ("p", DEFAULT_USER_ROLE, permission_key(TODO_RESOURCE, READ_ACTION)),
    ("p", DEFAULT_USER_ROLE, permission_key(TODO_RESOURCE, UPDATE_ACTION)),
    ("p", DEFAULT_USER_ROLE, permission_key(TODO_RESOURCE, DELETE_ACTION)),
    ("p", DEFAULT_USER_ROLE, permission_key(USER_RESOURCE, ME_ACTION)),
)
