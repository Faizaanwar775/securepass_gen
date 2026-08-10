# SecurePass Gen

A terminal-based password generator built entirely on the Python standard
library — no third-party dependencies required to run it.

Built for the **Khizex Python Engineering Internship — Week 6 Build
Challenge**.

---

## 1. Project Structure

```
securepass_gen/
├── securepass/              # Installable package
│   ├── __init__.py
│   ├── generator.py         # Pure generation logic — NO I/O, fully unit-testable
│   ├── cli.py                # argparse CLI: parsing, printing, file writing, logging
│   └── exceptions.py         # Custom exception hierarchy
├── tests/
│   ├── __init__.py
│   └── test_generator.py     # Automated tests (unittest / pytest compatible)
├── docs/
│   └── example_transcript.txt  # Real captured terminal output (see Section 6)
├── setup.py                  # Packaging + console_scripts entry point
├── requirements.txt           # stdlib-only at runtime; pytest optional for dev
├── LICENSE
├── .gitignore
└── README.md                  # You are here
```

The generation logic (`generator.py`) never calls `print`, `input`, or
touches the filesystem. Everything user-facing — argument parsing, printing
to the terminal, writing output files, logging — lives in `cli.py`. This
separation is what makes the core logic independently unit-testable and is
required by Section 3.7 of the assignment brief.

---

## 2. Installation

Requires **Python 3.10+**. No third-party packages are needed to run the
program.

```bash
# Clone / unzip the project, then from the project root:
cd securepass_gen

# Option A — install as a CLI command (recommended)
pip install -e .
securepass-gen --help

# Option B — run directly without installing
python3 -m securepass.cli --help
```

If you want to run the test suite with `pytest` instead of the built-in
`unittest` runner, install the (optional) dev dependency:

```bash
pip install -r requirements.txt
```

---

## 3. Usage

```
usage: securepass-gen [-h] [-l LENGTH] [--no-lowercase] [--no-uppercase]
                       [--no-digits] [--no-symbols] [--exclude-ambiguous]
                       [--count COUNT] [--output FILE] [--secure] [-v]
```

| Flag | Default | Description |
|---|---|---|
| `-l, --length` | `16` | Password length (must be between 4 and 128). |
| `--no-lowercase` | included | Exclude lowercase letters (a-z). |
| `--no-uppercase` | included | Exclude uppercase letters (A-Z). |
| `--no-digits` | included | Exclude digits (0-9). |
| `--no-symbols` | included | Exclude punctuation/symbols. |
| `--exclude-ambiguous` | off | Exclude visually ambiguous characters (`0`, `O`, `1`, `l`, `I`). |
| `--count N` | `1` | Generate N passwords, printed as a numbered list. |
| `--output FILE` | none | Also save the generated password(s) to FILE. |
| `--secure` | off | Use the `secrets` CSPRNG module instead of `random` (see Section 5). |
| `-v, --verbose` | off | Debug logging to stderr (passwords themselves are **never** logged). |

### Examples

```bash
# Simple 16-character password using all four default classes
securepass-gen

# 20-character password, no symbols, no ambiguous characters
securepass-gen -l 20 --no-symbols --exclude-ambiguous

# Five cryptographically-secure 24-character passwords
securepass-gen -l 24 --count 5 --secure

# Save output to a file as well as printing it
securepass-gen -l 16 --output passwords.txt
```

All four character classes (lowercase, uppercase, digits, symbols) are
**on by default**, satisfying the assignment's minimum-bar requirement
(Section 3.1) while still letting every class be individually disabled
(Section 3.2).

---

## 4. Approach to Guaranteed Character-Class Representation

(Assignment Section 3.3)

Naively picking every character with `random.choice(combined_pool)` can, by
chance, produce a password with zero digits even though digits were
enabled. `generate_password()` in `securepass/generator.py` avoids this in
three steps:

1. **Guarantee first.** Draw exactly one character from *each enabled
   class* — one guaranteed lowercase char, one guaranteed digit, etc.
2. **Fill the rest.** Draw the remaining `length - num_classes` characters
   from the *combined* pool of all enabled classes (a class can "win" the
   filler draw again — that's fine, it doesn't reduce anyone else's
   guarantee).
3. **Shuffle.** The full list (guaranteed + filler) is shuffled in place
   before being joined into the final string, so the guaranteed characters
   don't predictably land in the first few positions (e.g. always
   `[lower][upper][digit][symbol][...random...]`).

This is covered by `TestGuaranteedClassRepresentation` in
`tests/test_generator.py`, which runs 200 generations to confirm every
enabled class actually appears, plus a second test confirming the
guaranteed characters aren't pinned to fixed positions.

---

## 5. Security Awareness (Assignment Section 3.6)

### Why `random` is not cryptographically secure

Python's `random` module is built on the **Mersenne Twister**, a
deterministic pseudo-random number generator (PRNG). "Deterministic" is the
key word: its entire future output sequence is completely determined by its
internal state (a 624-word integer array), which is itself seeded from a
predictable source (system time, by default, if no seed is given).

Two properties make it unsafe for anything security-sensitive:

- **State recovery from output.** Mersenne Twister's state can be
  fully reconstructed by observing a relatively small number of its
  outputs (624 consecutive 32-bit outputs is the commonly cited figure).
  Once an attacker has the state, every past and future "random" value the
  generator will ever produce is fully predictable — including other
  passwords generated in the same process.
