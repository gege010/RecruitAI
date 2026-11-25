"""Prepare and start RecruitAI on the loopback interface."""

import argparse
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import venv


ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("--port harus antara 1 dan 65535.")
    if sys.version_info[:2] not in {(3, 11), (3, 12)}:
        parser.error("Gunakan Python 3.11 atau 3.12 untuk menjalankan RecruitAI.")

    environment = ROOT / ".venv"
    python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    stamp = environment / ".recruitai-dependencies"
    digest = hashlib.sha256()
    for filename in ("requirements.txt", "requirements.lock"):
        digest.update((ROOT / filename).read_bytes())
    fingerprint = digest.hexdigest()

    try:
        if not python.is_file():
            stamp.unlink(missing_ok=True)
            print("Menyiapkan lingkungan Python RecruitAI…", flush=True)
            venv.EnvBuilder(with_pip=True).create(environment)
        if not stamp.exists() or stamp.read_text(encoding="ascii") != fingerprint:
            print(
                "Memasang dependensi. Instalasi pertama memerlukan internet.",
                flush=True,
            )
            subprocess.run(
                [python, "-m", "pip", "install", "-r", "requirements.txt"],
                cwd=ROOT,
                check=True,
            )
            stamp.write_text(fingerprint, encoding="ascii")
        print(
            f"Buka http://127.0.0.1:{args.port} di browser. Tekan Ctrl+C untuk berhenti.",
            flush=True,
        )
        return subprocess.call(
            [
                python,
                "-m",
                "uvicorn",
                "server.main:app",
                "--host",
                "127.0.0.1",
                "--port",
                str(args.port),
                "--no-access-log",
            ],
            cwd=ROOT,
        )
    except KeyboardInterrupt:
        return 0
    except (OSError, subprocess.CalledProcessError) as error:
        print(f"Penyiapan RecruitAI gagal: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
