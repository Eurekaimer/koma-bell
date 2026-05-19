class KomaBellError(Exception):
    """Base exception for expected application errors."""


class ConfigError(KomaBellError):
    """Configuration is missing or invalid."""


class StateError(KomaBellError):
    """State storage could not be read or written."""


class SourceError(KomaBellError):
    """A source adapter failed."""


class AuthError(SourceError):
    """Authentication failed."""


class NotifyError(KomaBellError):
    """Notification delivery failed."""