- **Predictable/low-entropy seeding.** If the generator is seeded from
  something guessable (like the current time, which `random` does
  automatically if you don't seed it yourself), an attacker can brute-force
  the seed space directly, without even needing to observe outputs first.

Neither property matters for simulations, games, or shuffling a playlist.
Both matter enormously for something like a password generator, where the
entire point is that an adversary *cannot* guess or reconstruct the output.

### What `secrets` does differently

The `secrets` module (and `random.SystemRandom`, which it's built on top
of) does not use Mersenne Twister at all. It pulls randomness directly from
the operating system's cryptographically secure source —
`os.urandom()`, which on Linux/macOS draws from the kernel's CSPRNG
(`/dev/urandom` / `getrandom()`) and on Windows uses
`CryptGenRandom`/`BCryptGenRandom`. These sources are specifically
engineered so that:

- Output is **not** derived from a small, recoverable internal state the
  way Mersenne Twister's is.
- Observing any amount of past output gives **no practical advantage** in
  predicting future output.

This is why `secrets` is the module the Python documentation itself
recommends for generating tokens, password-reset links, API keys, and — as
here — passwords.

### The `--secure` flag

Passing `--secure` switches the generator's random back-end from
`random.choice` / `random.shuffle` to `secrets.SystemRandom().choice` /
`secrets.SystemRandom().shuffle` (see `_get_backend()` in
`generator.py`). The class-guarantee and shuffle algorithm is otherwise
identical — only the source of randomness changes. `--secure` is not the
default (to match the assignment brief exactly, which specifies `random`
as the default mechanic and `secrets` as a documented bonus path), but it
is fully working, tested (`TestSecureBackend`), and is what should be used
for any password you would actually rely on.

### What this tool does *not* do

To be transparent about the limits of this generator:

- It does **not** check the generated password against any breached- or
  common-password list (e.g. `rockyou.txt`, Have I Been Pwned's range
  API). A password can satisfy every length/character-class rule here and
  still be a bad password if a near-identical string appears in a breach
  corpus.
- Password strength in the real world depends on more than length and
  character variety — avoiding predictable patterns, not reusing
  passwords across sites, and using a password manager all matter at least
  as much. This tool solves the "generate a long, random string" problem;
  it is one ingredient in good password hygiene, not the whole recipe.

---

## 6. Deliverables Checklist

| Deliverable | Where |
|---|---|
| Modular source (generator separated from CLI) | `securepass/generator.py`, `securepass/cli.py` |
| README: usage, class-guarantee approach, security write-up | This file, Sections 3–5 |
| Terminal transcript (default run, custom flags, batch, too-short error) | `docs/example_transcript.txt` — captured from real, actually-executed runs, not hand-written |
| Automated tests, single documented run command | `tests/test_generator.py`; run via `python -m unittest discover -s tests -v` or `pytest` |

### A note on the "too-short-for-classes" scenario

The assignment's minimum-length requirement (Section 3.4, "e.g. 4") and its
maximum-class-count (there are exactly four classes: lowercase, uppercase,
digits, symbols) happen to be the same number in this implementation's
defaults. That means via the CLI's default `--length` floor of 4, the
"length too short to fit one char per enabled class" case can never
actually be reached with all four classes on — the minimum-length check
already guarantees enough room.

The logic itself is real, independent, and fully tested — it's exercised
directly against the pure `generate_password()` function (bypassing only
the CLI's minimum-length floor, via `PasswordOptions(min_length=...)`) in
both `tests/test_generator.py::TestTooShortForEnabledClasses` and in
`docs/example_transcript.txt`. It would fire immediately if, say, a future
version added a 5th character class, or if a maintainer ever lowered
`DEFAULT_MIN_LENGTH` below 4.

---

## 7. Running the Tests

```bash
# Using the standard library (no install needed)
python -m unittest discover -s tests -v

# Or, if you installed the optional dev dependency
pytest tests/ -v
```

Both commands run the same 12 tests, covering:

- Output length correctness across a range of lengths.
- Length validation (below minimum, above maximum).
- All-classes-disabled → clear error, no crash.
- Guaranteed class representation (200-iteration check) and non-fixed
  shuffled positions.
- Too-short-for-enabled-classes edge case.
- Ambiguous-character exclusion.
- The `--secure` / `secrets`-backed code path.
- Batch generation (`--count`) correctness and uniqueness.

---

## 8. Design Notes

- **Type hints everywhere.** Every function signature in `generator.py`
  and `cli.py` is fully typed.
- **No bare `except:`.** The only exception handling is a targeted
  `except OSError` around file writes and a targeted
  `except SecurePassGenError` in the CLI — genuinely unexpected exceptions
  are left to propagate rather than being silently swallowed.
- **Non-numeric / missing length.** Handled natively by `argparse`'s
  `type=int` — invalid input produces a clean usage message and exits with
  code `2`, never a raw Python traceback.
- **Logging.** `cli.py` configures the standard `logging` module; `-v`
  raises the level to `DEBUG`. Only metadata (argument values, password
  *count* and *length*, which backend was used) is ever logged — the
  generated password strings themselves are never written to a log.
- **Character pools from `string`.** All alphabets come from
  `string.ascii_lowercase`, `string.ascii_uppercase`, `string.digits`, and
  `string.punctuation` — no hardcoded character-set literals.
