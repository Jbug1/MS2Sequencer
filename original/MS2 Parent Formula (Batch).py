#!/usr/bin/env python3
import os
import sys
import re
import csv
import time
import importlib.util
from collections import defaultdict
from datetime import datetime

import numpy as np
import pandas as pd

# -------------------------------------------------
# CLI ARGS (match node JSON order)
# -------------------------------------------------
#  1: mgf_path
#  2: elements_tsv_path
#  3: delta_solver_py_path
#  4: max_mz_delta
#  5: ppm_tolerance
#  6: element_bounds_str
#  7: min_rel_intensity_pct
#  8: max_start_mz
#  9: beam_width
# 10: min_intensity
# 11: ppm_model            <-- NEW (optional; default "path_fit")
pickle_path = sys.argv[1]
elements_path = sys.argv[2]
delta_solver_path = sys.argv[3]
max_mz_delta = float(sys.argv[4])
ppm_tolerance = float(sys.argv[5])
element_bounds_str = sys.argv[6]
min_rel_intensity_pct = float(sys.argv[7])
max_start_mz = float(sys.argv[8])
beam_width = int(sys.argv[9])
min_intensity = float(sys.argv[10])
ppm_model = (sys.argv[11].strip().lower() if len(sys.argv) > 11 else "path_fit")
if ppm_model not in ["path_fit", "per_edge", "global_fixed"]:
    ppm_model = "path_fit"  # safety default

# -------------------------------------------------
# Outputs
# -------------------------------------------------
out_dir = os.path.join(os.getcwd(), "output")
features_dir = os.path.join(out_dir, "features")
details_dir = os.path.join(out_dir, "details")
debug_dir = os.path.join(out_dir, "debug")
os.makedirs(features_dir, exist_ok=True)
os.makedirs(details_dir, exist_ok=True)
os.makedirs(debug_dir, exist_ok=True)

features_path = os.path.join(features_dir, "features.tsv")
details_path  = os.path.join(details_dir, "details.tsv")
log_path_main = os.path.join(debug_dir, "debug.txt")

# Create stub debug files so Executive always sees outputs
open(log_path_main, "w").write("[{}] batch start (PPM mode={}, hybrid+singleton seeding, force PEPMASS, min_intensity, BasePeak)\n".format(
    datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ppm_model))
open(os.path.join(features_dir, "debug.txt"), "w").write("features socket debug stub\n")
open(os.path.join(details_dir, "debug.txt"), "w").write("details socket debug stub\n")

def log(msg):
    stamp = "[{}] | ".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    with open(log_path_main, "a") as f:
        f.write(stamp + msg + "\n")

def write_header_if_needed(path, header_cols):
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        with open(path, "w", newline="") as f:
            w = csv.writer(f, delimiter="\t")
            w.writerow(header_cols)

# -------------------------------------------------
# Import delta_solver module
# -------------------------------------------------
log("loading delta_solver module: {}".format(delta_solver_path))
spec = importlib.util.spec_from_file_location("delta_solver", delta_solver_path)
delta_solver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(delta_solver)

parse_bounds = delta_solver.parse_bounds
load_element_masses = delta_solver.load_element_masses
find_delta_formulas = delta_solver.find_delta_formulas
# Expected signature:
#   find_delta_formulas(obs_delta_mz: float, ppm_tolerance: float, element_bounds, element_masses)
# Expected keys per match: "delta_formula", "ppm_error"

element_bounds = parse_bounds(element_bounds_str)
element_masses = load_element_masses(elements_path)
log("element bounds and masses loaded")

# -------------------------------------------------
# Helpers
# -------------------------------------------------
mz_int_line_re = re.compile(r"^\s*([0-9]*\.?[0-9]+)\s+([0-9]*\.?[0-9]+)\s*$")

def parse_title_polarity(title_line):
    if title_line and "=" in title_line:
        payload = title_line.strip().split("=", 1)[1]
        if "." in payload:
            last = payload.strip().split(".")[-1]
            if last and last[0] in ["+", "-"]:
                return last[0], payload
        return None, payload
    return None, title_line or ""

