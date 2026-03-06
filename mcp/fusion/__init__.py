"""
Fusion module — Hợp nhất kết quả search bằng RRF + Cross-Encoder.

Public API:
    fuse_and_rank()      — async orchestrator (full pipeline)
    fuse_and_rank_sync() — sync wrapper
"""
from mcp.fusion.pipeline import fuse_and_rank, fuse_and_rank_sync

__all__ = ["fuse_and_rank", "fuse_and_rank_sync"]
