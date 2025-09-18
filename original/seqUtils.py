import itertools
import numpy as np
from collections import defaultdict

def build_delta_dict(element_masses, element_limits, precision_limit):

    #get possible deltas for each element
    masses = np.zeros(len(element_masses))

    #build delta list in order
    element_deltas = list()
    i = 0
    for element, mass in element_masses.items():

        #add the mz for this element
        masses[i] = round(mass, precision_limit)

        #get an array of all possible element count changes
        element_deltas.append(list(range(element_limits[element][0], element_limits[element][1] + 1)))

    #get all possible combinations of individual element count changes
    element_deltas = np.array(list(itertools.product(*element_deltas)))

    #get mass of each combination
    delta_masses = element_deltas @ masses

    #create mapping of delta value to possible compositions
    delta_dict = defaultdict(list)
    for delta, element_composition in zip(delta_masses, element_deltas):

        delta_dict[delta].append(element_composition)








                    




def find_delta_formulas(delta_mass, ppm_tolerance, element_bounds, element_masses):

    target_mass_i = int(round(delta_mass))
    ppm_window = int(round(delta_mass * ppm_tolerance/ 1e6))
    
    elements = [e for e in element_bounds if e in element_masses]
    mass_table = {e: round(element_masses[e], precision_limit) for e in elements}
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