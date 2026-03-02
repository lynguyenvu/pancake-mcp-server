"""MCP tools for handling file attachments from conversations."""

import json
from typing import Any
import aiohttp
from pathlib import Path

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