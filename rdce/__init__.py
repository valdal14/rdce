import logging

from .enforcer import enforce_contract

# Set up a silent logger for the library.
# This prevents "No handler found" warnings if the user hasn't configured logging,
# and ensures we never spam their console unless they explicitly ask for it.
logging.getLogger("rdce").addHandler(logging.NullHandler())

__all__ = ["enforce_contract"]
