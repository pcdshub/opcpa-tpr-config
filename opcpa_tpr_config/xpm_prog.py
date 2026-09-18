import argparse
import itertools
import logging

import numpy as np

logger = logging.getLogger(__name__)
from psdaq.cas.pvedit import Pv
from psdaq.seq.seq import (ACRateSync, Branch, ControlRequest, FixedRateSync,
                           acRateHzToMarker)
from psdaq.seq.seqprogram import SeqUser

factors = [2, 2, 2, 2, 5, 5, 5, 5, 7, 13]  # 910,000
sc_factors = [2, 2, 2, 5, 5, 5, 5, 7]  # 35000 (remove 13, 2, add 1)
nc_factors = [2, 2, 2, 3, 5]# 120Hz  (independent of 910k factors)


def make_possible_rates(laser_factors):
    """
    Generate a list of factors --> rates (TPG second)
    """
    iters = [
        itertools.combinations(
            laser_factors, i+1
        ) for i in range(len(laser_factors))
    ]
    f = set()  # Unique set of factors; trims out duplicates
    for i in iters:
        for c in i:
            q = np.prod(np.array(c))
            f.add(q)

    return sorted(list(f))


def allowed_goose_rates(laser_rate, rate_list):
    """
    Return a dict of allowed goose rates, based on the base rate of the laser
    and a dictionary of allowed base rates created using make_laser_rates().
    """

    return [rate for rate in rate_list if rate < laser_rate]

