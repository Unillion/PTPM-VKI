
import logging
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from logger import setup_logging
from validator import (
    BLACKLIST,
    _validate_login,
    _validate_password,
    mask_secret,
    validate_registration,
)

VALID_PASSWORD = "Пароль1!"


def setUpModule():
    # Чтобы валидатор не засорял вывод тестов сообщениями об ошибках.
    logging.disable(logging.CRITICAL)


def tearDownModule():
    logging.disable(logging.NOTSET)


class TestMaskSecret(unittest.TestCase):

    def test_same_passwords_give_same_mask(self):
        self.assertEqual(mask_secret(VALID_PASSWORD), mask_secret(VALID_PASSWORD))

    def test_different_passwords_give_different_masks(self):
        self.assertNotEqual(mask_secret("Пароль1!"), mask_secret("Пароль2!"))

    def test_passwords_differing_only_by_case_give_different_masks(self):
        self.assertNotEqual(mask_secret("Пароль1!"), mask_secret("пароль1!"))

    def test_mask_does_not_contain_original_password(self):
        pwd = "СуперПароль9#"
        self.assertNotIn(pwd, mask_secret(pwd))

    def test_none_is_masked_as_none_marker(self):
        self.assertEqual(mask_secret(None), "<None>")

    def test_empty_string_is_masked_without_error(self):
        self.assertEqual(mask_secret(""), "<masked:e3b0c44298fc>")

    def test_mask_has_expected_format(self):
        mask = mask_secret(VALID_PASSWORD)
        self.assertTrue(mask.startswith("<masked:") and mask.endswith(">"))
        self.assertEqual(len(mask), len("<masked:") + 12 + 1)


class TestPhoneLogin(unittest.TestCase):

    def test_valid_phone_is_accepted(self):
        self.assertIsNone(_validate_login("+7-123-456-7890"))

    def test_phone_with_short_group_is_rejected(self):
        self.assertIsNotNone(_validate_login("+7-12-456-7890"))

    def test_phone_without_dashes_is_rejected(self):
        self.assertIsNotNone(_validate_login("+71234567890"))

    def test_phone_with_letters_is_rejected(self):
        self.assertIsNotNone(_validate_login("+7-abc-456-7890"))

    def test_phone_without_plus_is_not_treated_as_phone(self):
        # без "+" это уже "логин-строка", а дефисы в ней запрещены
        self.assertIsNotNone(_validate_login("7-123-456-7890"))

    def test_phone_with_non_ascii_digits_is_rejected(self):
        # арабско-индийские цифры не должны проходить как цифры телефона
        self.assertIsNotNone(_validate_login("+٧-١٢٣-٤٥٦-٧٨٩٠"))

    def test_phone_with_trailing_newline_is_rejected(self):
        self.assertIsNotNone(_validate_login("+7-123-456-7890\n"))

class TestEmailLogin(unittest.TestCase):

    def test_valid_email_is_accepted(self):
        self.assertIsNone(_validate_login("john.doe@example.com"))

    def test_email_with_plus_tag_is_accepted(self):
        self.assertIsNone(_validate_login("john+tag@example.co.uk"))

    def test_email_without_domain_zone_is_rejected(self):
        self.assertIsNotNone(_validate_login("user@example"))

    def test_email_with_double_at_is_rejected(self):
        self.assertIsNotNone(_validate_login("user@@example.com"))

    def test_email_with_empty_local_part_is_rejected(self):
        self.assertIsNotNone(_validate_login("@example.com"))

    def test_email_with_one_letter_zone_is_rejected(self):
        self.assertIsNotNone(_validate_login("user@example.c"))

    def test_email_with_consecutive_dots_in_domain_is_rejected(self):
        self.assertIsNotNone(_validate_login("user@example..com"))

    def test_email_with_consecutive_dots_in_local_part_is_rejected(self):
        self.assertIsNotNone(_validate_login("us..er@example.com"))

    def test_email_with_leading_dot_in_local_part_is_rejected(self):
        self.assertIsNotNone(_validate_login(".user@example.com"))

    def test_email_with_cyrillic_is_rejected(self):
        self.assertIsNotNone(_validate_login("юзер@example.com"))


