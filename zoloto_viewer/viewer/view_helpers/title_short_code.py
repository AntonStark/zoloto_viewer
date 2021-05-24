import random
import re
import transliterate

CONSONANTS = 'bcdfgjklmnpqstvxzhrwy'


def make_code_candidates(title):
    # suggest a list of short codes for given title phrase

    def make_random_code(length):
        idx_all = range(len(CONSONANTS))
        idx = sorted(random.sample(idx_all, k=length))
        letters = [CONSONANTS[i] for i in idx]
        return ''.join(letters)

    title = title.lower()
    eng_title = transliterate.translit(title, 'ru', reversed=True)
    filtered = ''.join(re.findall('[a-z]+', eng_title))
    if len(filtered) < 4:
        more_three_size = [make_random_code(3) for _ in range(10)]
        return [filtered] + more_three_size

    head, *tail = filtered
    tail_consonants = [c for c in tail if c in CONSONANTS]
    title_consonants = [head] + tail_consonants

    def make_code(length):
        idx_all = range(len(title_consonants))
        idx = sorted(random.sample(idx_all, k=length))
        letters = [title_consonants[i] for i in idx]
        return ''.join(letters)

    if len(title_consonants) < 4:
        three_size = [make_random_code(3) for _ in range(10)]
    else:
        three_size = [make_code(3) for _ in range(10)]
    if len(title_consonants) < 6:
        four_size = [make_random_code(4) for _ in range(10)]
    else:
        four_size = [make_code(4) for _ in range(10)]
    candidates = three_size + four_size
    return candidates
