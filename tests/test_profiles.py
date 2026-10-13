from backend.assistant.params import assistant_params
from backend.assistant.profiles import ACTIVE_PROFILE, PROFILES
from backend.config import SONNET


def test_active_profile_exists():
    assert ACTIVE_PROFILE in PROFILES


def test_base_is_the_v1_setup():
    params = assistant_params([{"role": "user", "content": "oi"}], "pt", PROFILES["base"])

    assert params["model"] == SONNET and params["max_tokens"] == 500
    assert params["thinking"] == {"type": "between_tools"}
    assert params["output_config"] == {"effort": "low"}
    assert "cache_control" not in params and isinstance(params["system"], str)


def test_cache_marks_the_shared_prefix_and_the_end_of_the_conversation():
    params = assistant_params([{"role": "user", "content": "oi"}], "pt", PROFILES["cache"])
    base = assistant_params([{"role": "user", "content": "oi"}], "pt", PROFILES["base"])

    assert params["system"] == [{"type": "text", "text": base["system"], "cache_control": {"type": "ephemeral"}}]
    assert params["cache_control"] == {"type": "ephemeral"}
    assert {k: v for k, v in params.items() if k not in ("system", "cache_control")} == \
           {k: v for k, v in base.items() if k != "system"}


def test_haiku_profiles_think_adaptively_with_room_and_keep_cache_and_router():
    from backend.config import HAIKU

    for effort in ("low", "medium", "high"):
        profile = PROFILES[f"haiku-{effort}"]
        params = assistant_params([{"role": "user", "content": "oi"}], "pt", profile)
        assert params["model"] == HAIKU and params["thinking"] == {"type": "adaptive"}
        assert params["output_config"] == {"effort": effort} and params["max_tokens"] == 1500
        assert params["cache_control"] == {"type": "ephemeral"} and profile.router == "haiku"
