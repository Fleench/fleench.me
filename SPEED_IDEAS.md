# Speed Improvements for `gen.py`

Based on a review of the `gen.py` engine, the following areas show the greatest potential for performance improvement:

## 1. Memoization & Caching
- **Component Rendering:** Implement a hash-based cache for rendered components/elements. Store the rendered output of a component (e.g., in `.cache/`) and only re-render if the source file or its dependencies have changed.
- **Dependency Tracking:** Track the "last modified" time of files (Markdown content, templates, Python scripts). If a file and its dependencies are unchanged, skip the build step for that page.

## 2. Dynamic Module Management
- **Persistent Loader Cache:** `importlib.util.spec_from_file_location` and `importlib.util.module_from_spec` are expensive operations when performed inside a tight loop for every component. Implement a global `ModuleRegistry` that caches loaded module objects, re-using them across pages if the source file hasn't changed.

## 3. Parallelization
- **Multiprocessing:** Page rendering (the `render()` call in `Page`) is inherently parallelizable. Use Python's `multiprocessing` or `concurrent.futures` to render pages in parallel across available CPU cores.

## 4. Faster IO
- **Async/Batch Writes:** Instead of writing files one by one as they are rendered, buffer the rendered output and write to the filesystem in a single batch (or use thread-pooled I/O) to reduce disk I/O latency.

## 5. Algorithmic Optimization
- **Regex/Parser Complexity:** The current `inject_elements` runs a loop up to 10 times to handle nested elements. While robust, this is inefficient for deeply nested structures. Consider a recursive descent parser or a single-pass tree traversal to resolve all dependencies in one walk.
