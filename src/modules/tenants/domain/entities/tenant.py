class Tenant:
    def __init__(
        self,
        id: int | None = None,
        name: str = "",
        slug: str = "",
        domain: str | None = None,
    ):
        self.id = id
        self.name = name
        self.slug = slug
        self.domain = domain
