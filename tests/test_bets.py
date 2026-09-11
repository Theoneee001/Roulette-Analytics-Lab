import numpy as np
import pytest

from roulette_lab.bets import (
    BetKind,
    BetSpec,
    SpecialRule,
    expected_net_return,
    house_edge,
    kelly_fraction,
    make_standard_bet,
)
from roulette_lab.wheels import WheelKind, make_biased_wheel, make_fair_wheel


@pytest.mark.parametrize(
    ("wheel_kind", "expected_edge"),
    [(WheelKind.EUROPEAN, 1 / 37), (WheelKind.AMERICAN, 2 / 38)],
)
def test_straight_up_house_edge(wheel_kind, expected_edge):
    wheel = make_fair_wheel(wheel_kind)
    bet = make_standard_bet(BetKind.STRAIGHT, ("17",), wheel)

    assert house_edge(wheel, bet, SpecialRule.STANDARD) == pytest.approx(
        expected_edge
    )


def test_european_la_partage_halves_even_money_edge():
    wheel = make_fair_wheel(WheelKind.EUROPEAN)
    bet = make_standard_bet(BetKind.RED, (), wheel)

    assert house_edge(wheel, bet, SpecialRule.LA_PARTAGE) == pytest.approx(1 / 74)


def test_kelly_requires_probability_above_break_even():
    assert kelly_fraction(1 / 37, 35) == 0.0
    assert kelly_fraction(1 / 36, 35) == pytest.approx(0.0)
    assert kelly_fraction(0.03, 35) > 0.0


@pytest.mark.parametrize(
    ("kind", "selection", "net_odds"),
    [
        (BetKind.STRAIGHT, ("17",), 35),
        (BetKind.SPLIT, ("17", "18"), 17),
        (BetKind.STREET, ("16", "17", "18"), 11),
        (BetKind.CORNER, ("16", "17", "19", "20"), 8),
        (BetKind.SIX_LINE, ("13", "14", "15", "16", "17", "18"), 5),
        (BetKind.DOZEN, tuple(str(number) for number in range(1, 13)), 2),
        (BetKind.COLUMN, tuple(str(number) for number in range(1, 37, 3)), 2),
    ],
)
def test_standard_bets_bind_standard_payout_to_valid_coverage(
    kind, selection, net_odds
):
    wheel = make_fair_wheel(WheelKind.EUROPEAN)

    bet = make_standard_bet(kind, selection, wheel)

    assert bet.covered_labels == selection
    assert bet.net_odds == net_odds


@pytest.mark.parametrize(
    "kind",
    [
        BetKind.RED,
        BetKind.BLACK,
        BetKind.EVEN,
        BetKind.ODD,
        BetKind.LOW,
        BetKind.HIGH,
    ],
)
def test_even_money_bets_derive_their_eighteen_covered_labels(kind):
    wheel = make_fair_wheel(WheelKind.EUROPEAN)

    bet = make_standard_bet(kind, (), wheel)

    assert len(bet.covered_labels) == 18
    assert bet.net_odds == 1
    assert "0" not in bet.covered_labels


def test_standard_bets_reject_wrong_selection_size():
    wheel = make_fair_wheel(WheelKind.EUROPEAN)

    with pytest.raises(ValueError, match="requires 2 labels"):
        make_standard_bet(BetKind.SPLIT, ("17",), wheel)


@pytest.mark.parametrize(
    ("wheel_kind", "label"),
    [(WheelKind.EUROPEAN, "0"), (WheelKind.AMERICAN, "0"), (WheelKind.AMERICAN, "00")],
)
def test_straight_bets_accept_zero_pockets_present_on_the_wheel(wheel_kind, label):
    wheel = make_fair_wheel(wheel_kind)

    bet = make_standard_bet(BetKind.STRAIGHT, (label,), wheel)

    assert bet.covered_labels == (label,)


def test_straight_bets_reject_zero_pockets_absent_from_the_wheel():
    wheel = make_fair_wheel(WheelKind.EUROPEAN)

    with pytest.raises(ValueError, match="present on the wheel"):
        make_standard_bet(BetKind.STRAIGHT, ("00",), wheel)


@pytest.mark.parametrize(
    ("kind", "selection"),
    [
        (BetKind.SPLIT, ("17", "19")),
        (BetKind.STREET, ("16", "17", "19")),
        (BetKind.CORNER, ("16", "17", "18", "19")),
        (BetKind.SIX_LINE, ("13", "14", "15", "19", "20", "21")),
        (BetKind.DOZEN, tuple(str(number) for number in range(1, 12)) + ("13",)),
        (BetKind.COLUMN, tuple(str(number) for number in range(1, 13))),
    ],
)
def test_standard_bets_reject_noncanonical_geometries(kind, selection):
    wheel = make_fair_wheel(WheelKind.EUROPEAN)

    with pytest.raises(ValueError, match="valid"):
        make_standard_bet(kind, selection, wheel)


