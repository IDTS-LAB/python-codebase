import asyncio

from src.core.seed.runner import run_seeders


async def main() -> None:
    result = await run_seeders()
    authorization = result.authorization
    print(
        "[seed:authorization] "
        f"resources_created={authorization.resources_created} "
        f"roles_created={authorization.roles_created} "
        f"permissions_created={authorization.permissions_created} "
        f"role_permissions_created={authorization.role_permissions_created} "
        f"policies_created={authorization.policies_created}"
    )
    user = result.user
    print(
        "[seed:user] "
        f"users_created={user.users_created} "
        f"roles_assigned={user.roles_assigned}"
    )


if __name__ == "__main__":
    asyncio.run(main())
