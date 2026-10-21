import asyncio
import importlib.util
import pathlib
from types import SimpleNamespace

from strands.interventions import Deny, Guide, Proceed

PATH = pathlib.Path(__file__).resolve().parent.parent / "patterns" / "policy" / "policy_gate.py"


def load():
    spec = importlib.util.spec_from_file_location("policy_gate", PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeClient:
    def __init__(self, answers):
        self.answers, self.calls = answers, []

    def ask(self, state, questions):
        self.calls.append((state, questions))
        return self.answers


QUESTIONS = {"urgency": {"type": "choice", "instructions": "How urgent?", "criteria": {"low": "can wait", "high": "now"}}}


def event(name="refund"):
    return SimpleNamespace(tool_use={"name": name, "input": {"amount": 5}, "toolUseId": "t1"}, agent=SimpleNamespace(messages=[]))


def make(module, answers, decide):
    return module.PolicyGate(QUESTIONS, lambda ev: f"tool={ev.tool_use['name']}", decide, FakeClient(answers), tools={"refund"})


def run(gate, ev):
    return asyncio.run(gate.before_tool_call(ev))


def test_pattern_file_is_self_contained():
    source = PATH.read_text()
    assert "import dealjudge" not in source and "from dealjudge" not in source


def test_decide_result_maps_to_the_sdk_actions():
    module = load()
    answers = {"urgency": {"choice": "high"}}
    assert isinstance(run(make(module, answers, lambda a: ("proceed", "")), event()), Proceed)
    assert isinstance(run(make(module, answers, lambda a: ("deny", "no")), event()), Deny)
    guided = run(make(module, answers, lambda a: ("guide", "ask the user first")), event())
    assert isinstance(guided, Guide) and guided.feedback == "ask the user first"


def test_the_gate_asks_the_typed_questions_with_the_rendered_state():
    module = load()
    gate = make(module, {"urgency": {"choice": "low"}}, lambda a: ("proceed", ""))
    run(gate, event())
    state, questions = gate._client.calls[0]
    assert state == "tool=refund" and questions == QUESTIONS


def test_tools_outside_the_watched_set_pass_without_asking():
    module = load()
    gate = make(module, {}, lambda a: ("deny", "no"))
    assert isinstance(run(gate, event(name="other")), Proceed)
    assert gate._client.calls == []


def test_an_unusable_client_answer_fails_toward_deny():
    module = load()

    class Broken:
        def ask(self, state, questions):
            raise RuntimeError("down")

    gate = module.PolicyGate(QUESTIONS, lambda ev: "s", lambda a: ("proceed", ""), Broken())
    assert isinstance(run(gate, event()), Deny)
