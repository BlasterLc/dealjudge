import json
import sqlite3
from datetime import date

import pytest

from dealjudge.baselines import LlmJudgement
from dealjudge.evaluate import (
    accuracy,
    calibrate_threshold,
    calibration_bins,
    expected_calibration_error,
    llm_action,
    llm_cost_usd,
    run_evaluation,
    summarize_latency,
)
from dealjudge.generator import Truth
from dealjudge.history import PricePoint
from dealjudge.judge import Judgement
from dealjudge.policy import decide
from dealjudge.real_series import knasta_reference, load_series


def test_accuracy():
    assert accuracy(["a", "b", "c", "d"], ["a", "b", "x", "x"]) == 0.5
    assert accuracy([], []) == 0.0


def test_calibration_bins_and_ece_on_hand_computed_points():
    conf = [0.1, 0.15, 0.5, 0.55, 0.9, 0.95]
    correct = [False, False, True, False, True, True]
    bins = calibration_bins(conf, correct, n_bins=5)
    assert [b["n"] for b in bins] == [2, 0, 2, 0, 2]
    assert bins[0]["accuracy"] == 0.0
    assert bins[2]["accuracy"] == 0.5
    assert bins[4]["accuracy"] == 1.0
    assert expected_calibration_error(conf, correct, n_bins=5) == pytest.approx(0.075)


def judgement(level_conf):
    return Judgement(0.95, "buena", level_conf, 0.95, decide(0.95, "buena", level_conf, 0.95, 90), 5.0, False)


def test_calibrate_threshold_picks_the_only_optimal_candidate():
    alert = Truth(True, "buena", True, "avisar")
    warn = Truth(True, "buena", True, "avisar_con_advertencia")
    dev = [(judgement(0.85), alert, 90)] * 4 + [(judgement(0.75), warn, 90)] * 4
    assert calibrate_threshold(dev) == 0.8


def test_calibrate_threshold_warns_where_a_decisive_answer_is_a_coin_flip():
    """Group A (conf 0.3): the decisive answer is right 4 of 10 times, so warning is worth more.
    Group B (conf 0.6): always right, so it must stay decisive. Plain accuracy would pick <= 0.3."""
    alert, silent = Truth(True, "buena", True, "avisar"), Truth(False, "sin_oferta", False, "callar")
    dev = [(judgement(0.3), alert, 90)] * 4 + [(judgement(0.3), silent, 90)] * 6 + [(judgement(0.6), alert, 90)] * 10
    assert calibrate_threshold(dev) == 0.6


def test_llm_action_mapping():
    good = LlmJudgement(True, "buena", True, 0, 0, 0.0, False)
    assert llm_action(good, 90) == "avisar"
    assert llm_action(good, 5) == "avisar_con_advertencia"
    assert llm_action(LlmJudgement(True, "marginal", True, 0, 0, 0.0, False), 90) == "callar"
    assert llm_action(LlmJudgement(False, "", False, 0, 0, 0.0, True), 90) == "avisar_con_advertencia"


def test_cost_and_latency_helpers():
    assert llm_cost_usd(1_000_000, 1_000_000) == pytest.approx(6.0)
    assert summarize_latency([10, 20, 30, 40, 50]) == {"median": 30, "p95": 50}
    assert summarize_latency([]) == {"median": None, "p95": None}


def make_db(path):
    db = sqlite3.connect(path)
    db.execute("""CREATE TABLE snapshots (id INTEGER PRIMARY KEY, ts TEXT, product TEXT, source TEXT,
                  store TEXT, url TEXT, title TEXT, price REAL, currency TEXT, extra TEXT)""")
    rows = [
        ("2026-10-18T09:00:00+00:00", "u1", 20000, "CLP"),
        ("2026-10-18T15:00:00+00:00", "u1", 18000, "CLP"),
        ("2026-10-19T09:00:00+00:00", "u1", 19000, "CLP"),
        ("2026-10-19T09:00:00+00:00", "u1", 25.5, "USD"),
        ("2026-10-19T09:00:00+00:00", "u2", 99999, "CLP"),
    ]
    db.executemany(
        "INSERT INTO snapshots (ts, product, source, store, url, title, price, currency, extra) "
        "VALUES (?, 'p', 'knasta', 's', ?, 't', ?, ?, NULL)",
        rows,
    )
    db.commit()
    db.close()


def test_load_series_keeps_one_clp_price_per_day_the_minimum(tmp_path):
    path = str(tmp_path / "t.db")
    make_db(path)
    assert load_series(path, "u1") == [
        PricePoint(date(2026, 10, 18), 18000),
        PricePoint(date(2026, 10, 19), 19000),
    ]


KNASTA_EXTRA = json.dumps(
    {
        "percent": 5,
        "ndays": 4,
        "descriptive": {"n_history": 47, "state": "HABITUAL", "habitual_price": 17990},
    }
)


def test_knasta_reference_extracts_state_percent_and_history():
    assert knasta_reference(KNASTA_EXTRA) == {"state": "HABITUAL", "percent": 5.0, "n_history": 47}


def test_knasta_reference_is_none_when_fields_are_missing_or_invalid():
    assert knasta_reference(json.dumps({"percent": 5})) is None
    assert knasta_reference("not json") is None
    assert knasta_reference(None) is None


class FakeJudge:
    def __init__(self):
        self.fits_seen = []

    def judge(self, state, history_days, fits_user=None):
        self.fits_seen.append(fits_user)
        return Judgement(0.9, "buena", 0.9, 0.9, decide(0.9, "buena", 0.9, 0.9, history_days), 7.0, False)


class FakeLlm:
    def judge(self, state):
        return LlmJudgement(True, "buena", True, 300, 20, 400.0, False)


def test_run_evaluation_writes_a_complete_report(tmp_path):
    judge = FakeJudge()
    report = run_evaluation(1, 2, 2, judge, FakeLlm(), str(tmp_path))
    assert judge.fits_seen and all(isinstance(f, bool) for f in judge.fits_seen)
    assert set(report["fits_user_accuracy"]) == {"decider_model"}
    for key in ("alert_accuracy", "action_accuracy", "is_real_accuracy", "level_accuracy", "by_scenario",
                "latency_ms", "cost", "calibration", "failures", "meta", "decider_warnings"):
        assert key in report
    assert set(report["alert_accuracy"]) == {"decider", "rule", "llm"}
    assert all(0.0 <= v <= 1.0 for v in report["alert_accuracy"].values())
    assert report["meta"]["simulated"] is True
    assert report["meta"]["n_test"] == 14
    assert report["failures"] == {"decider": 0, "llm": 0}
    assert json.loads((tmp_path / "evaluation.json").read_text())["meta"]["threshold"] == report["meta"]["threshold"]
    assert "simulated" in (tmp_path / "evaluation.md").read_text().lower()