class TestStringLogin(unittest.TestCase):

    def test_valid_string_login_is_accepted(self):
        self.assertIsNone(_validate_login("user_01"))

    def test_string_login_of_exactly_five_chars_is_accepted(self):
        self.assertIsNone(_validate_login("ab_12"))

    def test_string_login_of_four_chars_is_rejected(self):
        self.assertIsNotNone(_validate_login("usr1"))

    def test_string_login_with_cyrillic_is_rejected(self):
        self.assertIsNotNone(_validate_login("юзер01"))

    def test_string_login_with_space_is_rejected(self):
        self.assertIsNotNone(_validate_login("user 01"))

    def test_string_login_with_special_char_is_rejected(self):
        self.assertIsNotNone(_validate_login("user-01"))

    def test_string_login_with_trailing_newline_is_rejected(self):
        self.assertIsNotNone(_validate_login("user_01\n"))

    def test_string_login_of_254_chars_is_accepted(self):
        self.assertIsNone(_validate_login("a" * 254))

    def test_string_login_of_255_chars_is_rejected(self):
        self.assertIn("слишком длинный", _validate_login("a" * 255))

    def test_empty_login_is_rejected(self):
        self.assertIn("пустым", _validate_login(""))

    def test_none_login_is_rejected(self):
        self.assertIn("пустым", _validate_login(None))


class TestLoginBlacklist(unittest.TestCase):

    def test_blacklisted_login_is_rejected(self):
        self.assertIn("чёрный список", _validate_login("admin"))

    def test_blacklist_check_is_case_insensitive(self):
        self.assertIn("чёрный список", _validate_login("ADMIN"))

    def test_blacklisted_email_is_rejected(self):
        self.assertIn("чёрный список", _validate_login("Admin@Admin.com"))

    def test_blacklisted_phone_is_rejected(self):
        self.assertIn("чёрный список", _validate_login("+7-999-999-9999"))

    def test_every_blacklisted_login_is_rejected_by_some_rule(self):
        for login in BLACKLIST:
            with self.subTest(login=login):
                self.assertIsNotNone(_validate_login(login))

    def test_login_similar_to_blacklisted_is_accepted(self):
        self.assertIsNone(_validate_login("admin_2"))


class TestPassword(unittest.TestCase):

    def test_valid_password_is_accepted(self):
        self.assertIsNone(_validate_password(VALID_PASSWORD))

    def test_password_of_exactly_seven_chars_is_accepted(self):
        self.assertIsNone(_validate_password("Парол1!"))

    def test_password_of_six_chars_is_rejected(self):
        self.assertIn("7 символов", _validate_password("Паро1!"))

    def test_password_with_letter_yo_is_accepted(self):
        self.assertIsNone(_validate_password("Ёжик12!"))

    def test_password_without_uppercase_is_rejected(self):
        self.assertIn("заглавную", _validate_password("пароль1!"))

    def test_password_without_lowercase_is_rejected(self):
        self.assertIn("строчную", _validate_password("ПАРОЛЬ1!"))

    def test_password_without_digit_is_rejected(self):
        self.assertIn("цифру", _validate_password("Пароль!!"))

    def test_password_without_special_char_is_rejected(self):
        self.assertIn("спецсимвол", _validate_password("Пароль12"))

    def test_password_with_latin_letters_is_rejected(self):
        self.assertIn("только кириллицу", _validate_password("Password1!"))

    def test_password_with_space_is_rejected(self):
        self.assertIsNotNone(_validate_password("Пароль 1!"))

    def test_password_with_trailing_newline_is_rejected(self):
        self.assertIsNotNone(_validate_password("Пароль1!\n"))

    def test_empty_password_is_rejected(self):
        self.assertIn("пустым", _validate_password(""))

    def test_none_password_is_rejected(self):
        self.assertIn("пустым", _validate_password(None))

    def test_each_allowed_special_char_is_accepted(self):
        for ch in "!@#$%^&*()_-+=[]{};:'\",.<>/?\\|`~№":
            with self.subTest(special=ch):
                self.assertIsNone(_validate_password("Пароль1" + ch))

