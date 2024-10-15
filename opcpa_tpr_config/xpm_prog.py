# from psdaq.seq.seq import *

# import argparse
import itertools

import numpy as np

# import sys


factors = [2, 2, 2, 2, 5, 5, 5, 5, 7, 13]  # 910,000
carbide_factors = [1, 2, 2, 5, 5, 5, 5, 13]  # 32,500 (remove 2, 2, 7, add 1)


def make_base_rates(laser_factors):
    """
    Generate a dictionary of factors --> rates (TPG second)
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

    return sorted(list(f), reverse=True)


def allowed_goose_rates(base_rate, rate_list):
    """
    Return a dict of allowed goose rates, based on the base rate of the laser
    and a dictionary of allowed base rates created using make_base_rates().
    """

    return [rate for rate in rate_list if rate < base_rate]


# Selected base rate + goose rate --> pulse sequence
# def make_sequence(base_div, goose_div=None, offset=None):
#     # Do some setup
#     instrset = []
#
#     if offset is not None and offset != 0:
#         instrset.append( FixedRateSync(marker="910kH", occ=offset ) )
#
#     # Loop over base:goose rate ratio once. Because we're using divisors,
#     # we divide goose divider by base divider, rather than base rate by
#     # goose rate.
#     if goose_div is None:
#         n = 1
#     else:
#         n = (goose_div//base_div) - 1
#     for i in range(n):
#         instrset.append( ControlRequest([0]) )
#         instrset.append( FixedRateSync(marker="910kH", occ=base_div ) )
#     if goose_div is not None:
#         # Finish with goose pulse
#         instrset.append( ControlRequest([1]) )
#         instrset.append( FixedRateSync(marker="910kH", occ=base_div ) )
#     instrset.append( Branch.unconditional(0) )
#
#     return instrset

# if __name__ == "__main__":
#     parser = argparse.ArgumentParser()
#
#     parser.add_argument(
#         "base_rate",
#         help="Desired laser output rep rate (total)"
#     )
#     parser.add_argument(
#         "goose_rate",
#         help="Desired laser goose rate (sub-harmonic of base_rate)")
#     parser.add_argument("offset", help="Desired 910 kHz bucket offset")
#     parser.add_argument("bay", help="Laser bay to program for (2 or 3)")
#
#     args = parser.parse_args()
#
#     base_rate = int(args.base_rate)
#     goose_rate = int(args.goose_rate)
#     offset = int(args.offset)
#
#     allowed_bays = [2,3]
#     if int(args.bay) not in allowed_bays:
#         raise ValueError(f"Bay {args.bay} not in {allowed_bays}!")
#     else:
#         bay = int(args.bay)
#
#     engine = {2:6, 3:7}  # Bay --> sequence engine mapping
#
#     # Dict will eventually be applied to drop down menu
#     base_dict = make_base_rates(carbide_factors)
#
#     if base_rate not in list(base_dict.keys()):
#         rates = sorted(base_dict)
#         raise ValueError(
#            ("Base rate {base_rate} is not one of the available laser "
#             f"rates: {rates}")
#
#     # Dict will eventually be applied to drop down menu
#     goose_dict = allowed_goose_rates(base_rate, base_dict)
#
#     if goose_rate not in goose_dict.keys():
#         rates = sorted(goose_dict)
#         raise ValueError(
#            (f"Goose rate {goose_rate} is not one of the available goose "
#             f"rates: {rates}")
#
#     seqcodes = {0: f"Bay {bay}" + " On Time,1:" + f"Bay {bay}" + " Off Time"}
#     inst = make_sequence(
#         base_dict[base_rate], goose_dict[goose_rate], offset
#     )
#
#     print(seqcodes)
#     print(inst)
#
#     # Get descset from XPM, pass to execute
