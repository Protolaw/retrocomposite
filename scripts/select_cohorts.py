"""Select shared linear tactics and audited experimental cohorts."""

import sys

from retrocomposite.cli import main

if __name__ == "__main__":
    main(["select-cohorts", *sys.argv[1:]])
