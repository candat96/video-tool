import json
import openai

SYSTEM_PROMPT = """You are an expert film director and cinematographer specializing in wildlife/dinosaur documentaries.

Your job: Take a list of rough scene descriptions and produce consistent, detailed video generation prompts.

Rules:
1. Create a CHARACTER BIBLE describing every recurring subject (dinosaur, animal, environment) in precise visual detail:
   - Skin color, texture, scars, size, distinguishing features
   - Each subject must look IDENTICAL across all scenes
   - If there are multiple individuals of same species, differentiate them clearly

2. Create a STYLE GUIDE with consistent visual keywords (lighting, color grading, camera lens, film stock, mood).
   Use the user's style directive as base and expand it.

3. For each scene, write a detailed English prompt that:
   - Includes the subject description from the character bible (abbreviated but consistent)
   - Describes action, setting, camera movement precisely
   - Ends with style keywords from the style guide
   - Keeps under 800 characters (video AI prompt limit)

4. Add transition_hint for each scene describing the ending state (pose, direction, lighting)
   so the next scene can start consistently.

5. If input is not English, translate naturally to English.

6. Preserve the scene numbering exactly as given.

Output ONLY valid JSON (no markdown, no code fences):
{
  "character_bible": "full description string",
  "style_guide": "full style string",
  "scenes": [
    {
      "id": 1,
      "original": "user's original text",
      "enhanced_prompt": "detailed English prompt under 800 chars",
      "transition_hint": "ending state description"
    }
  ]
}"""


def enhance_prompts(api_key: str, scenes: list[dict], style_prefix: str = "",
                    model: str = "gpt-4o") -> dict:
    """
    Call ChatGPT to enhance scene prompts for consistency.

    Args:
        api_key: OpenAI API key
        scenes: list of {"id": int, "prompt": str}
        style_prefix: global style directive from user
        model: OpenAI model to use

    Returns:
        dict with character_bible, style_guide, scenes[]
    """
    client = openai.OpenAI(api_key=api_key)

    user_content = ""
    if style_prefix:
        user_content += f"GLOBAL STYLE DIRECTIVE: {style_prefix}\n\n"
    user_content += "SCENES:\n"
    for scene in scenes:
        user_content += f"Scene {scene['id']}: {scene['prompt']}\n"

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        temperature=0.7,
        max_tokens=16000,
        response_format={"type": "json_object"},
    )

    result_text = response.choices[0].message.content
    return json.loads(result_text)


def enhance_prompts_chunked(api_key: str, scenes: list[dict], style_prefix: str = "",
                            model: str = "gpt-4o", chunk_size: int = 15) -> dict:
    """
    For large scene lists (>15), split into chunks and process separately.
    First chunk establishes the character bible, subsequent chunks reuse it.
    """
    if len(scenes) <= chunk_size:
        return enhance_prompts(api_key, scenes, style_prefix, model)

    # Process first chunk to establish character bible
    first_chunk = scenes[:chunk_size]
    result = enhance_prompts(api_key, first_chunk, style_prefix, model)

    character_bible = result.get("character_bible", "")
    style_guide = result.get("style_guide", "")
    all_scenes = list(result.get("scenes", []))

    # Process remaining chunks with established bible
    for i in range(chunk_size, len(scenes), chunk_size):
        chunk = scenes[i:i + chunk_size]
        extended_style = (
            f"{style_prefix}\n\n"
            f"ESTABLISHED CHARACTER BIBLE (must follow exactly):\n{character_bible}\n\n"
            f"ESTABLISHED STYLE GUIDE (must follow exactly):\n{style_guide}"
        )
        chunk_result = enhance_prompts(api_key, chunk, extended_style, model)
        all_scenes.extend(chunk_result.get("scenes", []))

    result["scenes"] = all_scenes
    return result
