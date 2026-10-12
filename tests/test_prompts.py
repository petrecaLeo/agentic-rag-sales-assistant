import pytest

from backend.assistant.profiles import PROFILES
from backend.prompts.assistant import ASSISTANT_PROMPTS, build_system


def test_every_profile_uses_an_existing_prompt():
    assert {profile.prompt for profile in PROFILES.values()} <= set(ASSISTANT_PROMPTS)


@pytest.mark.parametrize("version", sorted(ASSISTANT_PROMPTS))
@pytest.mark.parametrize("language", ["pt", "en"])
def test_every_version_fills_all_placeholders(version, language):
    system = build_system(language, version)

    assert "{" not in system and "}" not in system
