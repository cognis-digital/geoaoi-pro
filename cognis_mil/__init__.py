"""cognis_mil — shared library for the 12-repo military/IC ecosystem.

Public, unclassified, EAR99. Provides:
  - Finding/ScanResult models with classification-placeholder fields
  - Severity-weighted scoring (NIST 800-30 style: Very High → Very Low)
  - 5 exporters: console / JSON / SARIF / Markdown / OSCAL-skeleton
  - CLI builder with --classification flag (placeholder only)
  - Audit-log primitive (hash-chained, tamper-evident, local-only)
"""
from .audit import AuditLog as AuditLog
from .classmark import ClassificationBanner as ClassificationBanner
from .cli import make_cli as make_cli
from .exporters import to_console as to_console
from .exporters import to_json as to_json
from .exporters import to_markdown as to_markdown
from .exporters import to_oscal_skeleton as to_oscal_skeleton
from .exporters import to_sarif as to_sarif
from .models import Finding as Finding
from .models import ScanResult as ScanResult
from .models import Severity as Severity

__version__ = "0.1.0"
