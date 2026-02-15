"""Binary handling utility for file import/export, images, and attachments."""

from __future__ import annotations

import base64
import mimetypes
import os
from typing import Any


def encode_file(file_path: str) -> dict[str, Any]:
    """Read a local file and return its base64-encoded content with metadata.

    Args:
        file_path: Absolute path to the file.
    """
    if not os.path.isfile(file_path):
        return {"error": f"File not found: {file_path}"}

    mime_type, _ = mimetypes.guess_type(file_path)
    with open(file_path, "rb") as f:
        data = f.read()

    return {
        "filename": os.path.basename(file_path),
        "size_bytes": len(data),
        "mime_type": mime_type or "application/octet-stream",
        "base64": base64.b64encode(data).decode("ascii"),
    }


def decode_to_file(
    base64_data: str,
    output_path: str,
    filename: str | None = None,
) -> dict[str, Any]:
    """Decode a base64 string and save it to a file.

    Args:
        base64_data: Base64-encoded file content.
        output_path: Directory to save the file.
        filename: Optional filename (generated if not provided).
    """
    try:
        data = base64.b64decode(base64_data)
    except Exception as e:
        return {"error": f"Invalid base64 data: {e}"}

    os.makedirs(output_path, exist_ok=True)
    fname = filename or "decoded_file"
    full_path = os.path.join(output_path, fname)

    with open(full_path, "wb") as f:
        f.write(data)

    return {
        "path": full_path,
        "filename": fname,
        "size_bytes": len(data),
    }


def csv_to_import_data(csv_content: str) -> dict[str, Any]:
    """Parse CSV content into Odoo import-compatible format.

    Returns headers and rows suitable for the /base_import endpoint.
    """
    import csv
    import io

    reader = csv.reader(io.StringIO(csv_content))
    rows = list(reader)

    if not rows:
        return {"error": "Empty CSV data."}

    return {
        "headers": rows[0],
        "rows": rows[1:],
        "row_count": len(rows) - 1,
    }


def format_file_size(size_bytes: int) -> str:
    """Format bytes into human-readable size."""
    for unit in ("B", "KB", "MB", "GB"):
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"
