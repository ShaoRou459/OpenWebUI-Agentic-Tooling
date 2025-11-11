"""
Title: Image Generation Tool
Description: Generate images from text prompts using AI models
author: ShaoRou459
author_url: https://github.com/ShaoRou459
Version: 1.1.0
Requirements: open_webui
"""

import re
from typing import Any, Callable, Awaitable, Dict, Optional
from pydantic import BaseModel, Field

from open_webui.utils.chat import generate_chat_completion

# Import universal debug system
try:
    from universal_debug import UniversalDebug, retry_async
    DEBUG_AVAILABLE = True
except ImportError:
    DEBUG_AVAILABLE = False
    # Fallback debug class
    class UniversalDebug:
        def __init__(self, *args, **kwargs): pass
        def __getattr__(self, name): return lambda *args, **kwargs: None


class Tools:
    """Image Generation Tool for OpenWebUI"""

    class Valves(BaseModel):
        image_gen_model: str = Field(
            default="gpt-4o-image",
            description="The model to use for image generation (must support image generation)."
        )
        debug_enabled: bool = Field(
            default=False,
            description="Enable detailed debug logging."
        )
        max_retries: int = Field(
            default=3,
            description="Maximum number of retry attempts for failed operations."
        )
        retry_delay: float = Field(
            default=1.0,
            description="Initial delay in seconds before retrying failed operations."
        )

    def __init__(self):
        self.valves = self.Valves()
        self.debug = UniversalDebug(enabled=False, tool_name="ImageGen")

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
        # Update debug state
        self.debug.enabled = self.valves.debug_enabled

        if self.debug.enabled:
            self.debug.start_session(f"Image gen: {prompt[:50]}...")

        async def _status(desc: str, done: bool = False) -> None:
            if __event_emitter__:
                await __event_emitter__(
                    {"type": "status", "data": {"description": desc, "done": done}}
                )

        if not prompt or not prompt.strip():
            self.debug.error("Empty prompt provided")
            return "❌ Empty image prompt provided. Please provide a description of the image you want to generate."

        self.debug.info(f"Image prompt: {prompt[:100]}...")

        # Generate description if not provided
        if description is None:
            description = prompt[:50] + ("..." if len(prompt) > 50 else "")
            self.debug.info(f"Auto-generated description: {description}")

        await _status(f'Generating image: "{prompt[:60]}..."')

        try:
            # Call the image generation model with retry logic
            self.debug.info(f"Calling image generation model: {self.valves.image_gen_model}")

            async def _generate():
                with self.debug.timer("image_generation"):
                    return await generate_chat_completion(
                        request=__request__,
                        form_data={
                            "model": self.valves.image_gen_model,
                            "messages": [{"role": "user", "content": prompt}],
                            "stream": False,
                        },
                        user=__user__,
                    )

            resp = await retry_async(
                _generate,
                max_retries=self.valves.max_retries,
                initial_delay=self.valves.retry_delay,
                debug=self.debug,
                operation_name="image generation"
            )

            image_reply = resp["choices"][0]["message"]["content"].strip()
            self.debug.data("Model response", image_reply[:200])

            # Extract URL from response
            url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
            url_match = re.search(url_pattern, image_reply)

            if not url_match:
                await _status("", done=True)
                self.debug.error(f"No valid URL found in response: {image_reply[:100]}")

                if self.debug.enabled:
                    self.debug.metrics_summary()

                return f"❌ Image generation did not return a valid URL. Response: {image_reply[:200]}"

            image_url = url_match.group(0)
            self.debug.success(f"Image generated: {image_url}")

            await _status("✓ Image generated successfully", done=True)

            if self.debug.enabled:
                self.debug.metrics.llm_calls += 1
                self.debug.metrics_summary()

            # Return markdown-formatted image
            result = f"![{description}]({image_url})\n\n*{description}*"
            return result

        except Exception as e:
            await _status("", done=True)
            self.debug.error(f"Image generation failed: {str(e)}")

            if self.debug.enabled:
                self.debug.metrics_summary()

            return f"❌ Image generation failed: {str(e)}"
