from __future__ import annotations

import string
import unittest

from securepass.exceptions import (
    AllClassesDisabledError,
    InvalidLengthError,
    LengthTooShortError,
)
from securepass.generator import (
    AMBIGUOUS_CHARACTERS,
    PasswordOptions,
    generate_multiple_passwords,
    generate_password,
)


class TestPasswordLengthCorrectness(unittest.TestCase):

    def test_output_matches_requested_length(self) -> None:
        for length in (4, 8, 16, 32, 64, 128):
            options = PasswordOptions(length=length)
            pwd = generate_password(options)
            self.assertEqual(len(pwd), length)

    def test_length_below_minimum_raises(self) -> None:
        with self.assertRaises(InvalidLengthError):
            generate_password(PasswordOptions(length=1))

    def test_length_above_maximum_raises(self) -> None:
        with self.assertRaises(InvalidLengthError):
            generate_password(PasswordOptions(length=999))


class TestAllClassesDisabled(unittest.TestCase):

    def test_all_classes_disabled_raises_clear_error(self) -> None:
        options = PasswordOptions(
            length=8,
            use_lowercase=False,
            use_uppercase=False,
            use_digits=False,
            use_symbols=False,
        )
        with self.assertRaises(AllClassesDisabledError):
            generate_password(options)


class TestGuaranteedClassRepresentation(unittest.TestCase):

    def test_every_enabled_class_present_across_many_runs(self) -> None:
        options = PasswordOptions(length=12)  # all four classes enabled
        for _ in range(200):
            pwd = generate_password(options)
            self.assertTrue(any(c in string.ascii_lowercase for c in pwd))
            self.assertTrue(any(c in string.ascii_uppercase for c in pwd))
            self.assertTrue(any(c in string.digits for c in pwd))
            self.assertTrue(any(c in string.punctuation for c in pwd))

    def test_guaranteed_characters_are_not_pinned_to_fixed_positions(self) -> None:

        options = PasswordOptions(length=20, use_digits=False, use_symbols=False)
        saw_uppercase_outside_first_two_slots = False
        for _ in range(100):
            pwd = generate_password(options)
            if not any(c in string.ascii_uppercase for c in pwd[:2]):
                saw_uppercase_outside_first_two_slots = True
                break
        self.assertTrue(saw_uppercase_outside_first_two_slots)


class TestTooShortForEnabledClasses(unittest.TestCase):
    """Section 3.7: 'the too-short-for-classes edge case'."""

    def test_length_too_short_for_enabled_classes_raises(self) -> None:

        options = PasswordOptions(length=3, min_length=1)  
        with self.assertRaises(LengthTooShortError):
            generate_password(options)

    def test_length_exactly_equal_to_class_count_succeeds(self) -> None:
        options = PasswordOptions(length=4, min_length=1) 
        pwd = generate_password(options)
        self.assertEqual(len(pwd), 4)


class TestExcludeAmbiguousCharacters(unittest.TestCase):
    def test_no_ambiguous_characters_appear_in_output(self) -> None:
        options = PasswordOptions(length=64, exclude_ambiguous=True)
        pwd = generate_password(options)
        for ambiguous_char in AMBIGUOUS_CHARACTERS:
            self.assertNotIn(ambiguous_char, pwd)


class TestSecureBackend(unittest.TestCase):
    """Section 3.6: working --secure / secrets-module code path."""

    def test_secure_flag_still_produces_a_valid_password(self) -> None:
        options = PasswordOptions(length=16, secure=True)
        pwd = generate_password(options)
        self.assertEqual(len(pwd), 16)
        self.assertTrue(any(c in string.ascii_lowercase for c in pwd))
        self.assertTrue(any(c in string.ascii_uppercase for c in pwd))
        self.assertTrue(any(c in string.digits for c in pwd))
        self.assertTrue(any(c in string.punctuation for c in pwd))


class TestBatchGeneration(unittest.TestCase):
    def test_generate_multiple_returns_requested_count(self) -> None:
        options = PasswordOptions(length=12)
        passwords = generate_multiple_passwords(5, options)
        self.assertEqual(len(passwords), 5)

        self.assertEqual(len(set(passwords)), 5)

    def test_generate_multiple_rejects_non_positive_count(self) -> None:
        options = PasswordOptions(length=12)
        with self.assertRaises(ValueError):
            generate_multiple_passwords(0, options)


if __name__ == "__main__":
    unittest.main()
