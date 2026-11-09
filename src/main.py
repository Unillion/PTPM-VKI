
import logging

from logger import setup_logging
from validator import validate_registration, mask_secret


def main() -> None:
    setup_logging()

    logging.info("Приложение запущено")

    demos = [
        ("user_01", "Пароль1!", "Пароль1!"),

        ("", "Пароль1!", "Пароль1!"),
        ("юзер", "Пароль1!", "Пароль1!"),
        ("admin", "Пароль1!", "Пароль1!"),
        ("+7-999-999-9999", "Пароль1!", "Пароль1!"),
        ("user_02", "123", "123"),
        ("user_03", "password1!", "password1!"),
        ("user_04", "пароль1!", "пароль1!"),
        ("user_05", "ПАРОЛЬ1!", "ПАРОЛЬ1!"),
        ("user_06", "Пароль!", "Пароль!"),
        ("user_07", "Пароль1", "Пароль1"),
        ("user_08", "Пароль1!", "Пароль2!"),
        ("user_09", "Пароль1!", ""),
        ("john.doe@example.com", "Кириллица9#", "Кириллица9#"),
        ("aaa2324234", "РРРООЗЩОп1!", "ПРПРРПРПаа3")
    ]

    for login, pwd, confirm in demos:
        ok, msg = validate_registration(login, pwd, confirm)
        status = "OK " if ok else "ERR"
        print(f"[{status}] login={login!r} -> {msg or 'успех'} "
              f"| pwd={mask_secret(pwd)}")

    logging.info("Приложение завершено")


if __name__ == "__main__":
    main()