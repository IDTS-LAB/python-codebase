from abc import ABC


class ModuleFacade(ABC):
    """Public contract a module exposes for cross-module communication.

    Other modules depend only on a module's facade — never on its
    application, domain, or infrastructure internals.
    """
