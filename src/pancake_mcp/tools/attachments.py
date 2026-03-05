"""MCP tools for handling file attachments from conversations."""

import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import aiohttp

from pancake_mcp.deps import get_access_token
from pancake_mcp.tools.common import MAX_PAGE_SIZE, fmt, get_chat_client

OCR_LANGUAGES = "vie+eng"


def _auth_headers() -> dict[str, str]:
    """Build auth headers for direct URL fetches."""
    try:
        return {"Authorization": f"Bearer {get_access_token()}"}
    except ValueError:
        return {}


async def _fetch_image_to_temp(
    page_id: str,
    conversation_id: str,
    customer_id: str,
    message_index: int,
    attachment_index: int,
    temp_dir: str,
) -> tuple[str | None, dict[str, Any] | None, str | None]:
    """Fetch an image attachment directly to a temp directory (no path validation).

    Returns (file_path, attachment_info, None) on success, or (None, None, error_string).
    """
    attachment, err = await _find_attachment(
        page_id, conversation_id, customer_id, message_index, attachment_index,
    )
    if err:
        return None, None, err

    url = attachment.get('url')
    if not url:
        return None, None, f"Error: No URL for attachment {message_index}:{attachment_index}."

    parsed = urlparse(url)
    filename = Path(parsed.path).name or f"attachment_{message_index}_{attachment_index}"
    file_path = Path(temp_dir) / _sanitize_filename(filename)

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=_auth_headers()) as resp:
            if resp.status != 200:
                return None, None, f"Error: Could not fetch image, status {resp.status}."
            with open(file_path, 'wb') as f:
                async for chunk in resp.content.iter_chunked(8192):
                    f.write(chunk)

    return str(file_path), attachment, None


def _is_safe_path(base_path: Path, target_path: Path, follow_symlinks: bool = False) -> bool:
    """Check if a target path is safe to access from within a base path."""
    try:
        base_resolved = base_path.resolve()
        if follow_symlinks:
            target_resolved = target_path.resolve()
        else:
            target_resolved = target_path.absolute()
        target_resolved.relative_to(base_resolved)
        return True
    except ValueError:
        return False


def _sanitize_filename(filename: str) -> str:
    """Sanitize a filename to prevent directory traversal and other security issues."""
    filename = re.sub(r'\.\.\/', '', filename)
    filename = re.sub(r'\.\.\\', '', filename)
    filename = Path(filename).name
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    if not filename or filename in ('.', '..'):
        filename = 'unnamed_file'
    return filename


def _get_allowed_download_paths() -> list[Path]:
    """Get list of allowed download paths from environment variables or default."""
    allowed_paths = [Path('./downloads').resolve()]
    env_paths = os.getenv('ALLOWED_DOWNLOAD_PATHS', '')
    if env_paths:
        for path_str in env_paths.split(':'):
            path_str = path_str.strip()
            if path_str:
                try:
                    allowed_paths.append(Path(path_str).resolve())
                except Exception:
                    continue
    return allowed_paths


async def _find_attachment(
    page_id: str,
    conversation_id: str,
    customer_id: str,
    message_index: int,
    attachment_index: int,
) -> tuple[dict[str, Any] | None, str | None]:
    """Look up a specific attachment from a conversation.

    Returns (attachment_dict, None) on success, or (None, error_string) on failure.
    """
    try:
        async with get_chat_client() as c:
            params = {"customer_id": customer_id, "page": 1, "page_size": MAX_PAGE_SIZE}
            messages_data = await c._get(
                f"/pages/{page_id}/conversations/{conversation_id}/messages",
                params,
            )
    except Exception as e:
        return None, f"Error fetching messages: {e}"

    if 'messages' not in messages_data:
        return None, "Error: No messages found in conversation."

    all_messages = messages_data['messages']
    if message_index < 0 or message_index >= len(all_messages):
        return None, f"Error: Message index {message_index} out of range (0-{len(all_messages)-1})."

    message = all_messages[message_index]
    msg_attachments = message.get('attachments', [])

    if attachment_index < 0 or attachment_index >= len(msg_attachments):
        return None, f"Error: Attachment index {attachment_index} out of range (0-{len(msg_attachments)-1})."

    attachment = msg_attachments[attachment_index]
    att_info: dict[str, Any] = {
        "message_index": message_index,
        "attachment_index": attachment_index,
        "type": attachment.get('type', 'unknown'),
        "url": attachment.get('url'),
        "name": attachment.get('name'),
        "image_data": attachment.get('image_data'),
    }

    if att_info['type'] == 'photo' and att_info['url']:
        parsed_url = urlparse(att_info['url'])
        att_info['filename'] = Path(parsed_url.path).name
        att_info['size_bytes'] = attachment.get('size_bytes')

    return att_info, None


