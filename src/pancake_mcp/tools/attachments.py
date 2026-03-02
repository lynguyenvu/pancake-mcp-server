"""MCP tools for handling file attachments from conversations."""

import json
from typing import Any
import aiohttp
from pathlib import Path
import tempfile
import os

from fastmcp import Context

from pancake_mcp.client import PancakeAPIError
from pancake_mcp.tools.common import fmt, get_chat_client


def register_attachment_tools(mcp: Any) -> None:
    """Register attachment handling tools onto the FastMCP instance."""

    @mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": True})
    async def list_message_attachments(
        ctx: Context,
        page_id: str,
        conversation_id: str,
        customer_id: str,
        message_index: int | None = None,
    ) -> str:
        """List all file attachments in a conversation or specific message.

        Args:
            page_id: Facebook page ID linked to your Pancake account.
            conversation_id: Conversation ID from list_conversations.
            customer_id: Customer ID to authenticate the request.
            message_index: Optional index of specific message to check (0-based).
                          If not provided, lists attachments from all messages.

        Returns:
            JSON list of attachments with type, URL, dimensions (for images), and download info.
        """
        try:
            async with get_chat_client() as c:
                # We need to call the messages endpoint directly to get full attachment data
                params = {"customer_id": customer_id, "page": 1, "page_size": 50}
                messages_data = await c._get(
                    f"/pages/{page_id}/conversations/{conversation_id}/messages",
                    params
                )

            if 'messages' not in messages_data:
                return "Error: No messages found in conversation."

            all_messages = messages_data['messages']

            if message_index is not None:
                # Get attachments from specific message only
                if message_index < 0 or message_index >= len(all_messages):
                    return f"Error: Message index {message_index} out of range (0-{len(all_messages)-1})."
                messages_to_check = [all_messages[message_index]]
            else:
                # Get attachments from all messages
                messages_to_check = all_messages

            attachments = []
            for msg_idx, message in enumerate(messages_to_check):
                msg_attachments = message.get('attachments', [])

                for att_idx, attachment in enumerate(msg_attachments):
                    att_info = {
                        "message_index": msg_idx if message_index is None else message_index,
                        "attachment_index": att_idx,
                        "type": attachment.get('type', 'unknown'),
                        "url": attachment.get('url'),
                        "name": attachment.get('name'),  # For files
                        "image_data": attachment.get('image_data'),  # For images
                    }

                    # Add extra info based on attachment type
                    if att_info['type'] == 'photo' and att_info['url']:
                        # Extract filename from URL
                        from urllib.parse import urlparse
                        parsed_url = urlparse(att_info['url'])
                        filename = Path(parsed_url.path).name
                        att_info['filename'] = filename
                        att_info['size_bytes'] = attachment.get('size_bytes')

                    attachments.append(att_info)

            return fmt({"attachments": attachments, "total_count": len(attachments)})

        except Exception as e:
            return f"Error listing attachments: {e}"

    @mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": True})
    async def download_attachment(
        ctx: Context,
        page_id: str,
        conversation_id: str,
        customer_id: str,
        message_index: int,
        attachment_index: int,
        download_dir: str = "./downloads",
    ) -> str:
        """Download a specific attachment from a conversation message.

        Args:
            page_id: Facebook page ID linked to your Pancake account.
            conversation_id: Conversation ID from list_conversations.
            customer_id: Customer ID to authenticate the request.
            message_index: Index of the message containing the attachment (0-based).
            attachment_index: Index of the attachment in the message (0-based).
            download_dir: Directory to save the downloaded file (default: ./downloads).

        Returns:
            JSON with download status, file path, and file info.
        """
        try:
            # First, get the attachment info
            attachments_result_str = await list_message_attachments(
                ctx, page_id, conversation_id, customer_id, message_index
            )

            attachments_result = json.loads(attachments_result_str)

            if 'attachments' not in attachments_result:
                return f"Error: Could not get attachment info: {attachments_result_str}"

            # Find the specific attachment
            target_attachment = None
            for att in attachments_result['attachments']:
                if att['message_index'] == message_index and att['attachment_index'] == attachment_index:
                    target_attachment = att
                    break

            if not target_attachment:
                return f"Error: Attachment at message {message_index}, index {attachment_index} not found."

            attachment_url = target_attachment.get('url')
            if not attachment_url:
                return f"Error: No download URL found for attachment {message_index}:{attachment_index}."

            # Create download directory
            download_path = Path(download_dir)
            download_path.mkdir(parents=True, exist_ok=True)

            # Determine filename
            from urllib.parse import urlparse
            parsed_url = urlparse(attachment_url)
            original_filename = Path(parsed_url.path).name

            # If we couldn't get filename from URL, construct it
            if not original_filename or '.' not in original_filename:
                file_type = target_attachment.get('type', 'file')
                original_filename = f"attachment_msg{message_index}_att{attachment_index}.{file_type}"

            file_path = download_path / original_filename

            # Download the file
            async with aiohttp.ClientSession() as session:
                async with session.get(attachment_url) as response:
                    if response.status != 200:
                        return f"Error: Could not download file, status {response.status}."

                    with open(file_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            f.write(chunk)

            # Get file stats
            stat = file_path.stat()

            result = {
                "status": "success",
                "download_path": str(file_path.absolute()),
                "original_filename": original_filename,
                "file_size_bytes": stat.st_size,
                "attachment_info": target_attachment
            }

            return fmt(result)

        except Exception as e:
            return f"Error downloading attachment: {e}"

    @mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": True})
    async def preview_attachment_content(
        ctx: Context,
        page_id: str,
        conversation_id: str,
        customer_id: str,
        message_index: int,
        attachment_index: int,
        preview_size: int = 1024,
    ) -> str:
        """Preview content of an attachment without fully downloading it.

        Args:
            page_id: Facebook page ID linked to your Pancake account.
            conversation_id: Conversation ID from list_conversations.
            customer_id: Customer ID to authenticate the request.
            message_index: Index of the message containing the attachment (0-based).
            attachment_index: Index of the attachment in the message (0-based).
            preview_size: Size of content preview in bytes (default 1024).

        Returns:
            JSON with file info and content preview.
        """
        try:
            # First, get the attachment info
            attachments_result_str = await list_message_attachments(
                ctx, page_id, conversation_id, customer_id, message_index
            )

            attachments_result = json.loads(attachments_result_str)

            if 'attachments' not in attachments_result:
                return f"Error: Could not get attachment info: {attachments_result_str}"

            # Find the specific attachment
            target_attachment = None
            for att in attachments_result['attachments']:
                if att['message_index'] == message_index and att['attachment_index'] == attachment_index:
                    target_attachment = att
                    break

            if not target_attachment:
                return f"Error: Attachment at message {message_index}, index {attachment_index} not found."

            attachment_url = target_attachment.get('url')
            if not attachment_url:
                return f"Error: No download URL found for attachment {message_index}:{attachment_index}."

            # Download only a portion of the file using range request
            async with aiohttp.ClientSession() as session:
                headers = {'Range': f'bytes=0-{preview_size-1}'}
                async with session.get(attachment_url, headers=headers) as response:
                    if response.status in [200, 206]:  # 206: Partial Content
                        preview_content = await response.read()

                        # Determine file type and handle accordingly
                        file_type = target_attachment.get('type', 'unknown')
                        content_str = ""

                        try:
                            # Try to decode as text if it's a text-based file
                            if file_type in ['document', 'text', 'pdf', 'doc', 'docx', 'txt', 'csv', 'json', 'xml']:
                                content_str = preview_content.decode('utf-8', errors='ignore')
                            else:
                                content_str = f"<Binary file preview - {len(preview_content)} bytes>"
                        except UnicodeDecodeError:
                            content_str = f"<Binary file preview - {len(preview_content)} bytes>"

                        result = {
                            "status": "success",
                            "file_info": target_attachment,
                            "preview_content": content_str,
                            "preview_size": len(preview_content),
                            "full_content_available": len(preview_content) == preview_size,
                            "message": "Use download_attachment to get full file if needed"
                        }
                        return fmt(result)
                    else:
                        return f"Error: Could not preview file, status {response.status}"

        except Exception as e:
            return f"Error previewing attachment content: {e}"

    @mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": True})
    async def extract_text_from_image(
        ctx: Context,
        page_id: str,
        conversation_id: str,
        customer_id: str,
        message_index: int,
        attachment_index: int,
    ) -> str:
        """Extract text from an image attachment using OCR.

        Args:
            page_id: Facebook page ID linked to your Pancake account.
            conversation_id: Conversation ID from list_conversations.
            customer_id: Customer ID to authenticate the request.
            message_index: Index of the message containing the attachment (0-based).
            attachment_index: Index of the attachment in the message (0-based).

        Returns:
            JSON with extracted text and confidence level.
        """
        try:
            # Import OCR libraries (only when needed to avoid import errors if not installed)
            try:
                from PIL import Image
                import pytesseract
            except ImportError:
                return "Error: OCR libraries not available. Please install Pillow and pytesseract."

            # First download the image temporarily
            with tempfile.TemporaryDirectory() as temp_dir:
                download_result_str = await download_attachment(
                    ctx, page_id, conversation_id, customer_id,
                    message_index, attachment_index, temp_dir
                )

                download_result = json.loads(download_result_str)

                if download_result.get("status") != "success":
                    return f"Error downloading image for OCR: {download_result_str}"

                image_path = download_result.get("download_path")

                # Open and process the image
                img = Image.open(image_path)

                # Extract text using OCR
                extracted_text = pytesseract.image_to_string(img, lang='vie+eng')

                # Get more detailed information
                data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)

                # Calculate confidence level
                confidences = [int(conf) for conf in data['conf'] if int(conf) != -1]
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0

                result = {
                    "status": "success",
                    "extracted_text": extracted_text.strip(),
                    "confidence_level": avg_confidence,
                    "word_count": len(extracted_text.split()),
                    "attachment_info": download_result.get("attachment_info"),
                    "language": "vie+eng"  # Vietnamese + English
                }

                return fmt(result)

        except Exception as e:
            return f"Error extracting text from image: {e}"

    @mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": True})
    async def analyze_image_content(
        ctx: Context,
        page_id: str,
        conversation_id: str,
        customer_id: str,
        message_index: int,
        attachment_index: int,
    ) -> str:
        """Analyze image content and provide a description.

        Args:
            page_id: Facebook page ID linked to your Pancake account.
            conversation_id: Conversation ID from list_conversations.
            customer_id: Customer ID to authenticate the request.
            message_index: Index of the message containing the attachment (0-based).
            attachment_index: Index of the attachment in the message (0-based).

        Returns:
            JSON with image analysis and description.
        """
        try:
            # Import image processing libraries
            try:
                from PIL import Image
                import pytesseract
                import cv2
                import numpy as np
            except ImportError:
                return "Error: Image analysis libraries not available. Please install Pillow, opencv-python, and pytesseract."

            # First download the image temporarily
            with tempfile.TemporaryDirectory() as temp_dir:
                download_result_str = await download_attachment(
                    ctx, page_id, conversation_id, customer_id,
                    message_index, attachment_index, temp_dir
                )

                download_result = json.loads(download_result_str)

                if download_result.get("status") != "success":
                    return f"Error downloading image for analysis: {download_result_str}"

                image_path = download_result.get("download_path")

                # Open and analyze the image
                img_pil = Image.open(image_path)

                # Get basic image properties
                width, height = img_pil.size
                mode = img_pil.mode
                format = img_pil.format

                # Convert to OpenCV format for analysis
                img_cv = cv2.imread(image_path)

                # Extract text if present (using OCR)
                extracted_text = pytesseract.image_to_string(img_pil, lang='vie+eng').strip()

                # Basic analysis
                analysis = {
                    "dimensions": {"width": width, "height": height},
                    "color_mode": mode,
                    "format": format,
                    "has_text": bool(extracted_text),
                    "text_content": extracted_text if extracted_text else None,
                    "approximate_size_category": "small" if width * height < 500000 else "medium" if width * height < 2000000 else "large",
                    "attachment_info": download_result.get("attachment_info")
                }

                result = {
                    "status": "success",
                    "analysis": analysis,
                    "summary": f"Image is {width}x{height} pixels, {mode} mode, {'with text' if extracted_text else 'without detectable text'}"
                }

                return fmt(result)

        except Exception as e:
            return f"Error analyzing image content: {e}"

    @mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": True})
    async def detect_objects_in_image(
        ctx: Context,
        page_id: str,
        conversation_id: str,
        customer_id: str,
        message_index: int,
        attachment_index: int,
    ) -> str:
        """Detect objects in an image attachment.

        Args:
            page_id: Facebook page ID linked to your Pancake account.
            conversation_id: Conversation ID from list_conversations.
            customer_id: Customer ID to authenticate the request.
            message_index: Index of the message containing the attachment (0-based).
            attachment_index: Index of the attachment in the message (0-based).

        Returns:
            JSON with detected objects and their locations.
        """
        try:
            # Import image processing libraries
            try:
                from PIL import Image
                import cv2
                import numpy as np
            except ImportError:
                return "Error: Object detection libraries not available. Please install Pillow and opencv-python."

            # First download the image temporarily
            with tempfile.TemporaryDirectory() as temp_dir:
                download_result_str = await download_attachment(
                    ctx, page_id, conversation_id, customer_id,
                    message_index, attachment_index, temp_dir
                )

                download_result = json.loads(download_result_str)

                if download_result.get("status") != "success":
                    return f"Error downloading image for object detection: {download_result_str}"

                image_path = download_result.get("download_path")

                # Load image for object detection
                img = cv2.imread(image_path)
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

                # Simple detection methods (basic implementation)
                # In a real implementation, you'd use a model like YOLO or SSD
                detected_objects = []

                # For now, we'll implement some basic detection patterns
                # Detect edges (might indicate objects)
                edges = cv2.Canny(gray, 50, 150)

                # Find contours (potential objects)
                contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                # Count significant contours (objects)
                significant_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > 100]  # Only large contours

                # Basic object detection based on common patterns
                # This is a simplified version - in practice, you'd use a trained model
                for i, contour in enumerate(significant_contours[:5]):  # Limit to first 5
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = float(w) / h

                    obj_info = {
                        "id": i + 1,
                        "position": {"x": x, "y": y, "width": w, "height": h},
                        "area": cv2.contourArea(contour),
                        "aspect_ratio": round(aspect_ratio, 2),
                        "type": "object"
                    }

                    # Try to classify based on shape
                    if 0.8 <= aspect_ratio <= 1.2:
                        obj_info["type"] = "square_object"
                    elif aspect_ratio < 0.8:
                        obj_info["type"] = "vertical_object"
                    else:
                        obj_info["type"] = "horizontal_object"

                    detected_objects.append(obj_info)

                result = {
                    "status": "success",
                    "detected_objects_count": len(detected_objects),
                    "detected_objects": detected_objects,
                    "image_analysis": {
                        "total_contours_found": len(contours),
                        "significant_objects": len(significant_contours),
                        "threshold_used": 100  # Area threshold
                    },
                    "attachment_info": download_result.get("attachment_info")
                }

                return fmt(result)

        except Exception as e:
            return f"Error detecting objects in image: {e}"