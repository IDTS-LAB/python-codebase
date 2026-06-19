from dataclasses import dataclass


@dataclass(frozen=True)
class AuthorizationResourceDefinition:
    key: str
    name: str
    description: str


DEFAULT_RESOURCES = (
    AuthorizationResourceDefinition(
        key="todo",
        name="Todo",
        description="Todo task resources",
    ),
    AuthorizationResourceDefinition(
        key="user",
        name="User",
        description="User account resources",
    ),
    AuthorizationResourceDefinition(
        key="role",
        name="Role",
        description="Authorization role resources",
    ),
    AuthorizationResourceDefinition(
        key="permission",
        name="Permission",
        description="Authorization permission resources",
    ),
)

DEFAULT_RESOURCE_KEYS = {resource.key: resource.key for resource in DEFAULT_RESOURCES}

TODO_RESOURCE = DEFAULT_RESOURCE_KEYS["todo"]
USER_RESOURCE = DEFAULT_RESOURCE_KEYS["user"]
ROLE_RESOURCE = DEFAULT_RESOURCE_KEYS["role"]
PERMISSION_RESOURCE = DEFAULT_RESOURCE_KEYS["permission"]

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
