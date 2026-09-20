"""Package an actual showcase recording as a README GIF and an MP4.

Requires ffmpeg and ffprobe on PATH. The original recording and every captured
outcome are retained. Only encoding, dimensions and frame sampling change;
there is no trimming, speed adjustment, generated frame or substituted output.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(command: list[str]) -> str:
    completed = subprocess.run(command, check=True, capture_output=True, text=True)
    return completed.stdout


def inspect(path: Path) -> dict:
    return json.loads(run([
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height,codec_name:format=duration,size",
        "-of", "json", str(path),
    ]))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--width", type=int, default=1120)
    parser.add_argument("--fps", type=int, default=10)
    args = parser.parse_args(argv)
    if not 320 <= args.width <= 1920 or not 1 <= args.fps <= 30:
        parser.error("width must be 320–1920 and fps must be 1–30")
    for binary in ("ffmpeg", "ffprobe"):
        if not shutil.which(binary):
            parser.error(f"{binary} must be installed separately and available on PATH")
    capture = args.capture_dir.resolve()
    transcript_path = capture / "transcript.json"
    transcript = json.loads(transcript_path.read_text())
    video = (capture / transcript["video"]).resolve()
    if not video.is_relative_to(capture) or not video.is_file():
        parser.error("transcript.video must name a file inside the capture directory")
    if video.suffix != ".webm":
        parser.error("expected the original Playwright WebM recording")
    if transcript["video"] != "original.webm":
        parser.error("recording must use video='original.webm' for portable evidence")
    if not transcript.get("video_saved") or not transcript.get("video_sha256"):
        parser.error("transcript must confirm a finalized video and its capture SHA-256")
    if sha256(video) != transcript["video_sha256"]:
        parser.error("original video does not match the capture SHA-256; preserve and inspect it")
    # These are public synthetic captures, never arbitrary browser profiles.
    text = transcript_path.read_text()
    if any(marker in text for marker in ("/Users/", "C:\\Users\\", "Bearer ")):
        parser.error("review and remove private paths or credentials before packaging")
    output = args.output.resolve()
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        parser.error("output directory must be empty; preserve prior attempts")
    output.mkdir(parents=True, exist_ok=True)
    original = output / "original.webm"
    shutil.copy2(video, original)
    # Preserve the raw transcript byte-for-byte, including failures and timing.
    shutil.copy2(transcript_path, output / "transcript.json")
    for screenshot in sorted(capture.glob("*.png")):
        shutil.copy2(screenshot, output / screenshot.name)
    mp4 = output / "full-run.mp4"
    run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-i", str(original),
        "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-pix_fmt", "yuv420p", "-threads", "2", "-movflags", "+faststart", str(mp4),
    ])
    gif = output / "preview.gif"
    gif_filter = (
        f"fps={args.fps},scale={args.width}:-1:flags=lanczos,split[a][b];"
        "[a]palettegen=stats_mode=diff:max_colors=128[p];"
        "[b][p]paletteuse=dither=bayer:bayer_scale=3:diff_mode=rectangle"
    )
    run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-i", str(original),
        "-filter_complex_threads", "2", "-filter_complex", gif_filter,
        "-an", "-loop", "0", str(gif),
    ])
    media = {path.name: inspect(path) for path in (original, mp4, gif)}
    original_seconds = float(media[original.name]["format"]["duration"])
    for path in (mp4, gif):
        difference = abs(float(media[path.name]["format"]["duration"]) - original_seconds)
        if difference > max(0.2, 2 / args.fps):
            raise RuntimeError(f"Unexpected duration change in {path.name}: {difference:.3f}s")
    files = sorted(path for path in output.iterdir() if path.is_file())
    provenance = {
        "format_version": 1,
        "scope": "Illustrative live-model recording, not a held-out quality benchmark.",
        "source": "transcript.json and original.webm from examples/record_showcase.py",
        "presentation": (
            "Full recording, without trimming or speed changes. MP4 re-encodes the "
            "original; GIF reduces dimensions, frame rate and colors and loops. "
            "No model result, measured latency or execution receipt is rewritten."
        ),
        "ffmpeg": run(["ffmpeg", "-version"]).splitlines()[0],
        "gif_settings": {"width": args.width, "fps": args.fps, "colors": 128},
        "media": media,
        "artifact_sha256": {path.name: sha256(path) for path in files},
    }
    (output / "provenance.json").write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2) + "\n"
    )
    print(json.dumps({
        "duration_seconds": original_seconds,
        "gif_bytes": gif.stat().st_size,
        "mp4_bytes": mp4.stat().st_size,
        "files": len(files),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
