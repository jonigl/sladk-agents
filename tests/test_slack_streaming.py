from ai.slack_streaming import (
    clamp_to_stream_budget,
)


def test_clamp_to_stream_budget_with_room():
    clipped, truncated = clamp_to_stream_budget(
        text="hello world",
        current_total_chars=0,
        max_total_chars=100,
        reserve_chars=10,
    )
    assert clipped == "hello world"
    assert truncated is False


def test_clamp_to_stream_budget_truncates():
    clipped, truncated = clamp_to_stream_budget(
        text="abcdefghij",
        current_total_chars=85,
        max_total_chars=100,
        reserve_chars=10,
    )
    assert clipped == "abcde"
    assert truncated is True


def test_clamp_to_stream_budget_no_room():
    clipped, truncated = clamp_to_stream_budget(
        text="abcdefghij",
        current_total_chars=90,
        max_total_chars=100,
        reserve_chars=10,
    )
    assert clipped == ""
    assert truncated is True
