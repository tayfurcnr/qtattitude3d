import sys
import warnings

warnings.simplefilter("ignore", DeprecationWarning)

from .demo import main


if __name__ == "__main__":
    raise SystemExit(main())
