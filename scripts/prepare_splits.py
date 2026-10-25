"""Create an audited grouped train/validation split."""

import sys

from retrocomposite.cli import main

if __name__ == "__main__":
    main(["split", *sys.argv[1:]])
