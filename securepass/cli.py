from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import List, Optional

from securepass.exceptions import SecurePassGenError
from securepass.generator import (
    DEFAULT_MAX_LENGTH,
    DEFAULT_MIN_LENGTH,
    PasswordOptions,
    generate_multiple_passwords,
)

logger = logging.getLogger("securepass")


def _configure_logging(verbose: bool) -> None:
  
    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def build_parser() -> argparse.ArgumentParser:
    
    parser = argparse.ArgumentParser(
        prog="securepass-gen",
        description=(
            "SecurePass Gen -- a terminal-based password generator built "
            "entirely on the Python standard library."
        ),
        epilog=(
            "Examples:\n"
            "  securepass-gen -l 16\n"
            "  securepass-gen -l 20 --no-symbols --exclude-ambiguous\n"
            "  securepass-gen -l 24 --count 5 --secure\n"
            "  securepass-gen -l 16 --output passwords.txt\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "-l", "--length",
        type=int,
        default=16,
        help="Password length, %(default)s by default "
             f"(must be between {DEFAULT_MIN_LENGTH} and {DEFAULT_MAX_LENGTH}).",
    )
    parser.add_argument(
        "--no-lowercase", dest="use_lowercase", action="store_false",
        default=True,
        help="Exclude lowercase letters (a-z). Included by default.",
    )
    parser.add_argument(
        "--no-uppercase", dest="use_uppercase", action="store_false",
        default=True,
        help="Exclude uppercase letters (A-Z). Included by default.",
    )
    parser.add_argument(
        "--no-digits", dest="use_digits", action="store_false",
        default=True,
        help="Exclude digits (0-9). Included by default.",
    )
    parser.add_argument(
        "--no-symbols", dest="use_symbols", action="store_false",
        default=True,
        help="Exclude punctuation/symbols. Included by default.",
    )
    parser.add_argument(
        "--exclude-ambiguous",
        action="store_true", default=False,
        help="Exclude visually ambiguous characters (0/O, 1/l/I).",
    )
    parser.add_argument(
        "--count", type=int, default=1,
        help="Number of passwords to generate, %(default)s by default.",
    )
    parser.add_argument(
        "--output", type=str, default=None, metavar="FILE",
        help="Save generated password(s) to FILE, in addition to printing them.",
    )
    parser.add_argument(
        "--secure",
        action="store_true", default=False,
        help=(
            "Use the 'secrets' CSPRNG module instead of 'random' for "
            "character selection and shuffling. Recommended for any "
            "password you will actually use -- see README for why."
        ),
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true", default=False,
        help="Enable debug logging to stderr (generated passwords are never logged).",
    )
    return parser


def _fail(message: str, exit_code: int = 1) -> "NoReturn":  # type: ignore[name-defined]

    print(f"Error: {message}", file=sys.stderr)
    logger.debug("Exiting with code %s due to: %s", exit_code, message)
    sys.exit(exit_code)


def _write_output_file(path: str, passwords: List[str]) -> None:
    try:
        Path(path).write_text("\n".join(passwords) + "\n", encoding="utf-8")
    except OSError as exc:
        _fail(f"Could not write to output file '{path}': {exc}")


def main(argv: Optional[List[str]] = None) -> None:
   
    parser = build_parser()
    args = parser.parse_args(argv)

    _configure_logging(args.verbose)
    logger.debug("Parsed arguments: %s", vars(args))

    if args.count < 1:
        _fail(f"--count must be a positive integer (got {args.count}).")

    options = PasswordOptions(
        length=args.length,
        use_lowercase=args.use_lowercase,
        use_uppercase=args.use_uppercase,
        use_digits=args.use_digits,
        use_symbols=args.use_symbols,
        exclude_ambiguous=args.exclude_ambiguous,
        secure=args.secure,
    )

    try:
        passwords = generate_multiple_passwords(args.count, options)
    except SecurePassGenError as exc:
        _fail(str(exc))
        return  

    backend_label = "secrets (CSPRNG)" if args.secure else "random (PRNG)"
    logger.debug(
        "Generated %d password(s) length=%d backend=%s",
        len(passwords), args.length, backend_label,
    )

    if len(passwords) == 1:
        print(passwords[0])
    else:
        width = len(str(len(passwords)))
        for idx, pwd in enumerate(passwords, start=1):
            print(f"{idx:>{width}}. {pwd}")

    if args.output:
        _write_output_file(args.output, passwords)
        print(f"\nSaved {len(passwords)} password(s) to {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
