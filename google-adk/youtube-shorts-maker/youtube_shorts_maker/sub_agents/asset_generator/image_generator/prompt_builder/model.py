from typing import List

from pydantic import BaseModel, Field


class OptimizedPrompt(BaseModel):
    scene_id: int = Field(description="Scene ID from the original content plan")
    enhanced_prompt: str = Field(
        description="Detailed prompt with technical specs and text overlay instructions for vertical YouTube Shorts"
    )


class PromptBuilderOutput(BaseModel):
    optimized_prompts: List[OptimizedPrompt] = Field(
        description="Array of optimized image generation prompts for vertical YouTube Shorts"
    )
