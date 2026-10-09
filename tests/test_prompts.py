import pytest

from backend.prompts.assistant import ACTIVE_VERSION, ASSISTANT_PROMPTS, build_system


def test_active_version_exists():
    assert ACTIVE_VERSION in ASSISTANT_PROMPTS


@pytest.mark.parametrize("version", sorted(ASSISTANT_PROMPTS))
@pytest.mark.parametrize("language", ["pt", "en"])
def test_every_version_fills_all_placeholders(version, language):
    system = build_system(language, version)

    assert "{" not in system and "}" not in system
