"""Video downloading service using yt-dlp."""

import asyncio
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yt_dlp


class DownloadError(Exception):
    """Raised when video download fails."""


class FileTooLargeError(DownloadError):
    """Raised when downloaded file exceeds size limit."""

    def __init__(self, file_size: int, max_size: int):
        self.file_size = file_size
        self.max_size = max_size
        super().__init__(
            f"File size ({file_size // 1024 // 1024}MB) "
            f"exceeds limit ({max_size // 1024 // 1024}MB)"
        )


class VideoUnavailableError(DownloadError):
    """Raised when video is unavailable (private, deleted, etc.)."""


@dataclass
class DownloadResult:
    """Result of a successful download."""

    file_path: Path
    title: str
    duration: int | None  # seconds
    file_size: int  # bytes


class VideoDownloader:
    """Downloads videos from supported platforms using yt-dlp."""

    def __init__(
        self,
        temp_dir: str = "/tmp/yt-downloader-bot",  # noqa: S108
        max_file_size: int = 50 * 1024 * 1024,
        timeout: int = 300,
        cookies_file: str | None = None,
    ):
        self._temp_dir = Path(temp_dir)
        self._max_file_size = max_file_size
        self._timeout = timeout
        self._cookies_file = cookies_file
        self._temp_dir.mkdir(parents=True, exist_ok=True)

    @property
    def temp_dir(self) -> Path:
        return self._temp_dir

    @property
    def max_file_size(self) -> int:
        return self._max_file_size

    def _get_yt_dlp_options(self, output_path: str) -> dict[str, Any]:
        """Get yt-dlp options for downloading."""
        max_size_mb = self._max_file_size // 1024 // 1024
        format_str = (
            f"best[ext=mp4][filesize<{max_size_mb}M]/"
            f"best[ext=mp4]/"
            f"best[filesize<{max_size_mb}M]/"
            f"best"
        )
        options: dict[str, Any] = {
            "format": format_str,
            "outtmpl": output_path,
            "restrictfilenames": True,
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False,
            "max_downloads": 1,
            "socket_timeout": 30,
        }
        if self._cookies_file:
            options["cookiefile"] = self._cookies_file
        return options

    async def download(self, url: str) -> DownloadResult:
        """
        Download video from URL.

        Args:
            url: Video URL (must be pre-validated).

        Returns:
            DownloadResult with file path and metadata.

        Raises:
            FileTooLargeError: If file exceeds size limit.
            VideoUnavailableError: If video is unavailable.
            DownloadError: If download fails.
        """
        unique_id = uuid.uuid4().hex[:8]
        output_path = str(self._temp_dir / f"video_{unique_id}.%(ext)s")
        options = self._get_yt_dlp_options(output_path)

        try:
            async with asyncio.timeout(self._timeout):
                with yt_dlp.YoutubeDL(options) as ydl:
                    info = await asyncio.to_thread(ydl.extract_info, url, download=True)

            if info is None:
                raise VideoUnavailableError("Could not download video")

            downloaded_file = self._find_downloaded_file(unique_id)
            if downloaded_file is None:
                raise DownloadError("Downloaded file not found")

            file_size = downloaded_file.stat().st_size
            if file_size > self._max_file_size:
                downloaded_file.unlink(missing_ok=True)
                raise FileTooLargeError(file_size, self._max_file_size)

            return DownloadResult(
                file_path=downloaded_file,
                title=info.get("title", "Unknown"),
                duration=info.get("duration"),
                file_size=file_size,
            )

        except TimeoutError as e:
            self._cleanup_partial_download(unique_id)
            raise DownloadError(f"Download timed out after {self._timeout} seconds") from e
        except FileTooLargeError, VideoUnavailableError, DownloadError:
            raise
        except yt_dlp.utils.DownloadError as e:
            error_msg = str(e).lower()
            if "private" in error_msg or "unavailable" in error_msg:
                raise VideoUnavailableError("Video is private or unavailable") from e
            raise DownloadError(f"Download failed: {e}") from e
        except Exception as e:
            raise DownloadError(f"Unexpected error during download: {e}") from e

    _TEMP_EXTENSIONS = frozenset({".part", ".ytdl", ".temp"})

    def _find_downloaded_file(self, unique_id: str) -> Path | None:
        """Find downloaded file by unique ID prefix, skipping temp files."""
        matches = [
            f
            for f in self._temp_dir.glob(f"video_{unique_id}.*")
            if f.suffix not in self._TEMP_EXTENSIONS
        ]
        return matches[0] if matches else None

    def _cleanup_partial_download(self, unique_id: str) -> None:
        """Clean up partial download files."""
        for file in self._temp_dir.glob(f"video_{unique_id}.*"):
            file.unlink(missing_ok=True)

    def cleanup_file(self, file_path: Path) -> None:
        """Clean up downloaded file."""
        file_path.unlink(missing_ok=True)
