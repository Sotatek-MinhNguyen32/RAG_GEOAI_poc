"""Mock Embedding Processor — trả về vector cố định để test local, KHÔNG push lên remote."""
import hashlib
import math
from typing import List


def get_embedding(text: str) -> List[float]:
    """Trả về vector 2048 chiều giả lập dựa trên hash của text."""
    if not text:
        raise ValueError("Empty text input.")

    seed = int(hashlib.sha256(text.encode()).hexdigest(), 16)
    dim = 2048
    vector = []
    for i in range(dim):
        val = math.sin(seed * (i + 1) * 0.0001) * 0.5 + math.cos(seed * (i + 1) * 0.00017) * 0.5
        vector.append(round(val, 6))

    # L2 normalize
    norm = math.sqrt(sum(v * v for v in vector)) or 1.0
    return [round(v / norm, 6) for v in vector]
