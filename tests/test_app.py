from pathlib import Path

from streamlit.testing.v1 import AppTest

from roulette_lab.experiment import ExperimentState


ROOT = Path(__file__).resolve().parents[1]


def test_sidebar_posterior_controls_reach_rendered_live_outputs():
    app = AppTest.from_file(ROOT / "app.py", default_timeout=20)
    app.session_state["experiment_signature"] = (
        20260912,
        1_000.0,
        "european",
        "standard",
        "straight",
        ("17",),
    )
    app.session_state["experiment_state"] = ExperimentState(
        seed=20260912,
        initial_bankroll=1_000.0,
        history=("17",) * 8 + ("0",) * 32,
        bankroll=1_000.0,
    )
    app.run(timeout=20)
    before = {metric.label: metric.value for metric in app.metric}

    app.select_slider(key="posterior-credible-level").set_value(0.80)
    app.select_slider(key="posterior-conservative-quantile").set_value(0.25)
    app.number_input(key="posterior-future-spins").set_value(20)
    app.run(timeout=20)
    after = {metric.label: metric.value for metric in app.metric}

    assert not app.exception
    assert before["Credible interval"] != after["Credible interval"]
    assert before["Conservative Kelly"] != after["Conservative Kelly"]
    assert before["Predictive hits"] != after["Predictive hits"]


def test_valid_history_upload_replaces_live_history_with_success_state():
    app = AppTest.from_file(ROOT / "app.py", default_timeout=20).run(timeout=20)

    app.file_uploader(key="history-import-file").upload(
        "valid.csv", b"spin,pocket\n1,17\n2,0\n", "text/csv"
    ).run(timeout=20)
    app.button(key="history-import-submit").click().run(timeout=20)

    assert not app.exception
    assert [message.value for message in app.success] == [
        "Imported 2 spins. Bankroll reset to the initial value."
    ]
    assert not app.error
    assert app.session_state["experiment_state"].history == ("17", "0")


def test_invalid_history_upload_shows_error_and_preserves_live_state():
    app = AppTest.from_file(ROOT / "app.py", default_timeout=20).run(timeout=20)
    original = ExperimentState(
        seed=20260912,
        initial_bankroll=1_000.0,
        history=("17", "0"),
        bankroll=980.0,
    )
    app.session_state["experiment_state"] = original

    app.file_uploader(key="history-import-file").upload(
        "invalid.csv", b"spin,pocket\n1,00\n", "text/csv"
    ).run(timeout=20)
    app.button(key="history-import-submit").click().run(timeout=20)

    assert not app.exception
    assert not app.success
    assert [message.value for message in app.error] == [
        "History import failed: Unknown pocket '00' in CSV row 2."
    ]
    assert app.session_state["experiment_state"] == original
