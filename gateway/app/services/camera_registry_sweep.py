"""On-demand sweep of every registered camera → ``scan_results`` (with location).

Prefer importing :func:`sweep_all_registered_cameras_to_db` from here for clarity; the
implementation lives in :mod:`app.services.scanner`.
"""

from app.services.scanner import RegistrySweepSummary, sweep_all_registered_cameras_to_db

__all__ = ["RegistrySweepSummary", "sweep_all_registered_cameras_to_db"]
