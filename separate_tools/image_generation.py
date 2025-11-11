"""
Title: Image Generation Tool
Description: Generate images from text prompts using AI models
author: ShaoRou459
author_url: https://github.com/ShaoRou459
Version: 1.0.0
Requirements: open_webui
"""

import re
from typing import Any, Callable, Awaitable, Dict, Optional
from pydantic import BaseModel, Field

from open_webui.utils.chat import generate_chat_completion


class Tools:
    """Image Generation Tool for OpenWebUI"""

    class Valves(BaseModel):
        image_gen_model: str = Field(
            default="gpt-4o-image",
            description="The model to use for image generation (must support image generation)."
        )

    def __init__(self):
        self.valves = self.Valves()

    async def generate_image(
        self,
        prompt: str,
        description: str = None,
        __event_emitter__: Optional[Callable[[dict], Awaitable[None]]] = None,
        __request__: Optional[Any] = None,
        __user__: Optional[Dict] = None,
    ) -> str:
        """
        Generate an image from a text prompt.

        Args:
            prompt: Detailed description of the image to generate (be specific and descriptive)
            description: Short caption/description for the image (optional, will be auto-generated if not provided)
            __event_emitter__: OpenWebUI event emitter for status updates
            __request__: Request object from OpenWebUI
            __user__: User object from OpenWebUI

        Returns:
            Markdown-formatted image with URL and caption

        Examples:
            # With custom description:
            await generate_image(
                prompt="A serene mountain landscape at sunset with purple and orange skies, reflecting on a calm lake",
                description="Mountain sunset reflection"
            )

            # Auto-generated description:
            await generate_image(
                prompt="A futuristic city with flying cars and neon lights"
            )
        """
        async def _status(desc: str, done: bool = False) -> None:
            if __event_emitter__:
                await __event_emitter__(
                    {"type": "status", "data": {"description": desc, "done": done}}
                )

        if not prompt or not prompt.strip():
            return "❌ Empty image prompt provided. Please provide a description of the image you want to generate."

        # Generate description if not provided
        if description is None:
            description = prompt[:50] + ("..." if len(prompt) > 50 else "")

        await _status(f'Generating image: "{prompt[:60]}..."')

        try:
            # Call the image generation model
            resp = await generate_chat_completion(
                request=__request__,
                form_data={
                    "model": self.valves.image_gen_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False,
                },
                user=__user__,
            )

            image_reply = resp["choices"][0]["message"]["content"].strip()

            # Extract URL from response
            url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
            url_match = re.search(url_pattern, image_reply)

            if not url_match:
                await _status("", done=True)
                return f"❌ Image generation did not return a valid URL. Response: {image_reply[:200]}"

            image_url = url_match.group(0)

            await _status("✓ Image generated successfully", done=True)

            # Return markdown-formatted image
            return f"![{description}]({image_url})\n\n*{description}*"

        except Exception as e:
            await _status("", done=True)
            return f"❌ Image generation failed: {str(e)}"
