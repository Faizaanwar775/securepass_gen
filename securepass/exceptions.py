from __future__ import annotations


class SecurePassGenError(Exception):
    """Base class for all SecurePass Gen errors.

    Catching this single type in the CLI is enough to guarantee that any
    *expected* failure (bad length, no classes enabled, etc.) is reported
    cleanly. Truly unexpected exceptions are intentionally left to propagate
    so they are never silently swallowed.
    """


class InvalidLengthError(SecurePassGenError):
    """Raised when the requested password length is out of the allowed range."""


class AllClassesDisabledError(SecurePassGenError):
    """Raised when every character class (lowercase/uppercase/digits/symbols)
    has been disabled, which would otherwise produce a blank password."""


class LengthTooShortError(SecurePassGenError):
    """Raised when the requested length is smaller than the number of enabled
    character classes, making it impossible to guarantee one character from
    every class."""