class TestRegistration(unittest.TestCase):

    def test_successful_registration_with_string_login(self):
        self.assertEqual(
            validate_registration("user_01", VALID_PASSWORD, VALID_PASSWORD), (True, "")
        )

    def test_successful_registration_with_email(self):
        self.assertEqual(
            validate_registration("john@example.com", "Кириллица9#", "Кириллица9#"),
            (True, ""),
        )

    def test_successful_registration_with_phone(self):
        self.assertEqual(
            validate_registration("+7-123-456-7890", "Кириллица9#", "Кириллица9#"),
            (True, ""),
        )

    def test_result_is_tuple_of_bool_and_str(self):
        result = validate_registration("user_01", VALID_PASSWORD, VALID_PASSWORD)
        self.assertIsInstance(result, tuple)
        self.assertIsInstance(result[0], bool)
        self.assertIsInstance(result[1], str)

    def test_password_mismatch_is_reported(self):
        ok, msg = validate_registration("user_01", "Пароль1!", "Пароль2!")
        self.assertFalse(ok)
        self.assertIn("не совпадают", msg)

    def test_confirmation_differing_only_by_case_is_mismatch(self):
        ok, msg = validate_registration("user_01", "Пароль1!", "пароль1!")
        self.assertFalse(ok)
        self.assertIn("не совпадают", msg)

    def test_empty_confirmation_is_reported(self):
        ok, msg = validate_registration("user_01", VALID_PASSWORD, "")
        self.assertFalse(ok)
        self.assertIn("Подтверждение", msg)

    def test_none_confirmation_is_reported(self):
        ok, msg = validate_registration("user_01", VALID_PASSWORD, None)
        self.assertFalse(ok)
        self.assertIn("Подтверждение", msg)

    def test_blacklisted_login_blocks_registration(self):
        ok, msg = validate_registration("admin", VALID_PASSWORD, VALID_PASSWORD)
        self.assertFalse(ok)
        self.assertIn("чёрный список", msg)

    def test_login_error_has_priority_over_password_error(self):
        ok, msg = validate_registration("", "123", "456")
        self.assertFalse(ok)
        self.assertIn("Логин", msg)

    def test_password_error_has_priority_over_mismatch(self):
        ok, msg = validate_registration("user_01", "123", "456")
        self.assertFalse(ok)
        self.assertIn("7 символов", msg)

    def test_non_string_login_returns_internal_error_instead_of_crash(self):
        ok, msg = validate_registration(12345, VALID_PASSWORD, VALID_PASSWORD)
        self.assertFalse(ok)
        self.assertIn("Внутренняя ошибка", msg)

    def test_at_least_ten_distinct_error_reasons(self):
        cases = [
            ("", VALID_PASSWORD, VALID_PASSWORD),
            ("юзер", VALID_PASSWORD, VALID_PASSWORD),
            ("admin", VALID_PASSWORD, VALID_PASSWORD),
            ("+7-1-2-3", VALID_PASSWORD, VALID_PASSWORD),
            ("bad@@mail", VALID_PASSWORD, VALID_PASSWORD),
            ("user_01", "123", "123"),
            ("user_02", "password1!", "password1!"),
            ("user_03", "пароль1!", "пароль1!"),
            ("user_04", "ПАРОЛЬ1!", "ПАРОЛЬ1!"),
            ("user_05", "Пароль!!", "Пароль!!"),
            ("user_06", "Пароль12", "Пароль12"),
            ("user_07", VALID_PASSWORD, "Другой1!"),
            ("user_08", VALID_PASSWORD, "")
        ]
        reasons = set()
        for login, pwd, confirm in cases:
            ok, msg = validate_registration(login, pwd, confirm)
            self.assertFalse(ok, f"Ожидалась ошибка для {login!r}")
            reasons.add(msg)
        self.assertGreaterEqual(len(reasons), 10, f"Причин: {len(reasons)}")

