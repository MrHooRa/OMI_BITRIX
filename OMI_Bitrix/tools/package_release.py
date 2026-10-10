"""Build a clean, explicit-inventory release ZIP; never include runtime data."""
import hashlib
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT.parent / "OMI_Bitrix_3.10_Clean_2026-10-10.zip"
EXCLUDED = {"data", ".venv", "__pycache__", ".playwright-cli", "output", ".git", ".cache"}
for folder in ("multilingual-e5-base", "bge-reranker-v2-m3"):
    if not (ROOT / "models" / folder / "model.safetensors").is_file():
        raise SystemExit("Prepare local models before packaging: " + folder)
files = list(ROOT.glob("*.py"))
files += [ROOT / name for name in ("README.md", "requirements.txt", "requirements-lock.txt", "start.bat", "start.sh")]
for folder in ("templates", "static", "docs", "tests", "tools", "wheelhouse", "models"):
    files += [p for p in (ROOT / folder).rglob("*") if p.is_file() and not set(p.relative_to(ROOT).parts) & EXCLUDED]
files = sorted(set(p for p in files if p.is_file()))
manifest = {}
with ZipFile(DEST, "w", ZIP_DEFLATED) as archive:
    for path in files:
        relative = path.relative_to(ROOT).as_posix()
        if set(path.relative_to(ROOT).parts) & EXCLUDED:
            continue
        archive.write(path, "OMI_Bitrix/" + relative)
        digest = hashlib.sha256()
        with path.open("rb") as source:
            for block in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(block)
        manifest[relative] = digest.hexdigest()
    archive.writestr("OMI_Bitrix/RELEASE_MANIFEST.json", json.dumps(manifest, indent=2))
with ZipFile(DEST) as archive:
    assert archive.testzip() is None
    assert not any(set(Path(name).parts) & EXCLUDED for name in archive.namelist())
with DEST.open("rb") as source:
    archive_digest = hashlib.file_digest(source, "sha256").hexdigest()
print(json.dumps({"archive": str(DEST), "files": len(manifest), "bytes": DEST.stat().st_size,
                  "sha256": archive_digest}))
