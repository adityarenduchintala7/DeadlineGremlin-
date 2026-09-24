#!/usr/bin/env python3
import sys
from pathlib import Path

# Ensure UTF-8 output encoding on Windows terminals to prevent charmap UnicodeEncodeErrors
if sys.stdout is not None and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if sys.stderr is not None and hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Add project root to sys.path so taskchecker can be imported from anywhere
package_root = Path(__file__).parent.parent.resolve()
if str(package_root) not in sys.path:
    sys.path.insert(0, str(package_root))

from taskchecker.cli import main

if __name__ == "__main__":
    main()
