from research.gate0.sandbox.api_v1 import EducationApiV1
from research.gate0.sandbox.api_v2 import EducationApiV2
from research.gate0.sandbox.api_v3 import EducationApiV3
from research.gate0.sandbox.store import EducationSandboxStore, SandboxStateError

VERSIONS = ("v1", "v2", "v3")

_API_CLASSES = {"v1": EducationApiV1, "v2": EducationApiV2, "v3": EducationApiV3}


def build_api(version: str, store: EducationSandboxStore):
    try:
        api_cls = _API_CLASSES[version]
    except KeyError as exc:
        raise ValueError(f"Unknown sandbox API version {version!r}; expected one of {VERSIONS}.") from exc
    return api_cls(store)


__all__ = [
    "VERSIONS",
    "EducationApiV1",
    "EducationApiV2",
    "EducationApiV3",
    "EducationSandboxStore",
    "SandboxStateError",
    "build_api",
]
