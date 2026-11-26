"""
Match what the user types to a drug in DDInter.

Handles:
  - brand names   ("Advil" -> ibuprofen), from brand_names.py
  - other names   ("paracetamol" / "acetaminophen")
  - typos         ("ibuprofn" -> Ibuprofen)
  - drug names inside a sentence ("Can I take warfarin with aspirin?")

Check which brand-name entries are missing from your DDInter data:
    python -m chatbot.name_matcher
"""

import re

from rapidfuzz import fuzz, process

from chatbot.brand_names import SYNONYMS

# Common words that should never be read as a drug name.
STOPWORDS = {
    "can", "i", "take", "with", "and", "or", "the", "a", "an", "is", "it",
    "safe", "together", "to", "my", "me", "do", "does", "they", "interact",
    "if", "what", "about", "mix", "taking", "also", "am", "on", "of", "for",
    "are", "these", "two", "medicines", "drugs", "pill", "pills", "same",
    "time", "should", "will", "would", "be", "ok", "okay", "while", "plus",
    "check", "please", "hi", "hello", "there", "any", "between", "have",
    "mom", "dad", "grandma", "grandpa", "mother", "father", "she", "he",
    "her", "his", "takes", "daily", "every", "day", "morning", "night",
}


class NameMatcher:
    def __init__(self, names: dict[str, str], min_score: int = 85):
        """names: DDInter ID -> drug name."""
        self.by_lower = {name.lower(): (drug_id, name) for drug_id, name in names.items()}
        self.choices = list(self.by_lower)
        self.min_score = min_score

    def match(self, text: str) -> tuple[str, str] | None:
        """Return (DDInter ID, drug name) for one name, or None."""
        query = text.strip().lower()
        if not query:
            return None
        for candidate in SYNONYMS.get(query, [query]):
            if candidate in self.by_lower:
                return self.by_lower[candidate]
        best = process.extractOne(
            query, self.choices, scorer=fuzz.ratio, score_cutoff=self.min_score
        )
        return self.by_lower[best[0]] if best else None

    def find_in_message(self, message: str, max_drugs: int = 2) -> list[str]:
        """Find drug names inside a sentence. Returns the matched drug names."""
        words = re.findall(r"[A-Za-z0-9][A-Za-z0-9\-]*", message)
        used = [False] * len(words)
        found: list[tuple[int, str, str]] = []  # (position, id, name)

        for n in (3, 2, 1):  # try longer phrases first ("folic acid" before "acid")
            for i in range(len(words) - n + 1):
                if any(used[i : i + n]):
                    continue
                phrase = " ".join(words[i : i + n]).lower()
                if n == 1 and (phrase in STOPWORDS or len(phrase) < 4):
                    if phrase not in SYNONYMS:
                        continue
                m = self.match(phrase)
                if m and all(m[0] != f[1] for f in found):
                    found.append((i, m[0], m[1]))
                    for j in range(i, i + n):
                        used[j] = True

        found.sort()
        return [name for _, _, name in found[:max_drugs]]

    def missing_synonyms(self) -> list[tuple[str, list[str]]]:
        """Brand-name entries whose generic names are not in the data."""
        return [
            (brand, targets)
            for brand, targets in SYNONYMS.items()
            if not any(t in self.by_lower for t in targets)
        ]


if __name__ == "__main__":
    from model.predict import get_matcher

    matcher = get_matcher()
    missing = matcher.missing_synonyms()
    print(f"Drugs in DDInter: {len(matcher.choices):,}")
    print(f"Brand-name entries: {len(SYNONYMS)}, found: {len(SYNONYMS) - len(missing)}")
    if missing:
        print("\nNot found in DDInter (check the spelling DDInter uses):")
        for brand, targets in missing:
            close = process.extract(targets[0], matcher.choices, scorer=fuzz.WRatio, limit=3)
            hints = ", ".join(c for c, _, _ in close)
            print(f"  {brand:<14} -> {', '.join(targets):<35} closest: {hints}")