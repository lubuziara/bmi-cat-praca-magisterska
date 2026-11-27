import re


def validate_phone(value: str) -> str:
    value = re.sub(r"[ ()-]", "", value.strip())
    if not re.fullmatch(r"\+[1-9][0-9]{7,14}", value):
        raise ValueError("Podaj telefon z numerem kierunkowym kraju, np. +48 123 456 789.")
    return value