class TestLogging(unittest.TestCase):

    def setUp(self):
        logging.disable(logging.NOTSET)  # в этом классе логи нужны
        self.root = logging.getLogger()
        self._old_handlers = list(self.root.handlers)
        self._old_level = self.root.level
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        for handler in list(self.root.handlers):
            if handler not in self._old_handlers:
                self.root.removeHandler(handler)
                handler.close()
        for handler in self._old_handlers:
            if handler not in self.root.handlers:
                self.root.addHandler(handler)
        self.root.setLevel(self._old_level)
        self.tmp.cleanup()
        logging.disable(logging.CRITICAL)

    def _read_log(self) -> str:
        for handler in self.root.handlers:
            handler.flush()
        with open(os.path.join(self.tmp.name, "file_txt.log"), encoding="utf-8") as f:
            return f.read()

    def test_setup_logging_creates_log_file(self):
        setup_logging(log_dir=self.tmp.name)
        self.assertTrue(os.path.isfile(os.path.join(self.tmp.name, "file_txt.log")))

    def test_setup_logging_creates_missing_log_directory(self):
        target = os.path.join(self.tmp.name, "nested", "logs")
        setup_logging(log_dir=target)
        self.assertTrue(os.path.isdir(target))

    def test_setup_logging_adds_console_and_file_handlers(self):
        setup_logging(log_dir=self.tmp.name)
        kinds = {type(h) for h in self.root.handlers}
        self.assertIn(logging.StreamHandler, kinds)
        self.assertIn(logging.FileHandler, kinds)

    def test_setup_logging_allows_info_messages(self):
        setup_logging(log_dir=self.tmp.name)
        self.assertTrue(self.root.isEnabledFor(logging.INFO))

    def test_repeated_setup_does_not_duplicate_handlers(self):
        setup_logging(log_dir=self.tmp.name)
        first = len(self.root.handlers)
        setup_logging(log_dir=self.tmp.name)
        self.assertEqual(len(self.root.handlers), first)

    def test_repeated_setup_closes_previous_file_handler(self):
        setup_logging(log_dir=self.tmp.name)
        old_file_handler = next(
            h for h in self.root.handlers if isinstance(h, logging.FileHandler)
        )
        setup_logging(log_dir=self.tmp.name)
        self.assertIsNone(old_file_handler.stream)  # None => файл закрыт

    def test_successful_registration_is_written_to_log_file(self):
        setup_logging(log_dir=self.tmp.name)
        validate_registration("user_01", VALID_PASSWORD, VALID_PASSWORD)
        self.assertIn("Успешная валидация регистрации", self._read_log())

    def test_failed_registration_is_written_to_log_file(self):
        setup_logging(log_dir=self.tmp.name)
        validate_registration("admin", VALID_PASSWORD, VALID_PASSWORD)
        self.assertIn("чёрный список", self._read_log())

    def test_log_does_not_contain_plain_password(self):
        setup_logging(log_dir=self.tmp.name)
        validate_registration("user_01", "Пароль1!", "Пароль2!")
        validate_registration("user_02", VALID_PASSWORD, VALID_PASSWORD)
        self.assertNotIn("Пароль1!", self._read_log())
        self.assertNotIn("Пароль2!", self._read_log())

    def test_log_line_contains_date_and_level(self):
        setup_logging(log_dir=self.tmp.name)
        validate_registration("admin", VALID_PASSWORD, VALID_PASSWORD)
        line = self._read_log().splitlines()[0]
        self.assertRegex(line, r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} \| \[[A-Z ]{7}\] \|")

    def test_validation_error_is_logged_with_error_level(self):
        with self.assertLogs(level="ERROR") as captured:
            validate_registration("admin", VALID_PASSWORD, VALID_PASSWORD)
        self.assertTrue(any("чёрный список" in m for m in captured.output))

    def test_unexpected_exception_is_logged_with_traceback(self):
        with self.assertLogs(level="ERROR") as captured:
            validate_registration(12345, VALID_PASSWORD, VALID_PASSWORD)
        self.assertTrue(any(r.exc_info for r in captured.records))


if __name__ == "__main__":
    unittest.main(verbosity=2)
