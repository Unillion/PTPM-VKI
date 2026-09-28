
import unittest

from validator import (
    validate_registration,
    mask_secret,
    _validate_login,
    _validate_password,
)


class TestMaskSecret(unittest.TestCase):

    def test_same_passwords_same_mask(self):
        self.assertEqual(mask_secret("Пароль1!"), mask_secret("Пароль1!"))

    def test_different_passwords_different_mask(self):
        self.assertNotEqual(mask_secret("Пароль1!"), mask_secret("Пароль2!"))

    def test_mask_hides_password(self):
        pwd = "СуперПароль9#"
        self.assertNotIn(pwd, mask_secret(pwd))

    def test_none_mask(self):
        self.assertEqual(mask_secret(None), "<None>")


class TestLoginValidation(unittest.TestCase):

    def test_valid_phone(self):
        self.assertIsNone(_validate_login("+7-123-456-7890"))

    def test_invalid_phone(self):
        self.assertIsNotNone(_validate_login("+7-12-456-7890"))
        self.assertIsNotNone(_validate_login("+71234567890"))

    def test_valid_email(self):
        self.assertIsNone(_validate_login("user@example.com"))

    def test_invalid_email(self):
        self.assertIsNotNone(_validate_login("user@@example.com"))
        self.assertIsNotNone(_validate_login("user@example"))

    def test_valid_string_login(self):
        self.assertIsNone(_validate_login("user_01"))

    def test_string_login_too_short(self):
        self.assertIsNotNone(_validate_login("usr1"))

    def test_string_login_invalid_chars(self):
        self.assertIsNotNone(_validate_login("юзер01"))

    def test_empty_login(self):
        self.assertIsNotNone(_validate_login(""))

    def test_blacklist(self):
        self.assertIsNotNone(_validate_login("admin"))
        self.assertIsNotNone(_validate_login("ADMIN"))
        self.assertIsNotNone(_validate_login("root"))


class TestPasswordValidation(unittest.TestCase):

    def test_valid_password(self):
        self.assertIsNone(_validate_password("Пароль1!"))

    def test_too_short(self):
        self.assertIsNotNone(_validate_password("П1!abc"))

    def test_no_uppercase(self):
        self.assertIsNotNone(_validate_password("пароль1!"))

    def test_no_lowercase(self):
        self.assertIsNotNone(_validate_password("ПАРОЛЬ1!"))

    def test_no_digit(self):
        self.assertIsNotNone(_validate_password("Пароль!"))

    def test_no_special(self):
        self.assertIsNotNone(_validate_password("Пароль1"))

    def test_latin_forbidden(self):
        self.assertIsNotNone(_validate_password("Password1!"))

    def test_space_forbidden(self):
        self.assertIsNotNone(_validate_password("Пароль 1!"))

    def test_empty(self):
        self.assertIsNotNone(_validate_password(""))


class TestRegistration(unittest.TestCase):

    def test_success(self):
        ok, msg = validate_registration("user_01", "Пароль1!", "Пароль1!")
        self.assertTrue(ok)
        self.assertEqual(msg, "")

    def test_success_email(self):
        ok, msg = validate_registration(
            "john@example.com", "Кириллица9#", "Кириллица9#"
        )
        self.assertTrue(ok)
        self.assertEqual(msg, "")

    def test_success_phone(self):
        ok, msg = validate_registration(
            "+7-123-456-7890", "Кириллица9#", "Кириллица9#"
        )
        self.assertTrue(ok)
        self.assertEqual(msg, "")

    def test_password_mismatch(self):
        ok, msg = validate_registration("user_01", "Пароль1!", "Пароль2!")
        self.assertFalse(ok)
        self.assertIn("не совпадают", msg.lower())

    def test_empty_confirm(self):
        ok, msg = validate_registration("user_01", "Пароль1!", "")
        self.assertFalse(ok)
        self.assertIn("подтверждение", msg.lower())

    def test_blacklisted_login(self):
        ok, msg = validate_registration("admin", "Пароль1!", "Пароль1!")
        self.assertFalse(ok)
        self.assertIn("чёрный список", msg.lower())


class TestAllErrorReasons(unittest.TestCase):

    def test_at_least_ten_distinct_reasons(self):
        cases = [
            ("", "Пароль1!", "Пароль1!"),               # пустой логин
            ("юзер", "Пароль1!", "Пароль1!"),           # не латиница
            ("admin", "Пароль1!", "Пароль1!"),          # чёрный список
            ("+7-1-2-3", "Пароль1!", "Пароль1!"),       # плохой телефон
            ("bad@@mail", "Пароль1!", "Пароль1!"),      # плохой email
            ("usr1", "Пароль1!", "Пароль1!"),           # короткий логин-строка
            ("user_01", "123", "123"),                  # короткий пароль
            ("user_02", "password1!", "password1!"),    # латиница
            ("user_03", "пароль1!", "пароль1!"),        # нет заглавной
            ("user_04", "ПАРОЛЬ1!", "ПАРОЛЬ1!"),        # нет строчной
            ("user_05", "Пароль!", "Пароль!"),          # нет цифры
            ("user_06", "Пароль1", "Пароль1"),          # нет спецсимвола
            ("user_07", "Пароль1!", "Другой1!"),        # не совпадают
            ("user_08", "Пароль1!", ""),                # пустое подтверждение
        ]
        reasons = set()
        for login, pwd, confirm in cases:
            ok, msg = validate_registration(login, pwd, confirm)
            self.assertFalse(ok, f"Ожидалась ошибка для {login!r}")
            reasons.add(msg)

        self.assertGreaterEqual(
            len(reasons), 10,
            f"Ожидалось >= 10 разных причин, получено {len(reasons)}: {reasons}"
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)