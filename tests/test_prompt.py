import pytest

from jevkit_mlx import Candidate, DecisionRequest
from jevkit_mlx.prompt import compile_choices, prepare_prompt


class CharacterTokenizer:
    def encode(self, text, **kwargs):
        return list(map(ord, text))

    def decode(self, tokens):
        return "".join(map(chr, tokens))

    def apply_chat_template(self, messages, **kwargs):
        return (
            "".join(f"<{m['role']}>{m['content']}</{m['role']}>" for m in messages) + "<assistant>"
        )


def request(utterance="Close it", state=None):
    return DecisionRequest(
        state or {"window": "notes"}, utterance, (Candidate("close.notes", "Close notes"),)
    )


def test_verified_codes_keep_business_ids():
    choices = compile_choices(CharacterTokenizer(), request())
    assert choices[0].id == "close.notes"
    assert len({c.token_id for c in choices}) == 3
    assert choices[-2].id == "__no_match__"
    assert choices[-1].id == "__abstain__"


def test_snapshot_boundaries_exclude_new_utterance_and_page_changes():
    tokenizer = CharacterTokenizer()
    a = prepare_prompt(tokenizer, request())
    b = prepare_prompt(tokenizer, request("Leave it open"))
    c = prepare_prompt(tokenizer, request(state={"window": "library"}))
    assert a.state_tokens == b.state_tokens
    assert a.tokens != b.tokens
    assert a.system_tokens == c.system_tokens
    assert a.state_tokens != c.state_tokens
    assert a.tokens[: len(a.state_tokens)] == a.state_tokens


def test_tokenizer_collisions_rejected():
    class CollisionTokenizer(CharacterTokenizer):
        def encode(self, text, **kwargs):
            return [1]

        def decode(self, tokens):
            return "0"

    with pytest.raises(ValueError, match="insufficient"):
        compile_choices(CollisionTokenizer(), request())


def test_code_merging_into_prompt_is_rejected():
    class MergingTokenizer(CharacterTokenizer):
        def encode(self, text, **kwargs):
            if text.endswith("<assistant>0"):
                return [999]
            return super().encode(text, **kwargs)

    with pytest.raises(ValueError, match="continuation"):
        prepare_prompt(MergingTokenizer(), request())


def test_candidate_order_changes_prompt_and_mapping():
    a = Candidate("a", "Open A")
    b = Candidate("b", "Open B")
    first = prepare_prompt(CharacterTokenizer(), DecisionRequest({}, "Open A", (a, b)))
    second = prepare_prompt(CharacterTokenizer(), DecisionRequest({}, "Open A", (b, a)))
    assert first.state_tokens != second.state_tokens
    assert first.choices[0].id != second.choices[0].id
