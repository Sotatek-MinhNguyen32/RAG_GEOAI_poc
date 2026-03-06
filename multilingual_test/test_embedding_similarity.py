"""
Embedding language analysis — PoC test.

Tests how the embedding model handles:
1. Same-meaning text in different languages → cosine similarity
2. Unrelated text in same language → cosine similarity
3. Character-level differences (Latin vs CJK vs Vietnamese diacritics)

Run:
    PYTHONPATH=. conda run -n agent python multilingual_test/test_embedding_similarity.py
"""
import sys
import math

sys.path.insert(0, ".")

from shared.config import settings


def _get_embedding(text: str):
    if settings.USE_MOCK:
        from services.worker.processors.mock_embed import get_embedding
    else:
        from services.worker.processors.embed import get_embedding
    return get_embedding(text)


def cosine_similarity(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


# Test pairs: (label, text_a, text_b, expected_relation)
# expected_relation: "high" = same meaning, "low" = unrelated
TEST_PAIRS = [
    # Same meaning, same language
    ("EN↔EN same meaning",
     "satellite image of urban area with buildings",
     "aerial photo of a city with structures",
     "high"),

    # Same meaning, EN ↔ JA
    ("EN↔JA same meaning",
     "forest area near a mountain",
     "山の近くの森林地帯",
     "high"),

    # Same meaning, EN ↔ VI
    ("EN↔VI same meaning",
     "urban area with road networks",
     "khu vực đô thị với mạng lưới đường giao thông",
     "high"),

    # Same meaning, JA ↔ VI
    ("JA↔VI same meaning",
     "東京の都市部の衛星画像",
     "ảnh vệ tinh khu vực đô thị Tokyo",
     "high"),

    # Unrelated, same language
    ("EN↔EN unrelated",
     "satellite image of dense forest and vegetation",
     "industrial port with shipping containers and cranes",
     "low"),

    # Unrelated, cross-language
    ("JA↔EN unrelated",
     "富士山周辺の森林地帯",
     "industrial port with shipping containers",
     "low"),

    # Identical text
    ("Identical",
     "Tokyo satellite image",
     "Tokyo satellite image",
     "identical"),

    # Japanese with different scripts (Kanji vs Hiragana)
    ("JA Kanji vs Hiragana",
     "東京の都市部",
     "とうきょうのとしぶ",
     "high"),
]


def main():
    print("=" * 70)
    print("MULTILINGUAL EMBEDDING SIMILARITY TEST")
    print(f"Mock mode: {settings.USE_MOCK}")
    print("=" * 70)
    print()

    if settings.USE_MOCK:
        print("⚠️  MOCK embeddings: similarity scores are based on text hash, NOT semantics.")
        print("    Results below show the mock model behavior (not real cross-lingual capability).")
        print("    Set USE_MOCK=False and point to a real multilingual embedding service for real results.")
        print()

    for label, text_a, text_b, expected in TEST_PAIRS:
        vec_a = _get_embedding(text_a)
        vec_b = _get_embedding(text_b)
        sim = cosine_similarity(vec_a, vec_b)

        if expected == "identical":
            icon = "✅" if sim > 0.99 else "❌"
        elif expected == "high":
            icon = "✅" if sim > 0.7 else ("⚠️" if sim > 0.4 else "❌")
        else:  # low
            icon = "✅" if sim < 0.5 else ("⚠️" if sim < 0.7 else "❌")

        print(f"{icon} {label}")
        print(f"   A: {text_a[:60]}...")
        print(f"   B: {text_b[:60]}...")
        print(f"   Cosine similarity: {sim:.6f} (expected: {expected})")
        print()


if __name__ == "__main__":
    main()
