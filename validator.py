import hashlib
import logging
import re
import traceback

BLACKLIST = {
    "admin",
    "administrator",
    "root",
    "superuser",
    "user",
    "test",
    "guest",
    "support",
    "moderator",
    "system",
    "mail@mail.ru",
    "admin@admin.com",
    "+7-999-999-9999",
}

PHONE_RE = re.compile(r"^\+\d-\d{3}-\d{3}-\d{4}$")
EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
STRING_LOGIN_RE = re.compile(r"^[A-Za-z0-9_]{5,}$")
PASSWORD_ALLOWED_RE = re.compile(r"^[А-Яа-яЁё0-9!@#$%^&*()_\-+=\[\]{};:'\",.<>/?\\|`~№]+$")

def mask_secret(secret: str) -> str:
    if secret is None:
        return "<None>"
    digest = hashlib.sha256(secret.encode("utf-8")).hexdigest()
    return f"<masked:{digest[:12]}>"

def _validate_login(login: str) -> str | None:
    if login is None or login == "":
        return "Логин не может быть пустым"

    if len(login) > 254:
        return "Логин слишком длинный (более 254 символов)"

    if login.startswith("+"):
        if not PHONE_RE.match(login):
            return "Неверный формат телефона. Ожидается +x-xxx-xxx-xxxx"
    elif "@" in login:
        if not EMAIL_RE.match(login):
            return "Неверный формат email"
    else:
        if not STRING_LOGIN_RE.match(login):
            return ("Логин-строка должен содержать минимум 5 символов "
                    "и состоять только из латиницы, цифр и знака подчёркивания")

    if login.lower() in BLACKLIST:
        return "Логин входит в чёрный список запрещённых"

    return None


def _validate_password(password: str) -> str | None:
    if password is None or password == "":
        return "Пароль не может быть пустым"

    if len(password) < 7:
        return "Пароль должен содержать минимум 7 символов"

    if not PASSWORD_ALLOWED_RE.match(password):
        return "Пароль может содержать только кириллицу, цифры и спецсимволы"

    if not re.search(r"[А-ЯЁ]", password):
        return "Пароль должен содержать минимум одну заглавную букву"

    if not re.search(r"[а-яё]", password):
        return "Пароль должен содержать минимум одну строчную букву"

    if not re.search(r"\d", password):
        return "Пароль должен содержать минимум одну цифру"

    if not re.search(r"[^А-Яа-яЁё0-9]", password):
        return "Пароль должен содержать минимум один спецсимвол"

    return None

def validate_registration(login: str, password: str, confirm: str) -> tuple[bool, str]:
    masked_password = mask_secret(password)
    masked_confirm = mask_secret(confirm)

    params_repr = (
        f"login={login!r}, "
        f"password={masked_password}, "
        f"confirm={masked_confirm}"
    )

    logging.info("Запрос на регистрацию: %s", params_repr)

    try:
        err = _validate_login(login)
        if err:
            logging.error("Ошибка валидации логина: %s | %s", err, params_repr)
            return False, err

        err = _validate_password(password)
        if err:
            logging.error("Ошибка валидации пароля: %s | %s", err, params_repr)
            return False, err

        if confirm is None or confirm == "":
            msg = "Подтверждение пароля не может быть пустым"
            logging.error("%s | %s", msg, params_repr)
            return False, msg

        if password != confirm:
            msg = "Пароль и подтверждение пароля не совпадают"
            logging.error("%s | %s", msg, params_repr)
            return False, msg

        logging.info(
            "Успешная валидация регистрации: login=%r, password=%s",
            login, masked_password
        )
        return True, ""

    except Exception as ex:
        logging.error("Непредвиденная ошибка при валидации: %s", ex)
        logging.exception("Traceback:")
        logging.debug("Детали трассировки:\n%s", traceback.format_exc())
        return False, f"Внутренняя ошибка: {ex}"