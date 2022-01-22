import random
import pymorphy2  # type: ignore

morph = pymorphy2.MorphAnalyzer()


class plural:
    def __init__(self, word: str) -> None:
        self.word = morph.parse(word)[0]

    def __format__(self, __format_spec: str) -> str:
        try:
            spec = int(__format_spec)
        except ValueError:
            raise TypeError(f"format spec {__format_spec!r} must be a numeric")

        return f"{str(spec)} {self.word.make_agree_with_number(spec).word}"

    def __repr__(self) -> str:
        return f"<plural word={self.word}>"


class random_chr:
    def __init__(self, a: int, b: int) -> None:
        self.a = a
        self.b = b + 1

    def __format__(self, __format_spec: str) -> str:
        try:
            spec = int(__format_spec)
        except ValueError:
            raise TypeError(f"format spec {__format_spec!r} must be a numeric")

        return "".join([chr(random.randint(self.a, self.b)) for _ in range(spec)])
