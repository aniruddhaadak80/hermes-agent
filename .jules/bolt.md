## 2024-05-24 - Holographic Memory Optimization
**Learning:** Python loops executing struct.unpack and list comprehensions converting numpy vectors into python objects (e.g. `[np.exp(1j * v) for v in vectors]`) are serious performance bottlenecks inside core math functions compared to numpy's native C vectorization.
**Action:** When working on numerical/AI representations, immediately look for ways to rewrite element-wise list comprehensions using native `numpy` vectorization such as `numpy.stack`, `numpy.frombuffer`, and `bytearray` building instead of standard list appending.