def test_expected_return_revalidates_directly_constructed_bet_geometry():
    wheel = make_fair_wheel(WheelKind.EUROPEAN)
    invalid_corner = BetSpec(BetKind.CORNER, ("16", "17", "18", "19"), 8)

    with pytest.raises(ValueError, match="valid corner"):
        expected_net_return(wheel, invalid_corner, SpecialRule.STANDARD)


def test_expected_return_revalidates_direct_straight_bet_wheel_membership():
    wheel = make_fair_wheel(WheelKind.EUROPEAN)
    double_zero = BetSpec(BetKind.STRAIGHT, ("00",), 35)

    with pytest.raises(ValueError, match="present on the wheel"):
        expected_net_return(wheel, double_zero, SpecialRule.STANDARD)


def test_expected_return_rejects_zero_in_a_direct_nonstraight_inside_bet():
    wheel = make_fair_wheel(WheelKind.EUROPEAN)
    invalid_split = BetSpec(BetKind.SPLIT, ("0", "1"), 17)

    with pytest.raises(ValueError, match="1 through 36"):
        expected_net_return(wheel, invalid_split, SpecialRule.STANDARD)


def test_expected_return_revalidates_direct_outside_bet_coverage():
    wheel = make_fair_wheel(WheelKind.EUROPEAN)
    non_red_coverage = BetSpec(
        BetKind.RED, tuple(str(number) for number in range(1, 19)), 1
    )

    with pytest.raises(ValueError, match="standard wheel coverage"):
        expected_net_return(wheel, non_red_coverage, SpecialRule.STANDARD)


@pytest.mark.parametrize(
    ("wheel_kind", "kind", "rule"),
    [
        (WheelKind.AMERICAN, BetKind.RED, SpecialRule.LA_PARTAGE),
        (WheelKind.EUROPEAN, BetKind.STRAIGHT, SpecialRule.LA_PARTAGE),
        (WheelKind.AMERICAN, BetKind.RED, SpecialRule.EN_PRISON),
        (WheelKind.EUROPEAN, BetKind.STRAIGHT, SpecialRule.EN_PRISON),
    ],
)
def test_special_rules_require_european_even_money_bets(wheel_kind, kind, rule):
    wheel = make_fair_wheel(wheel_kind)
    selection = ("17",) if kind is BetKind.STRAIGHT else ()
    bet = make_standard_bet(kind, selection, wheel)

    with pytest.raises(ValueError, match="European even-money"):
        expected_net_return(wheel, bet, rule)


def test_en_prison_is_a_deferred_settlement_with_half_zero_loss_in_expectation():
    wheel = make_fair_wheel(WheelKind.EUROPEAN)
    bet = make_standard_bet(BetKind.BLACK, (), wheel)

    assert expected_net_return(wheel, bet, SpecialRule.EN_PRISON) == pytest.approx(
        -1 / 74
    )
    assert house_edge(wheel, bet, SpecialRule.EN_PRISON) == pytest.approx(1 / 74)


def test_en_prison_rejects_a_wheel_where_a_zero_stake_never_settles():
    probabilities = np.zeros(37)
    probabilities[0] = 1.0
    wheel = make_biased_wheel(WheelKind.EUROPEAN, probabilities)
    bet = make_standard_bet(BetKind.RED, (), wheel)

    with pytest.raises(ValueError, match="never settles"):
        expected_net_return(wheel, bet, SpecialRule.EN_PRISON)


def test_en_prison_accepts_a_near_degenerate_wheel_that_can_settle():
    remaining_probability = 1e-13
    probabilities = np.zeros(37)
    probabilities[0] = 1.0 - remaining_probability
    probabilities[1] = remaining_probability
    wheel = make_biased_wheel(WheelKind.EUROPEAN, probabilities)
    bet = make_standard_bet(BetKind.RED, (), wheel)

    result = expected_net_return(wheel, bet, SpecialRule.EN_PRISON)

    assert np.isfinite(result)
    assert result == pytest.approx(remaining_probability)


@pytest.mark.parametrize(
    ("probability", "net_odds", "fraction", "expected"),
    [
        (0.5, 1, 1.0, 0.0),
        (0.75, 1, 1.0, 0.5),
        (0.75, 1, 0.5, 0.25),
        (1.0, 1, 1.0, 1.0),
        (0.0, 1, 1.0, 0.0),
    ],
)
def test_kelly_clamps_full_fraction_before_applying_requested_fraction(
    probability, net_odds, fraction, expected
):
    assert kelly_fraction(probability, net_odds, fraction) == pytest.approx(expected)


def test_kelly_rejects_non_positive_net_odds():
    with pytest.raises(ValueError, match="positive"):
        kelly_fraction(0.6, 0)


@pytest.mark.parametrize("net_odds", [float("nan"), float("inf")])
def test_kelly_rejects_non_finite_net_odds(net_odds):
    with pytest.raises(ValueError, match="positive"):
        kelly_fraction(0.6, net_odds)


def test_kelly_rejects_fraction_outside_the_fractional_range():
    with pytest.raises(ValueError, match="between zero and one"):
        kelly_fraction(0.75, 1, 2.0)