def validate_goose_len(base_div, goose_div, goose_len):
    """ Quick check for goose len to validate user input """
    if goose_div is None:
        return 1
    if goose_len < 1:
        return 1
    max_goose =   (goose_div//base_div) - 1
    return min(max_goose, goose_len)

# Selected base rate + goose rate --> pulse sequence
def make_sequence_sc(base_div, goose_div=None, goose_len=1, goose_start=1, offset=None, debug=False):
    # Do some setup
    instrset = []

    goose_len = validate_goose_len(base_div,goose_div, goose_len)

    # Insert bucket offset if it is present
    if offset is not None and offset != 0:
        instrset.append(FixedRateSync(marker="910kH", occ=offset))
        logger.debug(f"FixedRateSync(marker='910kH', occ={offset})")

    #initial goose start offset
    if goose_start > 1:
        occ = base_div * (goose_len - 1)
        instrset.append(FixedRateSync(marker="910kH", occ=occ))
        logger.debug(f"FixedRateSync(marker='910kH', occ={occ})")

    branch_0 = len(instrset)
    if goose_div not in (None, 0):
        # calculate ontime per goose
        ontime_per_goose= (goose_div//base_div) - goose_len

        # goosing shots are first, then # of ontime shots per goose
        for i in range(goose_len):
            instrset.append(ControlRequest([1, 2])) # goose + all
            logger.debug("ControlRequest([1, 2])  # goose + all")
            instrset.append(FixedRateSync(marker="910kH", occ=base_div))
            logger.debug(f"FixedRateSync(marker='910kH', occ={base_div})")
        for i in range(ontime_per_goose):
            instrset.append(ControlRequest([0, 2])) # on_time + all
            logger.debug("ControlRequest([0, 2])  # on_time + all")
            instrset.append(FixedRateSync(marker="910kH", occ=base_div))
            logger.debug(f"FixedRateSync(marker='910kH', occ={base_div})")
    else:
        # no goose, only on_time shots
        instrset.append(ControlRequest([0,2])) #on_time + all
        logger.debug("ControlRequest([0, 2])  # on_time + all")
        instrset.append(FixedRateSync(marker="910kH", occ=base_div))
        logger.debug(f"FixedRateSync(marker='910kH', occ={base_div})")

    # loop back to start
    instrset.append(Branch.unconditional(line=branch_0))
    logger.debug(f"Branch.unconditional(line={branch_0})")

    return instrset

def make_sequence_nc(base_div, start_ts1=True, goose_div=None, goose_len=1, goose_start=1, debug=False):
    """
    Generate an AC sequence at spacing of base_div times the base (120hz) rate for
    NC operation.

    NOTE:  AC base rates always need to specify a timeslot.
           There are 6 time slots each with 60H rate markers.

    Parameters
    ----------
    base_div
       divisor in units of beams (120hz)
       1 => full rate 120HZ, 2 for 60Hz, 3 for 40Hz, etc.
       rate = 120 / base_div
    start_ts1, optional
        if True, start synced to TS1, else TS4
        Only changes pattern if rate is a sub-harmonic of 60 Hz
    goose_div, optional
        Goose trigger divisor (same units as base_div)
        Must be integer multiple of base_div!
    debug, optional
        add print statements, by default False

    Notes
    -------

    Confluence Docs are inconsistent with the library definitions used here!
    Confluence examples show that "marker 0" corresponds to 60H rate,
    but in the acRateHzToMarker dictionary in seq.py, clearly maps "60H" maps to "marker 5".

    I used the library definitions here for correct simulations
    but this should be verified on hardware!
    """

    # Do some setup
    instrset = []

    goose_len = validate_goose_len(base_div,goose_div, goose_len)

    fiducial_marker = acRateHzToMarker["60Hz"]

    # first sync to starting timeslot
    if start_ts1:
        timeslot_mask = (1<<0)
    else:
        timeslot_mask = (1<<3)
    instrset.append(ACRateSync(timeslotm=timeslot_mask, marker=fiducial_marker, occ=1))
    logger.debug(f"ACRateSync(timeslotm={timeslot_mask}, marker={fiducial_marker}, occ=1)")

    # Linac only fires on TS 1 and 4
    timeslot_mask = (1<<0) | (1<<3)

    #initial offset for goose start
    if goose_start > 1:
        occ = base_div * (goose_start - 1)
        instrset.append(ACRateSync(timeslotm=timeslot_mask, marker=fiducial_marker, occ=occ))
        logger.debug(f"ACRateSync(timeslotm={timeslot_mask}, marker={fiducial_marker}, occ={occ})")

    branch_0 = len(instrset)
    if goose_div not in (None, 0):
        # calculate ontime per goose
        ontime_per_goose= (goose_div//base_div) - goose_len

        # goosing shots are first, then # of ontime shots per goose
        for i in range(goose_len):
            instrset.append(ControlRequest([1, 2])) # goose + all
            logger.debug("ControlRequest([1, 2])  # goose + all")
            instrset.append(ACRateSync(timeslotm=timeslot_mask, marker=fiducial_marker, occ=base_div))
            logger.debug(f"ACRateSync(timeslotm={timeslot_mask}, marker={fiducial_marker}, occ={base_div})")
        for i in range(ontime_per_goose):
            instrset.append(ControlRequest([0, 2])) # on_time + all
            logger.debug("ControlRequest([0, 2])  # on_time + all")
            instrset.append(ACRateSync(timeslotm=timeslot_mask, marker=fiducial_marker, occ=base_div))
            logger.debug(f"ACRateSync(timeslotm={timeslot_mask}, marker={fiducial_marker}, occ={base_div})")
    else:
        # no goose, only on_time shots
        instrset.append(ControlRequest([0,2])) #on_time + all
        logger.debug("ControlRequest([0, 2])  # on_time + all")
        instrset.append(ACRateSync(timeslotm=timeslot_mask, marker=fiducial_marker, occ=base_div))
        logger.debug(f"ACRateSync(timeslotm={timeslot_mask}, marker={fiducial_marker}, occ={base_div})")

    # loop back to start
    instrset.append(Branch.unconditional(line=branch_0))
    logger.debug(f"Branch.unconditional(line={branch_0})")

    for instr in instrset:
        logger.debug(f"{instr.print_()}")

    return instrset


def make_base_sequence(offset=None, firstSyncAC=False):
    """
    Setup base rate sequences always needed to operate the laser system.

    Rates: AC Rate 71,428, 35,714, 102, 5.1 Hz
            70k, 35k, 100, 5 (TPG seconds)

    Notes
    ----

    The AC power line is sampled at 2/14Mhz = 35,714 Hz
    to guaranteed all AC crossings coincide every two 71428 Hz markers.

    During testing it was observed the ACRateSync was observed to have an
    offset of 7 910kH markers from the corresponding 70kH fixedRateSync.

    This offset might change from 7, so the offset selection is kept even for AC rates

    """
    # initialize instruction set array
    instrset = []

    if offset is None:
        offset = 0

    if firstSyncAC:
        timeslot_mask = (1<<0) | (1<<3)
        fiducial_marker = acRateHzToMarker["60Hz"]
        instrset.append(ACRateSync(timeslotm=timeslot_mask, marker=fiducial_marker, occ=1))
        logger.debug(f"ACRateSync(timeslotm={timeslot_mask}, marker={fiducial_marker}, occ=1)")
        # needed so first offset_request() starts at a 70H marker
        instrset.append(FixedRateSync(marker="70kH", occ=2))
        logger.debug("FixedRateSync(marker='70kH', occ=2)")

    branch_0 = len(instrset)
    _add_offset_request(instrset, [0, 1, 2, 3], offset) # 70kH + 35kH + 100H + 5H
    instrset.append(FixedRateSync(marker="70kH", occ=1))
    logger.debug("FixedRateSync(marker='70kH', occ=1)")
    branch_1 = len(instrset)
    _add_inner_sequence(instrset, offset=offset)

    ## Loop 2: 100H markers per 5H marker
    spacing_100 = 700
    spacing_5 = 14000
    loop_count = spacing_5 // spacing_100 - 2
    instrset.append(Branch.conditional(line=branch_1, counter=1, value=loop_count))
    logger.debug(f"Branch.conditional(line={branch_1}, counter=1, value={loop_count})")
    # again last iteration has to be done manually
    _add_inner_sequence(instrset, offset=offset, final=True)

    instrset.append(Branch.unconditional(line=branch_0))
    logger.debug(f"Branch.unconditional(line={branch_0})")

    return instrset

def _add_offset_request(instrset: list, request, offset) -> list:
    """ helper function adds control requests with appropriate offset"""
    if offset != 0:
        instrset.append(FixedRateSync(marker="910kH", occ=offset))
        logger.debug(f"FixedRateSync(marker='910kH', occ={offset})")
    instrset.append(ControlRequest(request))
    logger.debug(f"ControlRequest({request})")


def _add_inner_sequence(instrset: list, offset=None, final=False):
    """
    To make the nc sequence a little more readable,
    a repeated section is broken out here

    Loop 1:
    75kH + 35kH markers per 100H marker

    final = true, do not add 100H last marker
    """
    # define all spacings in terms of smallest marker
    # spacing_70k = 1
    spacing_35k = 2
    spacing_100 = 700

    loop_count = spacing_100//spacing_35k - 2
    branch = len(instrset)
    _add_offset_request(instrset, [0], offset) #70kH
    instrset.append(FixedRateSync(marker="70kH", occ=1))
    logger.debug("FixedRateSync(marker='70kH', occ=1)")
    _add_offset_request(instrset, [0, 1], offset) #70kH + 35KH
    instrset.append(FixedRateSync(marker="70kH", occ=1))
    logger.debug("FixedRateSync(marker='70kH', occ=1)")
    instrset.append(Branch.conditional(line=branch, counter=0, value=loop_count))
    logger.debug(f"Branch.conditional(line={branch}, counter=0, value={loop_count})")
    # last iteration done manually since last iteration is different
    _add_offset_request(instrset, [0], offset) #70kH
    instrset.append(FixedRateSync(marker="70kH", occ=1))
    logger.debug("FixedRateSync(marker='70kH', occ=1)")
    if not final:
        _add_offset_request(instrset, [0, 1, 2], offset) #70kH + 35KH + 100H
        instrset.append(FixedRateSync(marker="70kH", occ=1))
        logger.debug("FixedRateSync(marker='70kH', occ=1)")
    return instrset


def write_xpm_config(xpm_pv: str, engine: int, seqdesc: dict, instrset: list) -> None:
    """Write an XPM sequence configuration to the specified engine."""
    seqcodes_pv = Pv(f'{xpm_pv}:SEQCODES', isStruct=True)
    seqcodes = seqcodes_pv.get()
    desc = seqcodes.value.Description

    seq = SeqUser(f'{xpm_pv}:SEQENG:{engine}')
    seq.execute('title', instrset, None, sync=True, refresh=False)

    engineMask = 1 << engine

    for e in range(4 * engine, 4 * engine + 4):
        desc[e] = ''
    for e, d in seqdesc.items():
        desc[4 * engine + e] = d

    tmo = 5.0  # EPICS PVA timeout

    v = seqcodes.value
    v.Description = desc
    seqcodes.value = v
    seqcodes_pv.put(seqcodes, wait=tmo)

    pvSeqReset = Pv(f'{xpm_pv}:SeqReset')
    pvSeqReset.put(engineMask, wait=tmo)


def build_laser_sequence(
    is_sc: bool,
    base_rate: int,
    goose_rate: int | None,
    goose_enabled: bool,
    offset: int,
    start_ts1: bool = True,
    goose_len: int = 1,
    goose_start: int = 1,
    bay: str = "",
) -> tuple[dict, list]:
    """Build the laser on/off time sequence and description."""
    fiducials_per_period = 910000 if is_sc else 120
    base_div = fiducials_per_period // base_rate

    if goose_enabled and goose_rate is not None:
        goose_div = fiducials_per_period // goose_rate
    else:
        goose_div = None

    logger.info(f"Building laser sequence: base_rate={base_rate}, goose_rate={goose_rate}")
    logger.debug(f"base_div={base_div}, goose_div={goose_div}, offset={offset}")

    if is_sc:
        instrset = make_sequence_sc(
            base_div, goose_div=goose_div, goose_len=goose_len,
            goose_start=goose_start, offset=offset,
        )
    else:
        instrset = make_sequence_nc(
            base_div, start_ts1=start_ts1, goose_div=goose_div,
            goose_len=goose_len, goose_start=goose_start,
        )

    seqdesc = {
        0: f"{bay} On time shots",
        1: f"{bay} Goose shots",
        2: f"{bay} All laser shots",
        3: "",
    }
    return seqdesc, instrset


def build_base_sequence(
    is_sc: bool,
    offset: int,
    bay: str = "",
) -> tuple[dict, list]:
    """Build the base rate sequence and description."""
    logger.info(f"Building base sequence: offset={offset}")

    instrset = make_base_sequence(offset, firstSyncAC=(not is_sc))

    seqdesc = {
        0: f"{bay} 71.4kHz",
        1: f"{bay} 35.7kHz",
        2: f"{bay} 102Hz",
        3: f"{bay} 5Hz",
    }
    return seqdesc, instrset


def program_xpm(bay: int, engine: int, laser_rate: int, goose_rate: int, offset: int, xpm_pv="DAQ:DEH:XMP:0") -> None:
    """Build and program the XPM sequence for a given bay/engine."""
    base_list = make_possible_rates(sc_factors)

    if laser_rate not in base_list:
        raise ValueError(
            f"Base rate {laser_rate} is not one of the available laser "
            f"rates: {base_list}"
        )

    goose_list = allowed_goose_rates(laser_rate, base_list)

    if goose_rate not in goose_list:
        raise ValueError(
            f"Goose rate {goose_rate} is not one of the available goose "
            f"rates: {goose_list}"
        )

    seqdesc = {0: f"Bay {bay} On Time", 1: f"Bay {bay} Off Time", 2: "", 3: ""}
    base_div = 910000 // int(laser_rate)
    goose_div = 910000 // int(goose_rate)
    inst = make_sequence_sc(base_div, goose_div=goose_div, offset=offset)

    logger.info(f"Programming XPM: bay={bay} engine={engine} laser_rate={laser_rate} goose_rate={goose_rate} offset={offset}")

    write_xpm_config(xpm_pv, engine, seqdesc, inst)
    logger.info("XPM programming complete")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="XPM sequence programmer")

    parser.add_argument(
        "--mode", type=str, choices=["sc", "nc"], default="sc",
        help="Timing mode: 'sc' for superconducting (910kHz base), 'nc' for normal conducting (120Hz base) (default: sc)"
    )
    parser.add_argument(
        "laser_rate", type=int, nargs="?", default=None,
        help="Desired laser output rep rate (total)"
    )
    parser.add_argument(
        "goose_rate", type=int, nargs="?", default=None,
        help="Desired laser goose rate (sub-harmonic of laser_rate)"
    )
    parser.add_argument(
        "offset", type=int, nargs="?", default=0,
        help="Desired 910 kHz bucket offset (default: 0)"
    )
    parser.add_argument(
        "--bay", type=int, choices=[1, 2, 3], default=None,
        help="Laser bay to program (required unless --dry-run)"
    )
    parser.add_argument(
        "--engine", type=int, default=None,
        help="XPM sequence engine number (required unless --dry-run)"
    )
    parser.add_argument(
        "--dry-run", action="store_true", default=True,
        help="Build sequence without programming hardware (default: True)"
    )
    parser.add_argument(
        "--no-dry-run", dest="dry_run", action="store_false",
        help="Actually program the XPM hardware"
    )
    parser.add_argument(
        "--debug", action="store_true", default=True,
        help="Enable debug-level log messages (default: True)"
    )
    parser.add_argument(
        "--no-debug", dest="debug", action="store_false",
        help="Disable debug-level log messages"
    )
    parser.add_argument(
        "--list", action="store_true", default=False,
        help="List possible base rates and exit"
    )

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(name)s [%(levelname)s] %(message)s",
    )

    # Select rate factors and sequence builder based on mode
    if args.mode == "sc":
        rate_factors = sc_factors
        clock_rate = 910000
        make_sequence = make_sequence_sc
    else:
        rate_factors = nc_factors
        clock_rate = 120
        make_sequence = make_sequence_nc

    base_list = make_possible_rates(rate_factors)

    # --list: print possible rates and exit
    if args.list:
        print(f"Mode: {args.mode} (clock={clock_rate} Hz)")
        print(f"Possible base rates (divisors): {base_list}")
        if args.laser_rate is not None:
            goose_list = allowed_goose_rates(args.laser_rate, base_list)
            print(f"Possible goose rates for laser_rate={args.laser_rate}: {goose_list}")
        raise SystemExit(0)

    # Positional args are required when not just listing
    if args.laser_rate is None or args.goose_rate is None:
        parser.error("laser_rate and goose_rate are required (use --list to see options)")

    # Validate bay/engine are provided when not dry-running
    if not args.dry_run:
        if args.bay is None or args.engine is None:
            parser.error("--bay and --engine are required when not using --dry-run")

    if args.laser_rate not in base_list:
        parser.error(
            f"On-time rate {args.laser_rate} is not one of the available "
            f"{args.mode} rates: {base_list}"
        )

    goose_list = allowed_goose_rates(args.laser_rate, base_list)

    if args.goose_rate not in goose_list:
        parser.error(
            f"Goose rate {args.goose_rate} is not one of the available goose "
            f"rates: {goose_list}"
        )

    base_div = clock_rate // args.laser_rate
    goose_div = clock_rate // args.goose_rate
    inst = make_sequence(base_div, goose_div, offset=args.offset, debug=args.debug)

    logger.info(f"Generated {args.mode} sequence with {len(inst)} instructions")
    for i, instr in enumerate(inst):
        logger.debug(f"  [{i}] {instr}")

    if args.dry_run:
        logger.info("Dry run complete — no hardware programmed")
    else:
        program_xpm(args.bay, args.engine, args.laser_rate, args.goose_rate, args.offset)
