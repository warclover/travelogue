"""CodeError base class and migrated domain errors."""

from __future__ import annotations

import pytest

from travelogue.curation.curate import CurateError
from travelogue.demo.build import DemoError
from travelogue.errors import CodeError, PlainCodeError
from travelogue.export.longshot import LongshotExportError
from travelogue.export.packager import ExportError
from travelogue.export.pdf import PdfExportError
from travelogue.llm.errors import LlmError
from travelogue.media.image_ops import ImageOpsError
from travelogue.media.ingest import IngestError
from travelogue.render.engine import RenderError
from travelogue.services.errors import NarrateError
from travelogue.services.layout import LayoutError
from travelogue.services.pipeline_state import PipelineError
from travelogue.vision.clip_encoder import VisionMissingError
from travelogue.web.copy_patch import CopyPatchError
from travelogue.web.longshot_smoke import LongshotSmokeError
from travelogue.web.tier_patch import TierPatchError


@pytest.mark.parametrize(
    "cls",
    [
        RenderError,
        ExportError,
        DemoError,
        CurateError,
        LayoutError,
        IngestError,
        PipelineError,
        NarrateError,
        LlmError,
        CopyPatchError,
        TierPatchError,
        LongshotExportError,
    ],
)
def test_code_error_subclasses(cls: type[CodeError]) -> None:
    exc = cls("E_TEST", "hello")
    assert isinstance(exc, CodeError)
    assert exc.code == "E_TEST"
    assert exc.message == "hello"
    assert str(exc) == "E_TEST: hello"


@pytest.mark.parametrize(
    "cls,factory",
    [
        (PdfExportError, lambda: PdfExportError("pdf failed")),
        (LongshotSmokeError, lambda: LongshotSmokeError("smoke failed")),
        (ImageOpsError, lambda: ImageOpsError("ops failed")),
        (VisionMissingError, lambda: VisionMissingError()),
    ],
)
def test_plain_code_error_str(cls: type[PlainCodeError], factory) -> None:
    exc = factory()
    assert isinstance(exc, PlainCodeError)
    assert isinstance(exc, CodeError)
    assert exc.code
    assert str(exc) == exc.message
