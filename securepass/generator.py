from __future__ import annotations

import random
import secrets
import string
from dataclasses import dataclass
from typing import Callable, Dict, List, Tuple

from securepass.exceptions import (
    AllClassesDisabledError,
    InvalidLengthError,
    LengthTooShortError,
)

DEFAULT_MIN_LENGTH = 4
DEFAULT_MAX_LENGTH = 128

AMBIGUOUS_CHARACTERS = "0O1lI"

_CHARACTER_CLASSES: Dict[str, str] = {
    "lowercase": string.ascii_lowercase,
    "uppercase": string.ascii_uppercase,
    "digits": string.digits,
    "symbols": string.punctuation,
}


@dataclass
class PasswordOptions:
    
    length: int
    use_lowercase: bool = True
    use_uppercase: bool = True
    use_digits: bool = True
    use_symbols: bool = True
    exclude_ambiguous: bool = False
    secure: bool = False
    min_length: int = DEFAULT_MIN_LENGTH
    max_length: int = DEFAULT_MAX_LENGTH


def _build_character_pools(options: PasswordOptions) -> Dict[str, str]:
    
    wanted = {
        "lowercase": options.use_lowercase,
        "uppercase": options.use_uppercase,
        "digits": options.use_digits,
        "symbols": options.use_symbols,
    }

    pools: Dict[str, str] = {}
    for name, enabled in wanted.items():
        if not enabled:
            continue
        alphabet = _CHARACTER_CLASSES[name]
        if options.exclude_ambiguous:
            alphabet = "".join(ch for ch in alphabet if ch not in AMBIGUOUS_CHARACTERS)
        if alphabet:
            pools[name] = alphabet
    return pools


def _get_backend(secure: bool) -> Tuple[Callable[[str], str], Callable[[List[str]], None]]:

    if secure:
        rng = secrets.SystemRandom()
        return rng.choice, rng.shuffle
    return random.choice, random.shuffle


def generate_password(options: PasswordOptions) -> str:
 
    if options.length < options.min_length or options.length > options.max_length:
        raise InvalidLengthError(
            f"Length must be between {options.min_length} and "
            f"{options.max_length} (got {options.length})."
        )

    pools = _build_character_pools(options)
    if not pools:
        raise AllClassesDisabledError(
            "All character classes are disabled -- enable at least one of "
            "lowercase, uppercase, digits, or symbols."
        )

    if options.length < len(pools):
        raise LengthTooShortError(
            f"Requested length {options.length} is too short to include at "
            f"least one character from each of the {len(pools)} enabled "
            f"class(es) ({', '.join(sorted(pools))}). Minimum required "
            f"length is {len(pools)}."
        )

    choice_fn, shuffle_fn = _get_backend(options.secure)

    guaranteed: List[str] = [choice_fn(alphabet) for alphabet in pools.values()]

    combined_pool = "".join(pools.values())
    filler_count = options.length - len(guaranteed)
    filler: List[str] = [choice_fn(combined_pool) for _ in range(filler_count)]

    password_chars = guaranteed + filler
    shuffle_fn(password_chars)

    return "".join(password_chars)


def generate_multiple_passwords(count: int, options: PasswordOptions) -> List[str]:
    
    if count < 1:
        raise ValueError(f"count must be a positive integer (got {count}).")
    return [generate_password(options) for _ in range(count)]
