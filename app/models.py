"""Shared data models (e.g. job posting) used by the app."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class JobPosting:
    """Represents a single job posting with its metadata and full description text."""

    title: str
    company: str
    location: str
    url: str
    description: str
