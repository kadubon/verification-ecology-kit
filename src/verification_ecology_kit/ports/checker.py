"""Checker port."""

from __future__ import annotations

from typing import Protocol

from verification_ecology_kit.result import CheckResult


class Checker(Protocol):
    def check(self, payload: object) -> CheckResult: ...
