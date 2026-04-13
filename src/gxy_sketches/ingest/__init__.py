from .base import Ingestor, WorkflowFile
from .iwc import IwcIngestor
from .nf_core import NfCoreIngestor

__all__ = ["Ingestor", "WorkflowFile", "IwcIngestor", "NfCoreIngestor"]
