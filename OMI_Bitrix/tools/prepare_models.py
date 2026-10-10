"""Build-time model preparation. Runtime inference never calls this script."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODELS = (
    ("intfloat/multilingual-e5-base", "d128750597153bb5987e10b1c3493a34e5a4502a", "multilingual-e5-base", "MIT"),
    ("BAAI/bge-reranker-v2-m3", "953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e", "bge-reranker-v2-m3", "Apache-2.0"),
)


def checksum(path):
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--download", action="store_true", help="Explicit connected build step; fetch pinned public weights")
    action.add_argument("--write-manifest", action="store_true", help="Hash already prepared local files without network")
    args = parser.parse_args()
    manifest_path = ROOT / "models" / "MODEL_MANIFEST.json"
    if args.download or args.write_manifest:
        manifest = {"models": [], "runtime_downloads": False}
        for repo, revision, folder, license_name in MODELS:
            target = ROOT / "models" / folder
            if args.download:
                from huggingface_hub import snapshot_download
                snapshot_download(repo, revision=revision, local_dir=target,
                    allow_patterns=["*.json", "model.safetensors", "README.md", "LICENSE*", "1_Pooling/config.json"])
            for required in ("model.safetensors", "config.json", "tokenizer.json", "README.md"):
                if not (target / required).is_file():
                    raise SystemExit(f"Missing model file: {folder}/{required}")
            files = {p.relative_to(target).as_posix(): checksum(p) for p in sorted(target.rglob("*"))
                     if p.is_file() and ".cache" not in p.relative_to(target).parts}
            manifest["models"].append({"repo": repo, "revision": revision, "folder": folder,
                "license": license_name, "source": "https://huggingface.co/" + repo,
                "bytes": sum((target / name).stat().st_size for name in files), "sha256": files})
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for model in manifest["models"]:
        for name, digest in model["sha256"].items():
            if checksum(ROOT / "models" / model["folder"] / name) != digest:
                raise SystemExit(f"Checksum mismatch: {model['folder']}/{name}")
    print(f"Verified {len(manifest['models'])} local models; no task data used.")


if __name__ == "__main__":
    main()
