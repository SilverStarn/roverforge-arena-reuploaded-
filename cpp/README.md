# Optional Native Module

The Python simulation automatically uses a pure-Python path scorer. This C++ module provides the
same scoring function behind a native boundary.

Build with CMake when a compiler is available:

```powershell
cmake -S cpp -B cpp/build
cmake --build cpp/build --config Release
```

On Windows the expected output is:

```text
cpp/build/Release/arena_native.dll
```

The Python loader also respects an explicit path:

```powershell
$env:PANDA_ARENA_NATIVE="C:\path\to\arena_native.dll"
```
