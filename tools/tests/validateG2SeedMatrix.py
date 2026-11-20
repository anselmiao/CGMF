#!/usr/bin/env python3
"""Validate that same-condition CI cases use disjoint RNG seed ranges."""
import argparse, json
from decimal import Decimal, InvalidOperation
from pathlib import Path


def validate_seed_ranges(cases, default_events=40):
    groups={}
    for case in cases:
        name=case["name"]
        try: energy=Decimal(str(case["energy_MeV"]))
        except InvalidOperation as exc: raise ValueError(f"{name}: invalid incident energy") from exc
        key=(int(case["ZAID"]),energy)
        start=int(case.get("seed_start",1))
        count=int(case.get("events",default_events))
        if start<1 or count<1: raise ValueError(f"{name}: seed_start and events must be positive")
        end=start+count-1
        for old_start,old_end,old_name in groups.setdefault(key,[]):
            if max(start,old_start)<=min(end,old_end):
                raise ValueError(f"{name}: RNG seed range {start}-{end} overlaps {old_name} range {old_start}-{old_end} for same ZAID/energy")
        groups[key].append((start,end,name))
    return {f"{k[0]}@{format(k[1], 'f')}":sorted(v) for k,v in groups.items()}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("matrix",type=Path); a=ap.parse_args()
    d=json.loads(a.matrix.read_text(encoding="utf-8"))
    groups=validate_seed_ranges(d["cases"],d.get("default_events",40))
    print(f"RNG seed ranges valid: {sum(map(len,groups.values()))} cases; no same-condition overlaps")

if __name__=="__main__": main()
