"""Export n1, n5, and union stocks from actual cleaned-route leaves."""

import sys
from retrocomposite.cli import main

if __name__ == "__main__":
    main(["stock", *sys.argv[1:]])