def parse_charge_polarity(charge_line):
    if not charge_line or "=" not in charge_line:
        return None
    payload = charge_line.strip().split("=", 1)[1].strip()
    if payload.endswith("+") and payload.startswith("127"):
        return "+"
    if payload.endswith("-") and payload.startswith("128"):
        return "-"
    return None

def ion_type_from_polarity(sign):
    return "[M]+" if sign == "+" else "[M]-"

def parse_formula(formula_str):
    parts = re.findall(r"([A-Z][a-z]*)(-?\d+)", str(formula_str))
    return {el: int(cnt) for el, cnt in parts}

def formula_to_str(fdict):
    elems = sorted([e for e, v in fdict.items() if v != 0])
    return "".join("{}{}".format(el, fdict[el]) for el in elems) if elems else ""

def add_formulas(f1, f2):
    res = defaultdict(int, f1)
    for el, cnt in f2.items():
        res[el] += cnt
    return dict(res)

def has_negative_counts(fdict):
    return any(v < 0 for v in fdict.values())

def robust_median(vals):
    if not vals:
        return 0.0
    return float(np.median(np.array(vals, dtype=float)))

# -------------------------------------------------
# Sequencer-style edge builder (high -> low)
# -------------------------------------------------
def build_edges_from_peaks(mzs_desc, max_delta, ppm_tol):
    rows = []
    n = len(mzs_desc)
    slow_call_threshold = 1.0  # seconds, logging only
    for i in range(n):
        mz1 = mzs_desc[i]
        for j in range(i + 1, n):
            mz2 = mzs_desc[j]
            delta = mz1 - mz2
            if delta < 0:
                continue
            entry = {"Fragment_1": mz1, "Fragment_2": mz2, "Matched": "", "PPM_Errors": ""}
            if delta <= max_delta:
                t0 = time.time()
                matches = find_delta_formulas(delta, ppm_tol, element_bounds, element_masses)
                dt = time.time() - t0
                if dt > slow_call_threshold:
                    log("solver slow: delta={:.10f} took {:.3f}s".format(delta, dt))
                if matches:
                    entry["Matched"]    = ", ".join(m["delta_formula"] for m in matches)
                    entry["PPM_Errors"] = ", ".join(str(m.get("ppm_error", "")) for m in matches)
                else:
                    entry["Matched"] = "No match"
            else:
                entry["Matched"] = "Delta > threshold"
            rows.append(entry)
    df = pd.DataFrame(rows)
    df = df[df["Matched"].notna() & df["PPM_Errors"].notna()].copy()
    df = df[~df["Matched"].astype(str).str.contains("Delta > threshold", na=False)].copy()
    df = df[~df["Matched"].astype(str).str.contains("No match", na=False)].copy()
    return df

