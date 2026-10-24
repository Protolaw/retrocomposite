"""Export n1+n5 reactions and invoke native SynPlanner rule extraction."""

import sys
from retrocomposite.cli import main

if __name__ == "__main__":
    main(["single-step", *sys.argv[1:]])
