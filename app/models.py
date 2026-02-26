"""Shared data models (e.g. job posting) used by the app."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class JobPosting:
    title: str
    company: str
    location: str
    url: str
    description: str