# -------------------------------------------------
# Beam inference with coverage (force PEPMASS)
# HYBRID + SINGLETON seeding in PPM mode
# -------------------------------------------------
def beam_infer_parent_with_coverage(edges_df, rel_series, max_start_mz, ppm_tol, beam_width,
                                    parent_mz, ppm_model="path_fit", parent_mz_tol=1e-4):
    if edges_df.empty:
        return None, None, {}, {
            "num_edges": 0, "num_paths": 0,
            "ppm_offset": 0.0, "coverage_pct": 0.0
        }

    df = edges_df.copy()
    df["Formula_list"] = df["Matched"].apply(
        lambda x: [parse_formula(f.strip()) for f in str(x).split(",") if f.strip() != ""]
    )
    df["PPM_list"] = df["PPM_Errors"].apply(
        lambda x: [float(p.strip()) for p in str(x).split(",") if p.strip() != ""]
    )

    # reverse edge direction (low -> high)
    up = pd.DataFrame({
        "Fragment_1": df["Fragment_2"].astype(float),
        "Fragment_2": df["Fragment_1"].astype(float),
        "Formula_list": df["Formula_list"],
        "PPM_list": df["PPM_list"]
    })

    # Candidate seeds (by source node) no higher than max_start_mz
    sources = set(up["Fragment_1"].astype(float).tolist())
    seed_frags = sorted([mz for mz in sources if mz <= max_start_mz])

    # Base from 0.0 -> seed (singleton median defines GLOBAL offset if used)
    base_map = defaultdict(list)
    zero_to_seed = up[up["Fragment_1"] == 0.0].copy()
    for _, row in zero_to_seed.iterrows():
        dest = float(row["Fragment_2"])
        for fml, ppm in zip(row["Formula_list"], row["PPM_list"]):
            base_map[dest].append((fml, ppm))

    def f_key(fd):
        return formula_to_str(fd)

    singleton_seeds = []
    for dest, lst in base_map.items():
        uniq = {}
        for fml, ppm_err in lst:
            uniq.setdefault(f_key(fml), []).append((fml, ppm_err))
        if len(uniq) == 1:
            singleton_seeds.append(dest)
    singleton_set = set(singleton_seeds)

    # GLOBAL offset from singleton seeds (only used if ppm_model == "global_fixed")
    seed_ppms_all = []
    for dest in singleton_seeds:
        best_ppm = min((ppm for _, ppm in base_map.get(dest, [])), key=lambda e: abs(e))
        seed_ppms_all.append(best_ppm)
    global_ppm_offset = float(np.median(seed_ppms_all)) if seed_ppms_all else 0.0

    target_parent_mz = float(parent_mz) if parent_mz is not None else 0.0

    # Initialize beams
    beams = defaultdict(list)
    for frag in seed_frags:
        if frag in singleton_set:
            best_ppm = min((ppm for _, ppm in base_map[frag]), key=lambda e: abs(e))
            base_f = base_map[frag][0][0]
            beams[frag].append({
                "path": [(frag, base_f, best_ppm)],
                "errors": [best_ppm]
            })
        else:
            beams[frag].append({
                "path": [(frag, {}, None)],
                "errors": []
            })

    if not any(beams.values()):
        return None, None, {}, {
            "num_edges": int(len(up)),
            "num_paths": 0,
            "ppm_offset": (global_ppm_offset if ppm_model == "global_fixed" else 0.0),
            "coverage_pct": 0.0,
            "no_seeds": True,
            "num_seed_frags": len(seed_frags),
            "num_singleton_seeds": len(singleton_seeds),
        }

    TOTAL_REL = float(rel_series.sum())
    def path_coverage_pct(state):
        mzs = [float(x[0]) for x in state["path"]]
        mzs = [m for m in mzs if m != 0.0]
        unique = set(mzs)
        if TOTAL_REL <= 0.0 or not unique:
            return 0.0
        return float(rel_series.reindex(list(unique)).fillna(0.0).sum()) / TOTAL_REL * 100.0

    def is_target_parent(x, tol=parent_mz_tol):
        return abs(float(x) - target_parent_mz) <= tol

    def gate_ok(ppm_err, model, global_off, tol):
        if ppm_err is None:
            return False
        if model == "global_fixed":
            return abs(ppm_err - global_off) <= tol
        else:
            # per_edge and path_fit: gate by raw ppm only
            return abs(ppm_err) <= tol

    def state_epsilon_hat(state, model):
        if model == "global_fixed":
            return global_ppm_offset
        # for path_fit, use robust median of accumulated errors; for per_edge, 0.0
        return robust_median(state["errors"]) if (model == "path_fit" and state["errors"]) else 0.0

    final_paths_all = []
    while any(beams.values()):
        new_beams = defaultdict(list)
        for node_mz, states in beams.items():
            outs = up[up["Fragment_1"] == node_mz]
            if outs.empty:
                continue
            for state in states:
                last_frag, last_formula, _ = state["path"][-1]
                for _, e_row in outs.iterrows():
                    dest  = float(e_row["Fragment_2"])
                    flist = e_row["Formula_list"]
                    plist = e_row["PPM_list"]
                    for cand_formula, ppm_err in zip(flist, plist):
                        new_formula = add_formulas(last_formula, cand_formula)
                        if has_negative_counts(new_formula):
                            continue
                        if not gate_ok(ppm_err, ppm_model, global_ppm_offset, ppm_tolerance):
                            continue
                        new_state = {
                            "path": state["path"] + [(dest, new_formula, ppm_err)],
                            "errors": state["errors"] + ([] if ppm_err is None else [ppm_err])
                        }
                        if is_target_parent(dest):
                            final_paths_all.append(new_state)
                        else:
                            new_beams[dest].append(new_state)

        # prune per node by beam width
        beams = {}
        for nid, sts in new_beams.items():
            def mae_ppm(st):
                eps = state_epsilon_hat(st, ppm_model)
                errs = st["errors"]
                return sum(abs(e - eps) for e in errs) / max(1, len(errs))
            def stdev_ppm(st):
                eps = state_epsilon_hat(st, ppm_model)
                errs = [e - eps for e in st["errors"]]
                return float(np.std(errs)) if errs else 0.0
            scored = sorted(
                sts,
                key=lambda s: (
                    mae_ppm(s),
                    stdev_ppm(s),
                    -len(s["path"])
                )
            )
            beams[nid] = scored[:beam_width]
        if not beams:
            break

    # Prefer anchored paths; fallback if none
    anchored_final_paths = [st for st in final_paths_all if st["path"][0][0] in singleton_set]
    anchor_missing = False
    final_paths = anchored_final_paths if anchored_final_paths else final_paths_all
    if not anchored_final_paths:
        anchor_missing = True

    def path_sig(st): return tuple(x[0] for x in st["path"])
    votes = defaultdict(set)
    for st in final_paths:
        pf = formula_to_str(st["path"][-1][1])
        votes[pf].add(path_sig(st))

    def mae_ppm_with(st):
        eps = state_epsilon_hat(st, ppm_model)
        errs = st["errors"]
        return (sum(abs(e - eps) for e in errs) / max(1, len(errs))), eps

    def stdev_ppm_with(st, eps):
        errs = [e - eps for e in st["errors"]]
        return float(np.std(errs)) if errs else 0.0

    paths_by_formula = defaultdict(list)
    for st in final_paths:
        paths_by_formula[formula_to_str(st["path"][-1][1])].append(st)

    if not paths_by_formula:
        return None, None, {}, {
            "num_edges": len(up),
            "num_paths": 0,
            "ppm_offset": (global_ppm_offset if ppm_model == "global_fixed" else 0.0),
            "coverage_pct": 0.0,
            "num_seed_frags": len(seed_frags),
            "num_singleton_seeds": len(singleton_seeds),
            "anchor_missing": anchor_missing,
        }

    best_path_for_formula = {}
    path_epsilons = {}
    for pf, plist in paths_by_formula.items():
        # compute eps and metrics for ordering inside this formula
        def key_fn(s):
            mae, eps = mae_ppm_with(s)
            sd = stdev_ppm_with(s, eps)
            return (path_coverage_pct(s), -mae, -sd, len(s["path"]))
        best = max(plist, key=key_fn)
        best_path_for_formula[pf] = best
        path_epsilons[pf] = state_epsilon_hat(best, ppm_model)

    ordered = sorted(
        best_path_for_formula.keys(),
        key=lambda pf: (
            -len(votes.get(pf, set())),
            -path_coverage_pct(best_path_for_formula[pf]),
            mae_ppm_with(best_path_for_formula[pf])[0],
            stdev_ppm_with(best_path_for_formula[pf], path_epsilons[pf]),
            -len(best_path_for_formula[pf]["path"])
        )
    )
    top_pf = ordered[0]
    winner = best_path_for_formula[top_pf]

    # Report the relevant offset for the winner (for details.tsv)
    winner_eps = path_epsilons.get(top_pf, 0.0) if ppm_model != "global_fixed" else global_ppm_offset

    stats = {
        "num_edges": len(up),
        "num_paths": len([1 for _ in final_paths_all]),
        "ppm_offset": float(winner_eps if ppm_model in ["path_fit"] else (global_ppm_offset if ppm_model == "global_fixed" else 0.0)),
        "votes_map": {k: len(v) for k, v in votes.items()},
        "coverage_pct": float(path_coverage_pct(winner)),
        "num_seed_frags": len(seed_frags),
        "num_singleton_seeds": len(singleton_seeds),
        "anchor_missing": anchor_missing,
        "ppm_model": ppm_model,
    }
    return top_pf, winner, votes, stats

