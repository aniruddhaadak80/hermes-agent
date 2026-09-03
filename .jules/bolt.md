## 2024-05-24 - Holographic Memory Optimization
**Learning:** Python loops executing struct.unpack and list comprehensions converting numpy vectors into python objects (e.g. `[np.exp(1j * v) for v in vectors]`) are serious performance bottlenecks inside core math functions compared to numpy's native C vectorization.
**Action:** When working on numerical/AI representations, immediately look for ways to rewrite element-wise list comprehensions using native `numpy` vectorization such as `numpy.stack`, `numpy.frombuffer`, and `bytearray` building instead of standard list appending.

## 2026-09-03 - Fast YAML Loading Optimization
**Learning:** The default `yaml.safe_load` in PyYAML uses a pure-Python loader which is significantly slower than the libyaml-backed C extension (`CSafeLoader`). Replacing `yaml.safe_load` with the codebase's custom `fast_safe_load` wrapper (which opportunistically uses the C loader) reduces parsing time during startup and runtime configuration reads.
**Action:** Replace all generic occurrences of `yaml.safe_load` with the optimized `fast_safe_load` imported from `utils` to decrease cold-start and configuration reading overhead.
