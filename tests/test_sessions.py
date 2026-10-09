import pytest

from backend.sessions import ConversationTooLong, SessionStore


class Clock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def test_reopens_the_same_session():
    store = SessionStore()
    session = store.open(None)

    assert store.open(session.id) is session


def test_expired_session_is_replaced():
    clock = Clock()
    store = SessionStore(ttl=60, clock=clock)
    old = store.open(None)

    clock.now = 61
    new = store.open(old.id)

    assert new.id != old.id
    assert len(store) == 1


def test_activity_keeps_a_session_alive():
    clock = Clock()
    store = SessionStore(ttl=60, clock=clock)
    session = store.open(None)

    for minute in (50, 100, 150):
        clock.now = minute
        assert store.open(session.id) is session


def test_oldest_session_leaves_when_full():
    clock = Clock()
    store = SessionStore(max_sessions=2, clock=clock)
    first = store.open(None)
    clock.now = 1
    second = store.open(None)
    clock.now = 2
    store.open(None)

    assert len(store) == 2
    assert store.open(second.id) is second
    assert store.open(first.id) is not first


def test_commit_only_appends():
    store = SessionStore()
    session = store.open(None)
    session.commit([{"role": "user", "content": "a"}, {"role": "assistant", "content": "b"}], started_at_turn=0)
    session.commit([{"role": "user", "content": "c"}, {"role": "assistant", "content": "d"}], started_at_turn=1)

    assert [m["content"] for m in session.messages] == ["a", "b", "c", "d"]
    assert session.turns == 2


def test_a_reply_based_on_an_old_history_is_not_saved():
    session = SessionStore().open(None)

    assert session.commit([{"role": "user", "content": "a"}, {"role": "assistant", "content": "b"}], started_at_turn=0)
    assert not session.commit([{"role": "user", "content": "c"}, {"role": "assistant", "content": "d"}], started_at_turn=0)

    assert [m["content"] for m in session.messages] == ["a", "b"]
    assert session.turns == 1


def test_turn_limit():
    store = SessionStore(max_turns=1)
    session = store.open(None)
    session.commit([{"role": "user", "content": "a"}, {"role": "assistant", "content": "b"}], started_at_turn=0)

    with pytest.raises(ConversationTooLong):
        store.open(session.id)
