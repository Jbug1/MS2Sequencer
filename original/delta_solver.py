import pandas as pd
import itertools
import re

SCALE = 10000  # Integer scaling factor for mass precision

# Parse user-supplied element bounds (e.g. "C[-5,5], H[-10,10]")
def parse_bounds(bounds_str):
    pattern = re.compile(r"([A-Z][a-z]?)\[\s*(-?\d+)\s*,\s*(-?\d+)\s*\]")
    bounds = {}
    for match in pattern.finditer(bounds_str):
        element, min_val, max_val = match.groups()
        bounds[element] = (int(min_val), int(max_val))
    return bounds

# Load monoisotopic masses from a TSV file with Symbol and mz columns
def load_element_masses(path):
    df = pd.read_csv(path, sep="\t")
    return dict(zip(df["Symbol"], df["mz"]))

# Core search function to find formulas matching a delta mass
def find_delta_formulas(delta_mass, ppm_tolerance, element_bounds, element_masses):
    target_mass_i = int(round(delta_mass * SCALE))
    ppm_window = int(round(delta_mass * ppm_tolerance * SCALE / 1e6))
    
    elements = [e for e in element_bounds if e in element_masses]
    mass_table = {e: int(round(element_masses[e] * SCALE)) for e in elements}
    bound_table = {e: element_bounds[e] for e in elements}

    element_ranges = [range(bound_table[e][0], bound_table[e][1] + 1) for e in elements]
    results = []

    for coeffs in itertools.product(*element_ranges):
        if all(c == 0 for c in coeffs):
            continue  # Skip empty formula

        total_mass = sum(c * mass_table[e] for c, e in zip(coeffs, elements))
        delta = total_mass - target_mass_i
        ppm_error = (delta / target_mass_i) * 1e6

        if abs(ppm_error) <= ppm_tolerance:
            coeff_dict = {e: coeffs[i] for i, e in enumerate(elements)}
            delta_formula = "".join([f"{e}{v:+d}".replace("+", "") for e, v in coeff_dict.items() if v != 0])
            
            result = {
                "ppm_error": round(ppm_error, 2),
                "delta_mass": round(delta / SCALE, 6),
                "delta_formula": delta_formula
            }
            for e in elements:
                result[e] = coeff_dict[e]

            results.append(result)

    return results
