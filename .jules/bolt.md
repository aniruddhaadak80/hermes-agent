## 2024-05-24 - Holographic Memory Optimization
**Learning:** Python loops executing struct.unpack and list comprehensions converting numpy vectors into python objects (e.g. `[np.exp(1j * v) for v in vectors]`) are serious performance bottlenecks inside core math functions compared to numpy's native C vectorization.
**Action:** When working on numerical/AI representations, immediately look for ways to rewrite element-wise list comprehensions using native `numpy` vectorization such as `numpy.stack`, `numpy.frombuffer`, and `bytearray` building instead of standard list appending.

## 2024-09-12 - Atom Encoding Allocation Overhead
**Learning:** Python-level `bytearray.extend()` operations combined with redundant UTF-8 encodings in tight loops introduce measurable overhead during fact memory atom encoding.
**Action:** Use list comprehensions and native `b"".join()` to collect bytes along with hoisting invariant strings out of loops. This avoids intermediary allocations and repetitive encoding logic for immediate micro-optimization wins.
