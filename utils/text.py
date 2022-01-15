import random
import pymorphy2

morph = pymorphy2.MorphAnalyzer()

class plural:
    def __init__(self, word: str) -> None:
        self.word = morph.parse(word)[0]
    
    def __format__(self, __format_spec: str) -> str:
        try:
            __format_spec = int(__format_spec)
        except ValueError:
            raise TypeError(f'format spec {__format_spec!r} must be a numeric')
        
        return f'{str(__format_spec)} {self.word.make_agree_with_number(__format_spec).word}'
    
    def __repr__(self) -> str:
        return f'<plural word={self.word}>'

class random_chr:
    def __init__(self, a, b) -> None:
        self.ab = (a, b)
    def __format__(self, __format_spec: str) -> str:
        try:
            __format_spec = int(__format_spec)
        except ValueError:
            raise TypeError(f'format spec {__format_spec!r} must be a numeric')

        return ''.join([chr(random.randint(*self.ab)) for i in range(__format_spec)])