"""Neutral error types shared by all board backends."""

from __future__ import annotations


class BoardAPIError(Exception):
    """Any board backend failure (network, HTTP, bad data).

    Skills catch this — never a backend-specific subclass — so swapping
    Trello for another backend changes nothing in the workflow code.
    """

    def __init__(self, message: str, status: int | None = None):
        super().__init__(message)
        self.status = status
