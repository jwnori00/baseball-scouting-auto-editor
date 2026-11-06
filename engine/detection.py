"""Extension contract only: no trained pitch detector is shipped in v0.1.0."""
from dataclasses import dataclass
from typing import Protocol

@dataclass(frozen=True)
class Candidate:
    source_file: str
    start: float
    end: float
    confidence: float
    status: str = 'AUTO_CANDIDATE'
    reason: str = ''

class PitchDetector(Protocol):
    """Local models/OCR may propose candidates; user confirmation is mandatory."""
    def detect(self, source_file: str, start: float, end: float) -> list[Candidate]: ...
