"""Prefix-tree LRU matching the KVCache.AI simulator: evict only least-recent leaves."""

import heapq
from collections.abc import Hashable, Iterable, Sequence
from dataclasses import dataclass, field

from common.trace import Request


@dataclass(eq=False)
class _Node:
    parent: "_Node | None" = None
    block: Hashable = None
    children: dict[Hashable, "_Node"] = field(default_factory=dict)
    touched: int = 0
    active: bool = True


class LeafLRU:
    def __init__(self, capacity: int) -> None:
        self.capacity = capacity
        self.root = _Node()
        self.size = 0
        self.filled = capacity == 0
        self.clock = 0
        self.leaves: list[tuple[int, _Node]] = []

    def _touch(self, node: _Node) -> None:
        self.clock += 1
        node.touched = self.clock
        if not node.children:
            heapq.heappush(self.leaves, (node.touched, node))

    def _evict(self, protected: set[_Node]) -> bool:
        skipped = []
        victim = None
        while self.leaves:
            stamp, node = heapq.heappop(self.leaves)
            if not node.active or node.children or stamp != node.touched:
                continue
            if node in protected:
                skipped.append((stamp, node))
                continue
            victim = node
            break
        for entry in skipped:
            heapq.heappush(self.leaves, entry)
        if victim is None:
            return False
        parent = victim.parent
        del parent.children[victim.block]
        victim.active = False
        self.size -= 1
        if parent is not self.root and not parent.children:
            heapq.heappush(self.leaves, (parent.touched, parent))
        return True

    def match(self, blocks: Iterable[Hashable]) -> int:
        """Count a prefix without changing cache contents or recency."""
        node: _Node | None = self.root
        hits = 0
        for block in blocks:
            node = node.children.get(block)
            if node is None:
                break
            hits += 1
        return hits

    def access(self, blocks: Sequence[Hashable]) -> int:
        """Probe then admit a request; return its cached prefix length in blocks.

        The pre-existing prefix is protected during admission. Newly inserted nodes
        are evictable, so a request longer than the budget can evict its own tail.
        """
        parent = self.root
        protected = set()
        for block in blocks:
            child = parent.children.get(block)
            if child is None:
                break
            self._touch(child)
            protected.add(child)
            parent = child
        hits = len(protected)
        for block in blocks[hits:]:
            if self.size == self.capacity and not self._evict(protected):
                break
            if not parent.active:
                break
            child = _Node(parent=parent, block=block)
            parent.children[block] = child
            self.size += 1
            self.filled |= self.size == self.capacity
            self._touch(child)
            parent = child
        return hits


def replay(
    requests: Iterable[Request], capacity: int, block_size: int, warmup: int = 0
) -> list[int] | None:
    """Return hit tokens for each request after `warmup`, in file order.

    Returns None if a warmup never filled the cache. Inputs carry one hash ID per
    block, including a partial tail, which occupies a slot and counts its actual tokens.
    """
    cache = LeafLRU(capacity)
    hits = []
    for index, request in enumerate(requests):
        if warmup and index == warmup and not cache.filled:
            return None
        blocks = cache.access(request["hash_ids"])
        if index >= warmup:
            hits.append(min(request["input_length"], blocks * block_size))
    return hits