# -------------------------------------------------
# Main
# -------------------------------------------------
def main():
    # Headers
    write_header_if_needed(features_path, ["Metabolite", "Formula", "Ion Type", "RT (min)", "Scan"])
    write_header_if_needed(details_path,  [
        "Scan","PEPMASS","TopFormula","Votes","Coverage(%)",
        "MAE_ppm","PathLength",
        "NumPeaksKept","NumEdges","NumUniquePaths",
        "Path_mz_seq","Path_formula_seq","Path_ppm_seq",
        "BasePeak","ppm_offset_baseline","ppm_model"
    ])

    log("reading MGF into RAM: {}".format(mgf_path))
    log("ppm_model = {}".format(ppm_model))
    blocks = parse_mgf_to_blocks(mgf_path)
    log("parsed {} scan(s)".format(len(blocks)))

    for idx, (meta, peaks) in enumerate(blocks, start=1):
        title_line = meta.get("TITLE")
        charge_line = meta.get("CHARGE")
        pepmass = meta.get("PEPMASS")
        rt_seconds = meta.get("RTINSECONDS")

        # Base-peak intensity filter (skip weak scans)
        base_peak = max((inten for _, inten in peaks), default=0.0)
        if base_peak < min_intensity:
            log("scan {}: skipped due to min_intensity (base_peak={} < {})".format(idx, base_peak, min_intensity))
            continue

        log("scan {}: begin (peaks={}, base_peak={})".format(idx, len(peaks), base_peak))

        # polarity
        sign, title_payload = parse_title_polarity(title_line)
        if sign is None:
            sign = parse_charge_polarity(charge_line)
        if sign not in ["+", "-"]:
            sign = "+"
        ion_type = ion_type_from_polarity(sign)
        log("scan {}: polarity={}, ion_type={}".format(idx, sign, ion_type))

        # relative intensities
        rel_peaks = []
        if base_peak > 0.0:
            for mz, inten in peaks:
                rel = (inten / base_peak) * 100.0
                if rel >= min_rel_intensity_pct:
                    rel_peaks.append((float(mz), rel))

        # Insert PEPMASS if not present
        if pepmass is not None:
            tol = 1e-4
            present = any(abs(mz - float(pepmass)) <= tol for mz, _ in rel_peaks)
            if not present:
                rel_peaks.append((float(pepmass), 100.0))
                log("scan {}: parent m/z {:.4f} inserted at 100.0% (not in peak list)".format(idx, float(pepmass)))
            else:
                log("scan {}: parent m/z {:.4f} found in peak list".format(idx, float(pepmass)))
        else:
            log("scan {}: WARNING no PEPMASS parsed; cannot enforce parent m/z presence")

        # Synthetic 0.0 m/z base
        rel_peaks.append((0.0, 100.0))
        log("scan {}: peaks kept (incl parent check and 0.0) = {}".format(idx, len(rel_peaks)))

        # coverage series (exclude 0.0)
        rel_series = pd.Series({mz: rel for mz, rel in rel_peaks})
        if 0.0 in rel_series.index:
            rel_series = rel_series.drop(index=0.0)
        log("scan {}: TOTAL_REL = {:.4f}".format(idx, float(rel_series.sum())))

        # edges
        mzs_desc = sorted([mz for mz, _ in rel_peaks], reverse=True)
        log("scan {}: building edges".format(idx))
        edges_df = build_edges_from_peaks(mzs_desc, max_mz_delta, ppm_tolerance)
        log("scan {}: edges built = {}".format(idx, len(edges_df)))

        # infer (force PEPMASS as parent target)
        log("scan {}: beam infer (forcing parent target {:.4f})".format(idx, float(pepmass) if pepmass is not None else float("nan")))
        top_formula, winner_state, votes_map, stats = beam_infer_parent_with_coverage(
            edges_df, rel_series, max_start_mz, ppm_tolerance, beam_width,
            parent_mz=pepmass, ppm_model=ppm_model, parent_mz_tol=1e-4
        )

        if stats.get("no_seeds"):
            log("scan {}: no seeds; #seed_frags={}, #singleton_seeds={}".format(
                idx, stats.get("num_seed_frags", -1), stats.get("num_singleton_seeds", -1)))
            continue

        log("scan {}: final paths = {}, votes_map = {}".format(
            idx, stats.get("num_paths", 0), stats.get("votes_map", {})))
        log("scan {}: winner = {}, coverage = {:.2f}%, ppm_offset = {:.4f}, model={}, seed_frags={}, singleton_seeds={}, anchor_missing={}".format(
            idx, top_formula if top_formula else "NA", stats.get("coverage_pct", 0.0),
            stats.get("ppm_offset", 0.0), stats.get("ppm_model", ppm_model),
            stats.get("num_seed_frags", -1), stats.get("num_singleton_seeds", -1),
            stats.get("anchor_missing", False)
        ))

        # features row
        rt_min = round(float(rt_seconds) / 60.0, 2)
        rt_min_name = round(float(rt_seconds) / 60.0, 1)
        metabolite_name = "Parent_{}_{}".format(top_formula if top_formula else "NA", rt_min_name)
        with open(features_path, "a", newline="") as f:
            w = csv.writer(f, delimiter="\t")
            w.writerow([metabolite_name, top_formula if top_formula else "NA", ion_type, rt_min, title_payload or ""])

        # details row
        if winner_state is not None:
            mz_seq   = [str(x[0]) for x in winner_state["path"]]
            form_seq = [formula_to_str(x[1]) for x in winner_state["path"]]
            ppm_seq  = [("NA" if x[2] is None else "{:.4f}".format(x[2])) for x in winner_state["path"]]
            vcount   = len(votes_map.get(top_formula, set())) if top_formula else 0

            # MAE computed around reported baseline offset (stats["ppm_offset"])
            mae_ppm = 0.0
            if winner_state["errors"]:
                ppm_off = stats.get("ppm_offset", 0.0)
                mae_ppm = sum(abs(e - ppm_off) for e in winner_state["errors"]) / float(len(winner_state["errors"]))

            with open(details_path, "a", newline="") as f:
                w = csv.writer(f, delimiter="\t")
                w.writerow([
                    title_payload or "",
                    "{:.4f}".format(pepmass if pepmass is not None else float("nan")),
                    top_formula if top_formula else "NA",
                    vcount,
                    "{:.2f}".format(stats.get("coverage_pct", 0.0)),
                    "{:.4f}".format(mae_ppm),
                    len(winner_state["path"]),
                    len(rel_series),
                    stats.get("num_edges", 0),
                    stats.get("num_paths", 0),
                    "|".join(mz_seq), "|".join(form_seq), "|".join(ppm_seq),
                    "{:.0f}".format(base_peak),
                    "{:.4f}".format(stats.get("ppm_offset", 0.0)),
                    ppm_model
                ])
        else:
            with open(details_path, "a", newline="") as f:
                w = csv.writer(f, delimiter="\t")
                w.writerow([
                    title_payload or "",
                    "{:.4f}".format(pepmass if pepmass is not None else float("nan")),
                    "NA", 0, "0.00", "NA", 0,
                    len(rel_series),
                    0, 0,
                    "NA", "NA", "NA",
                    "{:.0f}".format(base_peak),
                    "{:.4f}".format(0.0),
                    ppm_model
                ])

        log("scan {}: done".format(idx))

    log("All scans processed.")

if __name__ == "__main__":
    log("Starting MS2 Parent Formula Batch (PPM mode={}, hybrid+singleton seeding, force PEPMASS, min_intensity, BasePeak)...".format(ppm_model))
    main()
    log("Done.")