def register_attachment_tools(mcp: Any) -> None:
    """Register attachment handling tools onto the FastMCP instance."""

    @mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": True})
    async def list_message_attachments(
        page_id: str,
        conversation_id: str,
        customer_id: str,
        message_index: int | None = None,
    ) -> str:
        """List all file attachments in a conversation or specific message.

        Args:
            page_id: Pancake page ID (represents a connected channel).
            conversation_id: Conversation ID from list_conversations.
            customer_id: Customer ID to authenticate the request.
            message_index: Optional index of specific message to check (0-based).
                          If not provided, lists attachments from all messages.

        Returns:
            JSON list of attachments with type, URL, dimensions (for images), and download info.
        """
        try:
            async with get_chat_client() as c:
                params = {"customer_id": customer_id, "page": 1, "page_size": MAX_PAGE_SIZE}
                messages_data = await c._get(
                    f"/pages/{page_id}/conversations/{conversation_id}/messages",
                    params,
                )

            if 'messages' not in messages_data:
                return "Error: No messages found in conversation."

            all_messages = messages_data['messages']

            if message_index is not None:
                if message_index < 0 or message_index >= len(all_messages):
                    return f"Error: Message index {message_index} out of range (0-{len(all_messages)-1})."
                messages_to_check = [all_messages[message_index]]
            else:
                messages_to_check = all_messages

            attachments = []
            for msg_idx, message in enumerate(messages_to_check):
                for att_idx, attachment in enumerate(message.get('attachments', [])):
                    att_info: dict[str, Any] = {
                        "message_index": msg_idx if message_index is None else message_index,
                        "attachment_index": att_idx,
                        "type": attachment.get('type', 'unknown'),
                        "url": attachment.get('url'),
                        "name": attachment.get('name'),
                        "image_data": attachment.get('image_data'),
                    }
                    if att_info['type'] == 'photo' and att_info['url']:
                        parsed_url = urlparse(att_info['url'])
                        att_info['filename'] = Path(parsed_url.path).name
                        att_info['size_bytes'] = attachment.get('size_bytes')
                    attachments.append(att_info)

            return fmt({"attachments": attachments, "total_count": len(attachments)})

        except Exception as e:
            return f"Error listing attachments: {e}"

    @mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": True})
    async def download_attachment(
        page_id: str,
        conversation_id: str,
        customer_id: str,
        message_index: int,
        attachment_index: int,
        download_dir: str = "./downloads",
    ) -> str:
        """Download a specific attachment from a conversation message.

        Args:
            page_id: Pancake page ID (represents a connected channel).
            conversation_id: Conversation ID from list_conversations.
            customer_id: Customer ID to authenticate the request.
            message_index: Index of the message containing the attachment (0-based).
            attachment_index: Index of the attachment in the message (0-based).
            download_dir: Directory to save the downloaded file (default: ./downloads).
                         Can be a mounted directory from the host system.

        Returns:
            JSON with download status, file path, and file info.
        """
        try:
            target_attachment, err = await _find_attachment(
                page_id, conversation_id, customer_id, message_index, attachment_index,
            )
            if err:
                return err

            attachment_url = target_attachment.get('url')
            if not attachment_url:
                return f"Error: No download URL found for attachment {message_index}:{attachment_index}."

            # Validate download directory
            download_path = Path(download_dir).resolve()
            allowed_paths = _get_allowed_download_paths()
            if not any(
                _is_safe_path(ap, download_path) or download_path == ap
                for ap in allowed_paths
            ):
                return f"Error: Download directory '{download_dir}' is not in allowed paths. Allowed paths: {[str(p) for p in allowed_paths]}"

            download_path.mkdir(parents=True, exist_ok=True)
            if not os.access(download_path, os.W_OK):
                return f"Error: No write permissions for directory '{download_dir}'."

            # Determine and sanitize filename
            parsed_url = urlparse(attachment_url)
            original_filename = Path(parsed_url.path).name
            if not original_filename or '.' not in original_filename:
                file_type = target_attachment.get('type', 'file')
                original_filename = f"attachment_msg{message_index}_att{attachment_index}.{file_type}"

            sanitized_filename = _sanitize_filename(original_filename)
            file_path = download_path / sanitized_filename

            if not _is_safe_path(download_path, file_path):
                return "Error: Invalid file path construction - path traversal detected."

            headers = _auth_headers()

            async with aiohttp.ClientSession() as session:
                async with session.get(attachment_url, headers=headers) as response:
                    if response.status != 200:
                        return f"Error: Could not download file, status {response.status}."
                    with open(file_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            f.write(chunk)

            stat = file_path.stat()
            return fmt({
                "status": "success",
                "download_path": str(file_path.absolute()),
                "original_filename": original_filename,
                "sanitized_filename": sanitized_filename,
                "file_size_bytes": stat.st_size,
                "attachment_info": target_attachment,
            })

        except Exception as e:
            return f"Error downloading attachment: {e}"

    @mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": True})
    async def preview_attachment_content(
        page_id: str,
        conversation_id: str,
        customer_id: str,
        message_index: int,
        attachment_index: int,
        preview_size: int = 1024,
    ) -> str:
        """Preview content of an attachment without fully downloading it.

        Args:
            page_id: Pancake page ID (represents a connected channel).
            conversation_id: Conversation ID from list_conversations.
            customer_id: Customer ID to authenticate the request.
            message_index: Index of the message containing the attachment (0-based).
            attachment_index: Index of the attachment in the message (0-based).
            preview_size: Size of content preview in bytes (default 1024).

        Returns:
            JSON with file info and content preview.
        """
        try:
            target_attachment, err = await _find_attachment(
                page_id, conversation_id, customer_id, message_index, attachment_index,
            )
            if err:
                return err

            attachment_url = target_attachment.get('url')
            if not attachment_url:
                return f"Error: No download URL found for attachment {message_index}:{attachment_index}."

            headers = {**_auth_headers(), 'Range': f'bytes=0-{preview_size-1}'}

            async with aiohttp.ClientSession() as session:
                async with session.get(attachment_url, headers=headers) as response:
                    if response.status not in (200, 206):
                        return f"Error: Could not preview file, status {response.status}"

                    preview_content = await response.read()
                    file_type = target_attachment.get('type', 'unknown')

                    try:
                        if file_type in ('document', 'text', 'pdf', 'doc', 'docx', 'txt', 'csv', 'json', 'xml'):
                            content_str = preview_content.decode('utf-8', errors='ignore')
                        else:
                            content_str = f"<Binary file preview - {len(preview_content)} bytes>"
                    except UnicodeDecodeError:
                        content_str = f"<Binary file preview - {len(preview_content)} bytes>"

                    return fmt({
                        "status": "success",
                        "file_info": target_attachment,
                        "preview_content": content_str,
                        "preview_size": len(preview_content),
                        "full_content_available": len(preview_content) == preview_size,
                        "message": "Use download_attachment to get full file if needed",
                    })

        except Exception as e:
            return f"Error previewing attachment content: {e}"

    @mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": True})
    async def extract_text_from_image(
        page_id: str,
        conversation_id: str,
        customer_id: str,
        message_index: int,
        attachment_index: int,
    ) -> str:
        """Extract text from an image attachment using OCR.

        Args:
            page_id: Pancake page ID (represents a connected channel).
            conversation_id: Conversation ID from list_conversations.
            customer_id: Customer ID to authenticate the request.
            message_index: Index of the message containing the attachment (0-based).
            attachment_index: Index of the attachment in the message (0-based).

        Returns:
            JSON with extracted text and confidence level.
        """
        try:
            try:
                from PIL import Image
                import pytesseract
            except ImportError:
                return "Error: OCR libraries not available. Please install Pillow and pytesseract."

            with tempfile.TemporaryDirectory() as temp_dir:
                image_path, att_info, err = await _fetch_image_to_temp(
                    page_id, conversation_id, customer_id,
                    message_index, attachment_index, temp_dir,
                )
                if err:
                    return err

                img = Image.open(image_path)
                extracted_text = pytesseract.image_to_string(img, lang=OCR_LANGUAGES)
                data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)

                confidences = [int(conf) for conf in data['conf'] if int(conf) != -1]
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0

                return fmt({
                    "status": "success",
                    "extracted_text": extracted_text.strip(),
                    "confidence_level": avg_confidence,
                    "word_count": len(extracted_text.split()),
                    "attachment_info": att_info,
                    "language": OCR_LANGUAGES,
                })

        except Exception as e:
            return f"Error extracting text from image: {e}"

    @mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": True})
    async def analyze_image_content(
        page_id: str,
        conversation_id: str,
        customer_id: str,
        message_index: int,
        attachment_index: int,
    ) -> str:
        """Analyze image content and provide a description.

        Args:
            page_id: Pancake page ID (represents a connected channel).
            conversation_id: Conversation ID from list_conversations.
            customer_id: Customer ID to authenticate the request.
            message_index: Index of the message containing the attachment (0-based).
            attachment_index: Index of the attachment in the message (0-based).

        Returns:
            JSON with image analysis and description.
        """
        try:
            try:
                from PIL import Image
                import pytesseract
            except ImportError:
                return "Error: Image analysis libraries not available. Please install Pillow and pytesseract."

            with tempfile.TemporaryDirectory() as temp_dir:
                image_path, att_info, err = await _fetch_image_to_temp(
                    page_id, conversation_id, customer_id,
                    message_index, attachment_index, temp_dir,
                )
                if err:
                    return err

                img_pil = Image.open(image_path)
                width, height = img_pil.size
                mode = img_pil.mode
                img_format = img_pil.format

                extracted_text = pytesseract.image_to_string(img_pil, lang=OCR_LANGUAGES).strip()

                analysis = {
                    "dimensions": {"width": width, "height": height},
                    "color_mode": mode,
                    "format": img_format,
                    "has_text": bool(extracted_text),
                    "text_content": extracted_text if extracted_text else None,
                    "approximate_size_category": (
                        "small" if width * height < 500000
                        else "medium" if width * height < 2000000
                        else "large"
                    ),
                    "attachment_info": att_info,
                }

                return fmt({
                    "status": "success",
                    "analysis": analysis,
                    "summary": f"Image is {width}x{height} pixels, {mode} mode, {'with text' if extracted_text else 'without detectable text'}",
                })

        except Exception as e:
            return f"Error analyzing image content: {e}"
