"""Gerador de lançamentos contábeis pelo regime de competência, apoiado por LLM."""

__version__ = "1.0.0"

import logging as _logging

_logging.getLogger("lancamentos").addHandler(_logging.NullHandler())
