from collections.abc import Iterator

from backend.assistant.loop import stream_reply
from backend.assistant.policy_path import policy_reply
from backend.assistant.profiles import Profile, active_profile
from backend.routing.router import route
from backend.sessions import Session
from backend.stream_events import event


def reply(session: Session, text: str, language: str, profile: Profile | None = None) -> Iterator[dict]:
    profile = profile or active_profile()
    if profile.router:
        chosen = route(text, session.messages)
        yield event("route", name=chosen)
        if chosen == "politica":
            yield from policy_reply(session, text, language)
            return
    yield from stream_reply(session, text, language, profile)
