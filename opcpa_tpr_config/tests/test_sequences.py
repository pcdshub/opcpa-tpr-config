""" Tests for XPM sequence generation"""

from pprint import pprint

import numpy as np
import psdaq.seq.seq
from psdaq.seq.globals import *
from psdaq.seq.seqplot import *

from opcpa_tpr_config import xpm_prog


def simulate_sequence(title, instrset, descset, stop=910001, engine=0, acmode=False):
    """
    Simulates executing the given instruction set using classes from seqplot.py.

    Parameters
    ----------
    title : str
        The title or name of the sequence simulation.
    instrset : list
        A list of instructions to be executed in the simulation.
    descset : list
        A list of descriptions corresponding to each instruction.
    stop : int, optional
        the number of frames to simulate
    acmode : bool, optional
        if following Fixed rate or AC marker  (won't simulate both)

    Returns
    -------
    the sequence object after execution

    """
    seq = SeqUser(start=0, stop=stop, acmode=acmode)
    seq.execute(title, instrset, descset)
    ydata = np.array(seq.ydata) + int(engine) * 4 + 272
    return (seq.xdata, ydata)


def sequence_stats(data: tuple, event_defs=None):
    """
    Gives basic stats about the generated sequence to confirm the
    correct number of triggers are generated.

    For now just list event code counts assuming 1 TPG second of frames.
    """
    frame_number, event_codes = data
    event_code_stats = {}

    # Get unique y values and their counts
    unique_codes, counts = np.unique(event_codes, return_counts=True)
    sorted_indices = np.argsort(unique_codes)
    unique_codes = unique_codes[sorted_indices]
    counts = counts[sorted_indices]

    # if event_defs is a list, assume names are given in order
    if event_defs is not None and isinstance(event_defs, list):
        event_dict = {}
        for event_code, event_name in zip(unique_codes, event_defs):
            event_dict[int(event_code)] = event_name
        event_defs = event_dict

    # generate a dict for each event code, add counts and event name
    for value, count in zip(unique_codes, counts):
        event_name = "NA" if event_defs is None else event_defs[value]
        event_code_stats[int(value)] = {"count": int(count), "event_name": event_name}

    # get first instance of each marker, add to dict
    for xi, yi in zip(frame_number, unique_codes):
        if yi not in event_code_stats:
            # (counts, first instance)
            event_code_stats[yi]["start_frame"] = xi

    return event_code_stats


def test_base_sequences():
    """ Test that the NC Base sequences are simulated properly."""
    seqdesc, instrset = xpm_prog.build_base_sequence(
        is_sc=False, offset=0, bay="Test"
    )
    event_names = ['70kH', '35kH', '100H', '5H']
    data = simulate_sequence(
        "NC Base Sequence",
        instrset,
        event_names,
        stop=910000,
        engine=0,
        acmode=False
        )
    pprint(sequence_stats(data, event_names))

def filter_second_period(data: tuple, period: int) -> tuple:
    """Filter simulation data to only include the 2nd period (frames >= period)."""
    xdata, ydata = np.array(data[0]), np.array(data[1])
    mask = xdata >= period -1
    return (xdata[mask], ydata[mask])


def simulate_laser_case(
    is_sc: bool,
    rate: int,
    goose_rate: int | None,
    goose_len: int = 1,
    goose_start: int = 1,
    start_ts1: bool = True,
    assert_check: bool = False
) -> tuple:
    """
    Build, simulate 2 periods, and report stats for the 2nd period.

    The 1st period is discarded to skip initial offset part of the sequence.
    Asserts that event counts in the 2nd period match expected rates.
    Returns (data, stats) for the 2nd period.
    """
    event_names = ["On Time", "Goose", "All Shots"]
    clock = 910000 if is_sc else 360

    seqdesc, instrset = xpm_prog.build_laser_sequence(
        is_sc=is_sc,
        base_rate=rate,
        goose_rate=goose_rate,
        goose_enabled=goose_rate is not None,
        offset=0,
        start_ts1=start_ts1,
        goose_len=goose_len,
        goose_start=goose_start,
        bay="Test",
    )

    # Simulate 2 full periods
    raw_data = simulate_sequence(
        "SC Sequence" if is_sc else "NC Sequence",
        instrset, event_names,
        stop=(2 * clock) - 1, engine=0, acmode=(not is_sc),
    )

    # Analyze only the 2nd period (skip startup transient)
    data = filter_second_period(raw_data, clock)
    stats = sequence_stats(data, event_names)

    mode = "SC" if is_sc else "NC"
    timestamp_start = f"  TS1_start: {start_ts1}" if not is_sc else ""
    goose_start_msg = f"  Goose Start: {goose_start}" if not is_sc else ""
    goose_len_msg = f"  Goose_len: {goose_len}" if goose_rate is not None else ""
    print(f"\n{mode} Rate: {rate} Hz, Goose: {goose_rate}{timestamp_start}{goose_len_msg}{goose_start_msg}")
    pprint(stats)

    if assert_check:
        ontime = stats[272]["count"]
        all_shots = stats[274]["count"]

        assert rate != all_shots, f"ERROR: Simulated rate {all_shots}, Expected Rate {rate}"

        #check goose shots/:
        if goose_rate is not None:
            exp_goose_len = min(rate//goose_rate - 1 , goose_len)
            expected = goose_rate * exp_goose_len
            assert 273 in stats, f"ERROR: no goose shots detected, Expected goose rate{expected}"
            goose = stats[273]["count"]
            # TODO: come up with a reliable way to assert number of goose,
            # since sequences can start at different locations, this is not straight forward
            # assert abs(goose - expected) <= 1, f"ERROR: Simulated goose {goose}, Expected Rate {expected}"
        else:
            if 273 in stats:
                goose = stats[273]["count"]
                raise AssertionError(f"ERROR: goose shots fired when disabled. {goose}")


    return data, stats


def test_all_sequences(
    rate: int,
    is_sc: bool = True,
    goose_starts: list[int] | None = None,
    goose_lens: list[int] | None = None,
):
    """Test sequences across all rate / goose / goose_len combos."""
    if goose_starts is None:
        goose_starts = [1, 2, 3]
    if goose_lens is None:
        goose_lens = [1, 2, 3, 4]

    factors = xpm_prog.sc_factors if is_sc else xpm_prog.nc_factors
    all_rates = xpm_prog.make_possible_rates(factors)

    goose_rates = xpm_prog.allowed_goose_rates(rate, all_rates)
    goose_rates.append(None)
    for goose_rate in goose_rates:
        for goose_start in goose_starts:
            for goose_len in goose_lens:
                simulate_laser_case(
                    is_sc=is_sc,
                    rate=rate,
                    goose_rate=goose_rate,
                    goose_len=goose_len,
                    goose_start=goose_start,
                    assert_check=True
                )

if __name__ == "__main__":
    test_base_sequences()
    test_all_sequences(1000, is_sc=True)
    test_all_sequences(120, is_sc=False)
