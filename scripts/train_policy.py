"""Train a seeded MHN using frozen grouped assignments."""

import sys

from retrocomposite.cli import main

if __name__ == "__main__":
    main(["train", *sys.argv[1:]])
