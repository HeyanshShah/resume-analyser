"""Optional: rewrite weak bullets with Claude (Anthropic API).

Off by default. Set ANTHROPIC_API_KEY (and optionally ANTHROPIC_MODEL) to enable.
The prompt forbids inventing facts: missing numbers become [placeholders] for the
user to fill in, so the tool never fabricates achievements.
"""
import json
import os

DEFAULT_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5-5")

PROMPT = """You are an expert technical resume editor. Rewrite each bullet so it:
- starts with a strong past-tense action verb (present tense if the role is current),
- uses active voice and no pronouns,
- is 12-28 words,
- weaves in these job keywords ONLY where the original already supports them: {keywords}.
Never invent facts, tools, or numbers. Where impact is missing, insert a placeholder such
as [X%] or [N users] for the candidate to fill in.
Return ONLY a JSON list of strings, same order and length as the input.

Bullets:
{bullets}"""


def available() -> bool:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return False
    try:
        import anthropic  # noqa: F401
    except ImportError:
        return False
    return True


def rewrite_bullets(bullets: list[str], keywords: list[str], model: str = DEFAULT_MODEL) -> list[str]:
    import anthropic
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model=model, max_tokens=2000,
        messages=[{"role": "user", "content": PROMPT.format(
            keywords=", ".join(keywords) or "(none)",
            bullets=json.dumps(bullets, indent=1))}],
    )
    text = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text").strip()
    start, end = text.find("["), text.rfind("]")
    out = json.loads(text[start:end + 1])
    if len(out) != len(bullets):
        raise ValueError("model returned a different number of bullets")
    return out
