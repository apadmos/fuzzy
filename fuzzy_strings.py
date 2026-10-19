import datetime
import re
import unicodedata


class FuzzyStrings:
    """Forgiving string helpers: turning messy text into clean values and values into display text"""

    @staticmethod
    def slugify(text: str | None, allow_slashes: bool = False) -> str:
        """
        Lowercase ASCII words joined by hyphens: "Café Night: Part 2" -> "cafe-night-part-2".
        Punctuation is dropped ("Don't" -> "dont"); spaces and underscores become hyphens.
        allow_slashes keeps "/" for nested paths ("Shows/Spring Gala" -> "shows/spring-gala"),
        otherwise "/" separates words like a space does.
        Returns "" when nothing usable is left, so callers decide whether that's an error.
        """
        if not text:
            return ""
        slug: str = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
        slug = slug.lower().strip().rstrip("/")
        if not allow_slashes:
            slug = slug.replace("/", " ")
        slug = re.sub(r"[^a-z0-9\s/_-]", "", slug)
        slug = re.sub(r"[\s_]+", "-", slug)
        slug = re.sub(r"-+", "-", slug)
        return slug.strip("-")

    @staticmethod
    def guess_parse(value: str) -> datetime.datetime | bool | str | float | int:
        """Turns a string into the bool, int, float or datetime it looks like, or returns it unchanged"""
        # Check if value is actually a string
        if not isinstance(value, str):
            return value

        # Handle empty or whitespace-only strings
        if not value or not value.strip():
            return value

        value = value.strip()

        # Try boolean first (case-insensitive, excluding '1' and '0')
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'

        # Try integer
        try:
            # Check if it looks like an integer (no decimal point)
            if '.' not in value and 'e' not in value.lower():
                return int(value)
        except ValueError:
            pass

        # Try float
        try:
            return float(value)
        except ValueError:
            pass

        # Try ISO datetime parsing first (most common in APIs)
        try:
            return datetime.datetime.fromisoformat(value.replace('Z', '+00:00'))
        except ValueError:
            pass

        # Try other common datetime formats
        datetime_formats = [
            '%Y-%m-%d %H:%M:%S',  # 2023-12-25 14:30:00
            '%Y-%m-%d',  # 2023-12-25
            '%m/%d/%Y',  # 12/25/2023
            '%d/%m/%Y',  # 25/12/2023
            '%Y/%m/%d',  # 2023/12/25
            '%m-%d-%Y',  # 12-25-2023
            '%d-%m-%Y',  # 25-12-2023
        ]

        for fmt in datetime_formats:
            try:
                return datetime.datetime.strptime(value, fmt)
            except ValueError:
                continue

        # If nothing else worked, return as string
        return value

    @staticmethod
    def money_usd(amount) -> str:
        return FuzzyStr.with_commas(amount, accuracy=2, prefix="$")

    @staticmethod
    def quantity(amount, accuracy: int = 0) -> str:
        return FuzzyStr.with_commas(amount, accuracy=accuracy, prefix='')

    @staticmethod
    def with_commas(amount, accuracy: int = 0, prefix: str = "$") -> str:
        amount = str(amount)
        if not amount:
            amount = "0"

        parts = amount.split(".")
        if accuracy < 1:
            decimals = ""
        else:
            decimals = parts[1].ljust(accuracy, '0') if len(parts) > 1 else "00".ljust(accuracy, '0')
            decimals = f".{decimals[:accuracy]}"

        dollars = parts[0]
        ds = []
        comma = -1
        negative = dollars[0] == "-"
        for char in reversed(dollars):
            if char in "0123456789":
                comma += 1
                if comma > 2:
                    ds.insert(0, ",")
                    comma = 0
                ds.insert(0, char)

        dollars = "".join(ds)
        return f"-{prefix}{dollars}{decimals}" if negative else f"{prefix}{dollars}{decimals}"


if __name__ == '__main__':
    print(FuzzyStr.slugify("Café Night: Part 2"))
    print(FuzzyStr.money_usd("-3456"))
    print(FuzzyStr.money_usd("234342.34"))
    print(repr(FuzzyStr.guess_parse("2023-12-25")))
