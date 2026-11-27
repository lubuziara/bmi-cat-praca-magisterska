import unicodedata


def validate_name(value: str) -> str:
    value = unicodedata.normalize("NFC", value.strip())
    if not 1 <= len(value) <= 80 or not any(c.isalpha() for c in value):
        raise ValueError("Podaj imię (od 1 do 80 znaków).")
    if any(not c.isalpha() and c not in " -'’" for c in value):
        raise ValueError("Imię może zawierać litery, spacje, apostrof i łącznik.")
    return value
