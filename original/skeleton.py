import sys
import os
import time
import sqlite3

# EMBEDDED: import columns

class Thing:
    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, value):
        setattr(self, key, value)


def enum(options):
    values = options.split(" ")

    def __effectively_enums_are_strings__(element):
        if element in values:
            return str(element)
        print(f"Invalid value: {element} is not one of: {options}", sys.stderr)
        sys.exit(-1)

    return __effectively_enums_are_strings__


def loader(filename, header_description):
    for available in header_description:
        assert header_description[available]["field"] != "rest_of_row"
    f = open(filename)
    headers = f.readline().strip(" \r\n").split("\t")
    header_count = len(headers)
    to_parse = {}
    matched = {}
    matched_headers = []
    unexpected = []
    unmatched = []
    for (offset, header) in enumerate(headers):
        matched_it = False
        for available in header_description:
            if header == available:
                to_parse[offset] = header_description[available]
                matched[header_description[available]["field"]] = offset
                matched_headers.append(available)
                matched_it = True
                break
        if not matched_it:
            unexpected.append(header)
            to_parse[offset] = None
    for available in header_description:
        if available not in matched_headers:
            if header_description[available]["required"]:
                print(
                    f'Required header "{available}" was not found in the headers of {filename}!!!',
                    file=sys.stderr,
                )
                sys.exit(-1)
            else:
                unmatched.append(header_description[available]["field"])

    rows = []
    for line in f:
        new_row = Thing()
        vals = line.strip(" \r\n").split("\t")
        others = []
        for i in range(header_count):
            if to_parse[i]:
                new_row[to_parse[i]["field"]] = (to_parse[i]["constructor"])(vals[i])
            else:
                others.append(vals[i])
        if others:
            new_row["rest_of_row"] = "\t".join(others)
        rows.append(new_row)
    return (rows, unmatched, unexpected)


# EMBEDDED: import actions

elements = {"Ag": 106.905095,
            "Al": 26.981541,
            "Ar": 39.962383,
            "As": 74.921596,
            "Au": 196.96656,
            "B": 11.009305,
            "Ba": 137.905236,
            "Be": 9.012183,
            "Bi": 208.980388,
            "Br": 78.918336,
            "C": 12,
            "Ca": 39.962591,
            "Cd": 113.903361,
            "Ce": 139.905442,
            "Cl": 34.968853,
            "Co": 58.933198,
            "Cr": 51.94051,
            "Cs": 132.905433,
            "Cu": 62.929599,
            "D": 2.01355321274,
            "Dy": 163.929183,
            "e": 0.00054858,
            "Er": 165.930305,
            "Eu": 152.921243,
            "F": 18.998403,
            "Fe": 55.934939,
            "Ga": 68.925581,
            "Gd": 157.924111,
            "Ge": 73.921179,
            "H": 1.007825,
            "He": 4.002603,
            "Hf": 179.946561,
            "Hg": 201.970632,
            "Ho": 164.930332,
            "I": 126.904477,
            "In": 114.903875,
            "Ir": 192.962942,
            "K": 38.963708,
            "Kr": 83.911506,
            "La": 138.906355,
            "Li": 7.016005,
            "Lu": 174.940785,
            "Mg": 23.985045,
            "Mn": 54.938046,
            "Mo": 97.905405,
            "N": 14.003074,
            "Na": 22.98977,
            "Nb": 92.906378,
            "Nd": 141.907731,
            "Ne": 19.992439,
            "Ni": 57.935347,
            "O": 15.994915,
            "Os": 191.961487,
            "P": 30.973763,
            "Pb": 207.976641,
            "Pd": 105.903475,
            "Pr": 140.907657,
            "Pt": 194.964785,
            "Rb": 84.9118,
            "Re": 186.955765,
            "Rh": 102.905503,
            "Ru": 101.904348,
            "S": 31.972072,
            "Sb": 120.903824,
            "Sc": 44.955914,
            "Se": 79.916521,
            "Si": 27.976928,
            "Sm": 151.919741,
            "Sn": 119.902199,
            "Sr": 87.905625,
            "Ta": 180.948014,
            "Tb": 158.92535,
            "Te": 129.906229,
            "Th": 232.038054,
            "Ti": 47.947947,
            "Tl": 204.97441,
            "Tm": 168.934225,
            "U": 238.050786,
            "V": 50.943963,
            "W": 183.950953,
            "Xe": 131.904148,
            "Y": 88.905856,
            "Yb": 173.938873,
            "Zn": 63.929145,
            "Zr": 89.904708}


class Actions():
    def make_element(self, text, start, end):
        # print("element mass", text[start:end], elements[text[start:end]])
        return elements[text[start:end]]

    def make_term(self, _text, _start, _end, elements):
        if elements[1].text == "":
            # print("term mass:", elements[0])
            return elements[0]
        # print("term mass:", int(elements[1].text) * elements[0])
        return int(elements[1].text) * elements[0]

    def make_sub_formula(self, _text, _start, _end, elements):
        total = 0.0
        for e in elements[1]:
            total += e
        # print("sub_formula mass:", total)
        return total

    def make_ion_type(self, text, start, end, elements):
        total = 0.0
        for component in elements[3]:
            plus_minus = component.elements[0].text
            other_part = component.elements[1]
            if isinstance(other_part, float):
                if plus_minus == "+":
                    total += other_part
                else:
                    total -= other_part
            else:
                if other_part.elements[0].text == "":
                    multiplier = 1
                else:
                    multiplier = int(other_part.elements[0].text)
                if other_part.elements[1].text == "(":
                    sub_total = other_part.elements[2]
                else:
                    sub_total = 0.0
                    for e in other_part.elements[1]:  # TODO: Deal with case of count "(" mass ")"
                        # print("sub_total:", e)
                        sub_total += e
                if plus_minus == "+":
                    total += multiplier * sub_total
                else:
                    total -= multiplier * sub_total
                # for e in other_part.elements:
                #     print("subpart", e.text)
        mol_count = 1
        if elements[1].text != "":
            mol_count = int(elements[1].text)
        return {"molecular_ion": elements[2].text, "molecular_ion_count": mol_count, "delta_formula": elements[3].text, "delta": total, "z": elements[5].text}

    def make_mass(self, text, start, end, elements):
        # print("make mass:", self, text, start, end, elements)
        return float(text[start:end])


# EMBEDDED: import formula_actions

class Formula_Actions():
    def make_element(self, text, start, end):
        # print("element mass", text[start:end], elements[text[start:end]])
        return {"mass": elements[text[start:end]], "atom": text[start:end]}

    def make_term(self, _text, _start, _end, elements):
        if elements[1].text == "":
            # print("term mass:", elements[0])
            return {"mass": elements[0]["mass"], "atom": elements[0]["atom"], "count": 1}
        # print("term mass:", int(elements[1].text) * elements[0])
        the_count = int(elements[1].text)
        return {"mass": elements[0]["mass"] * the_count, "atom": elements[0]["atom"], "count": the_count}


# EMBEDDED: import nist_ion_descriptions

from collections import defaultdict
import re


class nist_ion_descriptions_TreeNode(object):
    def __init__(self, text, offset, elements=None):
        self.text = text
        self.offset = offset
        self.elements = elements or []

    def __iter__(self):
        for el in self.elements:
            yield el


class nist_ion_descriptions_TreeNode1(nist_ion_descriptions_TreeNode):
    def __init__(self, text, offset, elements):
        super(nist_ion_descriptions_TreeNode1, self).__init__(text, offset, elements)
        self.count = elements[1]
        self.molecular_ion = elements[2]
        self.formulae = elements[3]
        self.charge_state = elements[5]
        self.radical = elements[6]


class nist_ion_descriptions_TreeNode2(nist_ion_descriptions_TreeNode):
    def __init__(self, text, offset, elements):
        super(nist_ion_descriptions_TreeNode2, self).__init__(text, offset, elements)
        self.plus_minus = elements[0]


class nist_ion_descriptions_TreeNode3(nist_ion_descriptions_TreeNode):
    def __init__(self, text, offset, elements):
        super(nist_ion_descriptions_TreeNode3, self).__init__(text, offset, elements)
        self.count = elements[0]
        self.formula = elements[1]


class nist_ion_descriptions_TreeNode4(nist_ion_descriptions_TreeNode):
    def __init__(self, text, offset, elements):
        super(nist_ion_descriptions_TreeNode4, self).__init__(text, offset, elements)
        self.count = elements[0]
        self.mass = elements[2]


class nist_ion_descriptions_TreeNode5(nist_ion_descriptions_TreeNode):
    def __init__(self, text, offset, elements):
        super(nist_ion_descriptions_TreeNode5, self).__init__(text, offset, elements)
        self.count = elements[0]
        self.plus_minus = elements[1]


class nist_ion_descriptions_TreeNode6(nist_ion_descriptions_TreeNode):
    def __init__(self, text, offset, elements):
        super(nist_ion_descriptions_TreeNode6, self).__init__(text, offset, elements)
        self.count = elements[1]


class nist_ion_descriptions_TreeNode7(nist_ion_descriptions_TreeNode):
    def __init__(self, text, offset, elements):
        super(nist_ion_descriptions_TreeNode7, self).__init__(text, offset, elements)
        self.formula = elements[1]


class nist_ion_descriptions_TreeNode8(nist_ion_descriptions_TreeNode):
    def __init__(self, text, offset, elements):
        super(nist_ion_descriptions_TreeNode8, self).__init__(text, offset, elements)
        self.non_zero_digit = elements[0]


class nist_ion_descriptions_TreeNode9(nist_ion_descriptions_TreeNode):
    def __init__(self, text, offset, elements):
        super(nist_ion_descriptions_TreeNode9, self).__init__(text, offset, elements)
        self.decimal = elements[1]


class nist_ion_descriptions_ParseError(SyntaxError):
    pass


FAILURE = object()


class nist_ion_descriptions_Grammar(object):
    REGEX_1 = re.compile('^[1-9]')
    REGEX_2 = re.compile('^[0-9]')

    def _read_ion_type(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['ion_type'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        index1, elements0 = self._offset, []
        address1 = FAILURE
        chunk0 = None
        if self._offset < self._input_size:
            chunk0 = self._input[self._offset:self._offset + 1]
        if chunk0 == '[':
            address1 = nist_ion_descriptions_TreeNode(self._input[self._offset:self._offset + 1], self._offset)
            self._offset = self._offset + 1
        else:
            address1 = FAILURE
            if self._offset > self._failure:
                self._failure = self._offset
                self._expected = []
            if self._offset == self._failure:
                self._expected.append('"["')
        if address1 is not FAILURE:
            elements0.append(address1)
            address2 = FAILURE
            address2 = self._read_count()
            if address2 is not FAILURE:
                elements0.append(address2)
                address3 = FAILURE
                address3 = self._read_molecular_ion()
                if address3 is not FAILURE:
                    elements0.append(address3)
                    address4 = FAILURE
                    address4 = self._read_formulae()
                    if address4 is not FAILURE:
                        elements0.append(address4)
                        address5 = FAILURE
                        chunk1 = None
                        if self._offset < self._input_size:
                            chunk1 = self._input[self._offset:self._offset + 1]
                        if chunk1 == ']':
                            address5 = nist_ion_descriptions_TreeNode(self._input[self._offset:self._offset + 1], self._offset)
                            self._offset = self._offset + 1
                        else:
                            address5 = FAILURE
                            if self._offset > self._failure:
                                self._failure = self._offset
                                self._expected = []
                            if self._offset == self._failure:
                                self._expected.append('"]"')
                        if address5 is not FAILURE:
                            elements0.append(address5)
                            address6 = FAILURE
                            address6 = self._read_charge_state()
                            if address6 is not FAILURE:
                                elements0.append(address6)
                                address7 = FAILURE
                                address7 = self._read_radical()
                                if address7 is not FAILURE:
                                    elements0.append(address7)
                                else:
                                    elements0 = None
                                    self._offset = index1
                            else:
                                elements0 = None
                                self._offset = index1
                        else:
                            elements0 = None
                            self._offset = index1
                    else:
                        elements0 = None
                        self._offset = index1
                else:
                    elements0 = None
                    self._offset = index1
            else:
                elements0 = None
                self._offset = index1
        else:
            elements0 = None
            self._offset = index1
        if elements0 is None:
            address0 = FAILURE
        else:
            address0 = self._actions.make_ion_type(self._input, index1, self._offset, elements0)
            self._offset = self._offset
        self._cache['ion_type'][index0] = (address0, self._offset)
        return address0

    def _read_radical(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['radical'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        index1 = self._offset
        chunk0 = None
        if self._offset < self._input_size:
            chunk0 = self._input[self._offset:self._offset + 1]
        if chunk0 == '.':
            address0 = nist_ion_descriptions_TreeNode(self._input[self._offset:self._offset + 1], self._offset)
            self._offset = self._offset + 1
        else:
            address0 = FAILURE
            if self._offset > self._failure:
                self._failure = self._offset
                self._expected = []
            if self._offset == self._failure:
                self._expected.append('"."')
        if address0 is FAILURE:
            address0 = nist_ion_descriptions_TreeNode(self._input[index1:index1], index1)
            self._offset = index1
        self._cache['radical'][index0] = (address0, self._offset)
        return address0

    def _read_molecular_ion(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['molecular_ion'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        index1 = self._offset
        chunk0 = None
        if self._offset < self._input_size:
            chunk0 = self._input[self._offset:self._offset + 1]
        if chunk0 == 'M':
            address0 = nist_ion_descriptions_TreeNode(self._input[self._offset:self._offset + 1], self._offset)
            self._offset = self._offset + 1
        else:
            address0 = FAILURE
            if self._offset > self._failure:
                self._failure = self._offset
                self._expected = []
            if self._offset == self._failure:
                self._expected.append('"M"')
        if address0 is FAILURE:
            self._offset = index1
            chunk1 = None
            if self._offset < self._input_size:
                chunk1 = self._input[self._offset:self._offset + 3]
            if chunk1 == 'Cat':
                address0 = nist_ion_descriptions_TreeNode(self._input[self._offset:self._offset + 3], self._offset)
                self._offset = self._offset + 3
            else:
                address0 = FAILURE
                if self._offset > self._failure:
                    self._failure = self._offset
                    self._expected = []
                if self._offset == self._failure:
                    self._expected.append('"Cat"')
            if address0 is FAILURE:
                self._offset = index1
                chunk2 = None
                if self._offset < self._input_size:
                    chunk2 = self._input[self._offset:self._offset + 2]
                if chunk2 == 'An':
                    address0 = nist_ion_descriptions_TreeNode(self._input[self._offset:self._offset + 2], self._offset)
                    self._offset = self._offset + 2
                else:
                    address0 = FAILURE
                    if self._offset > self._failure:
                        self._failure = self._offset
                        self._expected = []
                    if self._offset == self._failure:
                        self._expected.append('"An"')
                if address0 is FAILURE:
                    self._offset = index1
        self._cache['molecular_ion'][index0] = (address0, self._offset)
        return address0

    def _read_formulae(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['formulae'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        remaining0, index1, elements0, address1 = 0, self._offset, [], True
        while address1 is not FAILURE:
            index2, elements1 = self._offset, []
            address2 = FAILURE
            address2 = self._read_plus_minus()
            if address2 is not FAILURE:
                elements1.append(address2)
                address3 = FAILURE
                index3 = self._offset
                index4, elements2 = self._offset, []
                address4 = FAILURE
                address4 = self._read_count()
                if address4 is not FAILURE:
                    elements2.append(address4)
                    address5 = FAILURE
                    address5 = self._read_formula()
                    if address5 is not FAILURE:
                        elements2.append(address5)
                    else:
                        elements2 = None
                        self._offset = index4
                else:
                    elements2 = None
                    self._offset = index4
                if elements2 is None:
                    address3 = FAILURE
                else:
                    address3 = nist_ion_descriptions_TreeNode3(self._input[index4:self._offset], index4, elements2)
                    self._offset = self._offset
                if address3 is FAILURE:
                    self._offset = index3
                    index5, elements3 = self._offset, []
                    address6 = FAILURE
                    address6 = self._read_count()
                    if address6 is not FAILURE:
                        elements3.append(address6)
                        address7 = FAILURE
                        chunk0 = None
                        if self._offset < self._input_size:
                            chunk0 = self._input[self._offset:self._offset + 1]
                        if chunk0 == '(':
                            address7 = nist_ion_descriptions_TreeNode(self._input[self._offset:self._offset + 1], self._offset)
                            self._offset = self._offset + 1
                        else:
                            address7 = FAILURE
                            if self._offset > self._failure:
                                self._failure = self._offset
                                self._expected = []
                            if self._offset == self._failure:
                                self._expected.append('"("')
                        if address7 is not FAILURE:
                            elements3.append(address7)
                            address8 = FAILURE
                            address8 = self._read_mass()
                            if address8 is not FAILURE:
                                elements3.append(address8)
                                address9 = FAILURE
                                chunk1 = None
                                if self._offset < self._input_size:
                                    chunk1 = self._input[self._offset:self._offset + 1]
                                if chunk1 == ')':
                                    address9 = nist_ion_descriptions_TreeNode(self._input[self._offset:self._offset + 1], self._offset)
                                    self._offset = self._offset + 1
                                else:
                                    address9 = FAILURE
                                    if self._offset > self._failure:
                                        self._failure = self._offset
                                        self._expected = []
                                    if self._offset == self._failure:
                                        self._expected.append('")"')
                                if address9 is not FAILURE:
                                    elements3.append(address9)
                                else:
                                    elements3 = None
                                    self._offset = index5
                            else:
                                elements3 = None
                                self._offset = index5
                        else:
                            elements3 = None
                            self._offset = index5
                    else:
                        elements3 = None
                        self._offset = index5
                    if elements3 is None:
                        address3 = FAILURE
                    else:
                        address3 = nist_ion_descriptions_TreeNode4(self._input[index5:self._offset], index5, elements3)
                        self._offset = self._offset
                    if address3 is FAILURE:
                        self._offset = index3
                        address3 = self._read_mass()
                        if address3 is FAILURE:
                            self._offset = index3
                if address3 is not FAILURE:
                    elements1.append(address3)
                else:
                    elements1 = None
                    self._offset = index2
            else:
                elements1 = None
                self._offset = index2
            if elements1 is None:
                address1 = FAILURE
            else:
                address1 = nist_ion_descriptions_TreeNode2(self._input[index2:self._offset], index2, elements1)
                self._offset = self._offset
            if address1 is not FAILURE:
                elements0.append(address1)
                remaining0 -= 1
        if remaining0 <= 0:
            address0 = nist_ion_descriptions_TreeNode(self._input[index1:self._offset], index1, elements0)
            self._offset = self._offset
        else:
            address0 = FAILURE
        self._cache['formulae'][index0] = (address0, self._offset)
        return address0

    def _read_charge_state(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['charge_state'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        index1, elements0 = self._offset, []
        address1 = FAILURE
        address1 = self._read_count()
        if address1 is not FAILURE:
            elements0.append(address1)
            address2 = FAILURE
            address2 = self._read_plus_minus()
            if address2 is not FAILURE:
                elements0.append(address2)
            else:
                elements0 = None
                self._offset = index1
        else:
            elements0 = None
            self._offset = index1
        if elements0 is None:
            address0 = FAILURE
        else:
            address0 = nist_ion_descriptions_TreeNode5(self._input[index1:self._offset], index1, elements0)
            self._offset = self._offset
        self._cache['charge_state'][index0] = (address0, self._offset)
        return address0

    def _read_plus_minus(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['plus_minus'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        index1 = self._offset
        chunk0 = None
        if self._offset < self._input_size:
            chunk0 = self._input[self._offset:self._offset + 1]
        if chunk0 == '+':
            address0 = nist_ion_descriptions_TreeNode(self._input[self._offset:self._offset + 1], self._offset)
            self._offset = self._offset + 1
        else:
            address0 = FAILURE
            if self._offset > self._failure:
                self._failure = self._offset
                self._expected = []
            if self._offset == self._failure:
                self._expected.append('"+"')
        if address0 is FAILURE:
            self._offset = index1
            chunk1 = None
            if self._offset < self._input_size:
                chunk1 = self._input[self._offset:self._offset + 1]
            if chunk1 == '-':
                address0 = nist_ion_descriptions_TreeNode(self._input[self._offset:self._offset + 1], self._offset)
                self._offset = self._offset + 1
            else:
                address0 = FAILURE
                if self._offset > self._failure:
                    self._failure = self._offset
                    self._expected = []
                if self._offset == self._failure:
                    self._expected.append('"-"')
            if address0 is FAILURE:
                self._offset = index1
        self._cache['plus_minus'][index0] = (address0, self._offset)
        return address0

    def _read_formula(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['formula'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        remaining0, index1, elements0, address1 = 1, self._offset, [], True
        while address1 is not FAILURE:
            address1 = self._read_term()
            if address1 is not FAILURE:
                elements0.append(address1)
                remaining0 -= 1
        if remaining0 <= 0:
            address0 = nist_ion_descriptions_TreeNode(self._input[index1:self._offset], index1, elements0)
            self._offset = self._offset
        else:
            address0 = FAILURE
        self._cache['formula'][index0] = (address0, self._offset)
        return address0

    def _read_term(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['term'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        index1, elements0 = self._offset, []
        address1 = FAILURE
        index2 = self._offset
        address1 = self._read_element()
        if address1 is FAILURE:
            self._offset = index2
            address1 = self._read_sub_formula()
            if address1 is FAILURE:
                self._offset = index2
        if address1 is not FAILURE:
            elements0.append(address1)
            address2 = FAILURE
            address2 = self._read_count()
            if address2 is not FAILURE:
                elements0.append(address2)
            else:
                elements0 = None
                self._offset = index1
        else:
            elements0 = None
            self._offset = index1
        if elements0 is None:
            address0 = FAILURE
        else:
            address0 = self._actions.make_term(self._input, index1, self._offset, elements0)
            self._offset = self._offset
        self._cache['term'][index0] = (address0, self._offset)
        return address0

    def _read_element(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['element'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        index1 = self._offset
        chunk0 = None
        if self._offset < self._input_size:
            chunk0 = self._input[self._offset:self._offset + 2]
        if chunk0 == 'Zr':
            address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
            self._offset = self._offset + 2
        else:
            address0 = FAILURE
            if self._offset > self._failure:
                self._failure = self._offset
                self._expected = []
            if self._offset == self._failure:
                self._expected.append('"Zr"')
        if address0 is FAILURE:
            self._offset = index1
            chunk1 = None
            if self._offset < self._input_size:
                chunk1 = self._input[self._offset:self._offset + 2]
            if chunk1 == 'Zn':
                address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                self._offset = self._offset + 2
            else:
                address0 = FAILURE
                if self._offset > self._failure:
                    self._failure = self._offset
                    self._expected = []
                if self._offset == self._failure:
                    self._expected.append('"Zn"')
            if address0 is FAILURE:
                self._offset = index1
                chunk2 = None
                if self._offset < self._input_size:
                    chunk2 = self._input[self._offset:self._offset + 2]
                if chunk2 == 'Yb':
                    address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                    self._offset = self._offset + 2
                else:
                    address0 = FAILURE
                    if self._offset > self._failure:
                        self._failure = self._offset
                        self._expected = []
                    if self._offset == self._failure:
                        self._expected.append('"Yb"')
                if address0 is FAILURE:
                    self._offset = index1
                    chunk3 = None
                    if self._offset < self._input_size:
                        chunk3 = self._input[self._offset:self._offset + 1]
                    if chunk3 == 'Y':
                        address0 = self._actions.make_element(self._input, self._offset, self._offset + 1)
                        self._offset = self._offset + 1
                    else:
                        address0 = FAILURE
                        if self._offset > self._failure:
                            self._failure = self._offset
                            self._expected = []
                        if self._offset == self._failure:
                            self._expected.append('"Y"')
                    if address0 is FAILURE:
                        self._offset = index1
                        chunk4 = None
                        if self._offset < self._input_size:
                            chunk4 = self._input[self._offset:self._offset + 2]
                        if chunk4 == 'Xe':
                            address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                            self._offset = self._offset + 2
                        else:
                            address0 = FAILURE
                            if self._offset > self._failure:
                                self._failure = self._offset
                                self._expected = []
                            if self._offset == self._failure:
                                self._expected.append('"Xe"')
                        if address0 is FAILURE:
                            self._offset = index1
                            chunk5 = None
                            if self._offset < self._input_size:
                                chunk5 = self._input[self._offset:self._offset + 1]
                            if chunk5 == 'W':
                                address0 = self._actions.make_element(self._input, self._offset, self._offset + 1)
                                self._offset = self._offset + 1
                            else:
                                address0 = FAILURE
                                if self._offset > self._failure:
                                    self._failure = self._offset
                                    self._expected = []
                                if self._offset == self._failure:
                                    self._expected.append('"W"')
                            if address0 is FAILURE:
                                self._offset = index1
                                chunk6 = None
                                if self._offset < self._input_size:
                                    chunk6 = self._input[self._offset:self._offset + 1]
                                if chunk6 == 'V':
                                    address0 = self._actions.make_element(self._input, self._offset, self._offset + 1)
                                    self._offset = self._offset + 1
                                else:
                                    address0 = FAILURE
                                    if self._offset > self._failure:
                                        self._failure = self._offset
                                        self._expected = []
                                    if self._offset == self._failure:
                                        self._expected.append('"V"')
                                if address0 is FAILURE:
                                    self._offset = index1
                                    chunk7 = None
                                    if self._offset < self._input_size:
                                        chunk7 = self._input[self._offset:self._offset + 1]
                                    if chunk7 == 'U':
                                        address0 = self._actions.make_element(self._input, self._offset, self._offset + 1)
                                        self._offset = self._offset + 1
                                    else:
                                        address0 = FAILURE
                                        if self._offset > self._failure:
                                            self._failure = self._offset
                                            self._expected = []
                                        if self._offset == self._failure:
                                            self._expected.append('"U"')
                                    if address0 is FAILURE:
                                        self._offset = index1
                                        chunk8 = None
                                        if self._offset < self._input_size:
                                            chunk8 = self._input[self._offset:self._offset + 2]
                                        if chunk8 == 'Tm':
                                            address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                            self._offset = self._offset + 2
                                        else:
                                            address0 = FAILURE
                                            if self._offset > self._failure:
                                                self._failure = self._offset
                                                self._expected = []
                                            if self._offset == self._failure:
                                                self._expected.append('"Tm"')
                                        if address0 is FAILURE:
                                            self._offset = index1
                                            chunk9 = None
                                            if self._offset < self._input_size:
                                                chunk9 = self._input[self._offset:self._offset + 2]
                                            if chunk9 == 'Tl':
                                                address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                self._offset = self._offset + 2
                                            else:
                                                address0 = FAILURE
                                                if self._offset > self._failure:
                                                    self._failure = self._offset
                                                    self._expected = []
                                                if self._offset == self._failure:
                                                    self._expected.append('"Tl"')
                                            if address0 is FAILURE:
                                                self._offset = index1
                                                chunk10 = None
                                                if self._offset < self._input_size:
                                                    chunk10 = self._input[self._offset:self._offset + 2]
                                                if chunk10 == 'Ti':
                                                    address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                    self._offset = self._offset + 2
                                                else:
                                                    address0 = FAILURE
                                                    if self._offset > self._failure:
                                                        self._failure = self._offset
                                                        self._expected = []
                                                    if self._offset == self._failure:
                                                        self._expected.append('"Ti"')
                                                if address0 is FAILURE:
                                                    self._offset = index1
                                                    chunk11 = None
                                                    if self._offset < self._input_size:
                                                        chunk11 = self._input[self._offset:self._offset + 2]
                                                    if chunk11 == 'Th':
                                                        address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                        self._offset = self._offset + 2
                                                    else:
                                                        address0 = FAILURE
                                                        if self._offset > self._failure:
                                                            self._failure = self._offset
                                                            self._expected = []
                                                        if self._offset == self._failure:
                                                            self._expected.append('"Th"')
                                                    if address0 is FAILURE:
                                                        self._offset = index1
                                                        chunk12 = None
                                                        if self._offset < self._input_size:
                                                            chunk12 = self._input[self._offset:self._offset + 2]
                                                        if chunk12 == 'Te':
                                                            address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                            self._offset = self._offset + 2
                                                        else:
                                                            address0 = FAILURE
                                                            if self._offset > self._failure:
                                                                self._failure = self._offset
                                                                self._expected = []
                                                            if self._offset == self._failure:
                                                                self._expected.append('"Te"')
                                                        if address0 is FAILURE:
                                                            self._offset = index1
                                                            chunk13 = None
                                                            if self._offset < self._input_size:
                                                                chunk13 = self._input[self._offset:self._offset + 2]
                                                            if chunk13 == 'Tb':
                                                                address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                self._offset = self._offset + 2
                                                            else:
                                                                address0 = FAILURE
                                                                if self._offset > self._failure:
                                                                    self._failure = self._offset
                                                                    self._expected = []
                                                                if self._offset == self._failure:
                                                                    self._expected.append('"Tb"')
                                                            if address0 is FAILURE:
                                                                self._offset = index1
                                                                chunk14 = None
                                                                if self._offset < self._input_size:
                                                                    chunk14 = self._input[self._offset:self._offset + 2]
                                                                if chunk14 == 'Ta':
                                                                    address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                    self._offset = self._offset + 2
                                                                else:
                                                                    address0 = FAILURE
                                                                    if self._offset > self._failure:
                                                                        self._failure = self._offset
                                                                        self._expected = []
                                                                    if self._offset == self._failure:
                                                                        self._expected.append('"Ta"')
                                                                if address0 is FAILURE:
                                                                    self._offset = index1
                                                                    chunk15 = None
                                                                    if self._offset < self._input_size:
                                                                        chunk15 = self._input[self._offset:self._offset + 2]
                                                                    if chunk15 == 'Sr':
                                                                        address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                        self._offset = self._offset + 2
                                                                    else:
                                                                        address0 = FAILURE
                                                                        if self._offset > self._failure:
                                                                            self._failure = self._offset
                                                                            self._expected = []
                                                                        if self._offset == self._failure:
                                                                            self._expected.append('"Sr"')
                                                                    if address0 is FAILURE:
                                                                        self._offset = index1
                                                                        chunk16 = None
                                                                        if self._offset < self._input_size:
                                                                            chunk16 = self._input[self._offset:self._offset + 2]
                                                                        if chunk16 == 'Sn':
                                                                            address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                            self._offset = self._offset + 2
                                                                        else:
                                                                            address0 = FAILURE
                                                                            if self._offset > self._failure:
                                                                                self._failure = self._offset
                                                                                self._expected = []
                                                                            if self._offset == self._failure:
                                                                                self._expected.append('"Sn"')
                                                                        if address0 is FAILURE:
                                                                            self._offset = index1
                                                                            chunk17 = None
                                                                            if self._offset < self._input_size:
                                                                                chunk17 = self._input[self._offset:self._offset + 2]
                                                                            if chunk17 == 'Sm':
                                                                                address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                self._offset = self._offset + 2
                                                                            else:
                                                                                address0 = FAILURE
                                                                                if self._offset > self._failure:
                                                                                    self._failure = self._offset
                                                                                    self._expected = []
                                                                                if self._offset == self._failure:
                                                                                    self._expected.append('"Sm"')
                                                                            if address0 is FAILURE:
                                                                                self._offset = index1
                                                                                chunk18 = None
                                                                                if self._offset < self._input_size:
                                                                                    chunk18 = self._input[self._offset:self._offset + 2]
                                                                                if chunk18 == 'Si':
                                                                                    address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                    self._offset = self._offset + 2
                                                                                else:
                                                                                    address0 = FAILURE
                                                                                    if self._offset > self._failure:
                                                                                        self._failure = self._offset
                                                                                        self._expected = []
                                                                                    if self._offset == self._failure:
                                                                                        self._expected.append('"Si"')
                                                                                if address0 is FAILURE:
                                                                                    self._offset = index1
                                                                                    chunk19 = None
                                                                                    if self._offset < self._input_size:
                                                                                        chunk19 = self._input[self._offset:self._offset + 2]
                                                                                    if chunk19 == 'Se':
                                                                                        address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                        self._offset = self._offset + 2
                                                                                    else:
                                                                                        address0 = FAILURE
                                                                                        if self._offset > self._failure:
                                                                                            self._failure = self._offset
                                                                                            self._expected = []
                                                                                        if self._offset == self._failure:
                                                                                            self._expected.append('"Se"')
                                                                                    if address0 is FAILURE:
                                                                                        self._offset = index1
                                                                                        chunk20 = None
                                                                                        if self._offset < self._input_size:
                                                                                            chunk20 = self._input[self._offset:self._offset + 2]
                                                                                        if chunk20 == 'Sc':
                                                                                            address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                            self._offset = self._offset + 2
                                                                                        else:
                                                                                            address0 = FAILURE
                                                                                            if self._offset > self._failure:
                                                                                                self._failure = self._offset
                                                                                                self._expected = []
                                                                                            if self._offset == self._failure:
                                                                                                self._expected.append('"Sc"')
                                                                                        if address0 is FAILURE:
                                                                                            self._offset = index1
                                                                                            chunk21 = None
                                                                                            if self._offset < self._input_size:
                                                                                                chunk21 = self._input[self._offset:self._offset + 2]
                                                                                            if chunk21 == 'Sb':
                                                                                                address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                self._offset = self._offset + 2
                                                                                            else:
                                                                                                address0 = FAILURE
                                                                                                if self._offset > self._failure:
                                                                                                    self._failure = self._offset
                                                                                                    self._expected = []
                                                                                                if self._offset == self._failure:
                                                                                                    self._expected.append('"Sb"')
                                                                                            if address0 is FAILURE:
                                                                                                self._offset = index1
                                                                                                chunk22 = None
                                                                                                if self._offset < self._input_size:
                                                                                                    chunk22 = self._input[self._offset:self._offset + 1]
                                                                                                if chunk22 == 'S':
                                                                                                    address0 = self._actions.make_element(self._input, self._offset, self._offset + 1)
                                                                                                    self._offset = self._offset + 1
                                                                                                else:
                                                                                                    address0 = FAILURE
                                                                                                    if self._offset > self._failure:
                                                                                                        self._failure = self._offset
                                                                                                        self._expected = []
                                                                                                    if self._offset == self._failure:
                                                                                                        self._expected.append('"S"')
                                                                                                if address0 is FAILURE:
                                                                                                    self._offset = index1
                                                                                                    chunk23 = None
                                                                                                    if self._offset < self._input_size:
                                                                                                        chunk23 = self._input[self._offset:self._offset + 2]
                                                                                                    if chunk23 == 'Ru':
                                                                                                        address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                        self._offset = self._offset + 2
                                                                                                    else:
                                                                                                        address0 = FAILURE
                                                                                                        if self._offset > self._failure:
                                                                                                            self._failure = self._offset
                                                                                                            self._expected = []
                                                                                                        if self._offset == self._failure:
                                                                                                            self._expected.append('"Ru"')
                                                                                                    if address0 is FAILURE:
                                                                                                        self._offset = index1
                                                                                                        chunk24 = None
                                                                                                        if self._offset < self._input_size:
                                                                                                            chunk24 = self._input[self._offset:self._offset + 2]
                                                                                                        if chunk24 == 'Rh':
                                                                                                            address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                            self._offset = self._offset + 2
                                                                                                        else:
                                                                                                            address0 = FAILURE
                                                                                                            if self._offset > self._failure:
                                                                                                                self._failure = self._offset
                                                                                                                self._expected = []
                                                                                                            if self._offset == self._failure:
                                                                                                                self._expected.append('"Rh"')
                                                                                                        if address0 is FAILURE:
                                                                                                            self._offset = index1
                                                                                                            chunk25 = None
                                                                                                            if self._offset < self._input_size:
                                                                                                                chunk25 = self._input[self._offset:self._offset + 2]
                                                                                                            if chunk25 == 'Re':
                                                                                                                address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                self._offset = self._offset + 2
                                                                                                            else:
                                                                                                                address0 = FAILURE
                                                                                                                if self._offset > self._failure:
                                                                                                                    self._failure = self._offset
                                                                                                                    self._expected = []
                                                                                                                if self._offset == self._failure:
                                                                                                                    self._expected.append('"Re"')
                                                                                                            if address0 is FAILURE:
                                                                                                                self._offset = index1
                                                                                                                chunk26 = None
                                                                                                                if self._offset < self._input_size:
                                                                                                                    chunk26 = self._input[self._offset:self._offset + 2]
                                                                                                                if chunk26 == 'Rb':
                                                                                                                    address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                    self._offset = self._offset + 2
                                                                                                                else:
                                                                                                                    address0 = FAILURE
                                                                                                                    if self._offset > self._failure:
                                                                                                                        self._failure = self._offset
                                                                                                                        self._expected = []
                                                                                                                    if self._offset == self._failure:
                                                                                                                        self._expected.append('"Rb"')
                                                                                                                if address0 is FAILURE:
                                                                                                                    self._offset = index1
                                                                                                                    chunk27 = None
                                                                                                                    if self._offset < self._input_size:
                                                                                                                        chunk27 = self._input[self._offset:self._offset + 2]
                                                                                                                    if chunk27 == 'Pt':
                                                                                                                        address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                        self._offset = self._offset + 2
                                                                                                                    else:
                                                                                                                        address0 = FAILURE
                                                                                                                        if self._offset > self._failure:
                                                                                                                            self._failure = self._offset
                                                                                                                            self._expected = []
                                                                                                                        if self._offset == self._failure:
                                                                                                                            self._expected.append('"Pt"')
                                                                                                                    if address0 is FAILURE:
                                                                                                                        self._offset = index1
                                                                                                                        chunk28 = None
                                                                                                                        if self._offset < self._input_size:
                                                                                                                            chunk28 = self._input[self._offset:self._offset + 2]
                                                                                                                        if chunk28 == 'Pr':
                                                                                                                            address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                            self._offset = self._offset + 2
                                                                                                                        else:
                                                                                                                            address0 = FAILURE
                                                                                                                            if self._offset > self._failure:
                                                                                                                                self._failure = self._offset
                                                                                                                                self._expected = []
                                                                                                                            if self._offset == self._failure:
                                                                                                                                self._expected.append('"Pr"')
                                                                                                                        if address0 is FAILURE:
                                                                                                                            self._offset = index1
                                                                                                                            chunk29 = None
                                                                                                                            if self._offset < self._input_size:
                                                                                                                                chunk29 = self._input[self._offset:self._offset + 2]
                                                                                                                            if chunk29 == 'Pd':
                                                                                                                                address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                self._offset = self._offset + 2
                                                                                                                            else:
                                                                                                                                address0 = FAILURE
                                                                                                                                if self._offset > self._failure:
                                                                                                                                    self._failure = self._offset
                                                                                                                                    self._expected = []
                                                                                                                                if self._offset == self._failure:
                                                                                                                                    self._expected.append('"Pd"')
                                                                                                                            if address0 is FAILURE:
                                                                                                                                self._offset = index1
                                                                                                                                chunk30 = None
                                                                                                                                if self._offset < self._input_size:
                                                                                                                                    chunk30 = self._input[self._offset:self._offset + 2]
                                                                                                                                if chunk30 == 'Pb':
                                                                                                                                    address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                    self._offset = self._offset + 2
                                                                                                                                else:
                                                                                                                                    address0 = FAILURE
                                                                                                                                    if self._offset > self._failure:
                                                                                                                                        self._failure = self._offset
                                                                                                                                        self._expected = []
                                                                                                                                    if self._offset == self._failure:
                                                                                                                                        self._expected.append('"Pb"')
                                                                                                                                if address0 is FAILURE:
                                                                                                                                    self._offset = index1
                                                                                                                                    chunk31 = None
                                                                                                                                    if self._offset < self._input_size:
                                                                                                                                        chunk31 = self._input[self._offset:self._offset + 1]
                                                                                                                                    if chunk31 == 'P':
                                                                                                                                        address0 = self._actions.make_element(self._input, self._offset, self._offset + 1)
                                                                                                                                        self._offset = self._offset + 1
                                                                                                                                    else:
                                                                                                                                        address0 = FAILURE
                                                                                                                                        if self._offset > self._failure:
                                                                                                                                            self._failure = self._offset
                                                                                                                                            self._expected = []
                                                                                                                                        if self._offset == self._failure:
                                                                                                                                            self._expected.append('"P"')
                                                                                                                                    if address0 is FAILURE:
                                                                                                                                        self._offset = index1
                                                                                                                                        chunk32 = None
                                                                                                                                        if self._offset < self._input_size:
                                                                                                                                            chunk32 = self._input[self._offset:self._offset + 2]
                                                                                                                                        if chunk32 == 'Os':
                                                                                                                                            address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                            self._offset = self._offset + 2
                                                                                                                                        else:
                                                                                                                                            address0 = FAILURE
                                                                                                                                            if self._offset > self._failure:
                                                                                                                                                self._failure = self._offset
                                                                                                                                                self._expected = []
                                                                                                                                            if self._offset == self._failure:
                                                                                                                                                self._expected.append('"Os"')
                                                                                                                                        if address0 is FAILURE:
                                                                                                                                            self._offset = index1
                                                                                                                                            chunk33 = None
                                                                                                                                            if self._offset < self._input_size:
                                                                                                                                                chunk33 = self._input[self._offset:self._offset + 1]
                                                                                                                                            if chunk33 == 'O':
                                                                                                                                                address0 = self._actions.make_element(self._input, self._offset, self._offset + 1)
                                                                                                                                                self._offset = self._offset + 1
                                                                                                                                            else:
                                                                                                                                                address0 = FAILURE
                                                                                                                                                if self._offset > self._failure:
                                                                                                                                                    self._failure = self._offset
                                                                                                                                                    self._expected = []
                                                                                                                                                if self._offset == self._failure:
                                                                                                                                                    self._expected.append('"O"')
                                                                                                                                            if address0 is FAILURE:
                                                                                                                                                self._offset = index1
                                                                                                                                                chunk34 = None
                                                                                                                                                if self._offset < self._input_size:
                                                                                                                                                    chunk34 = self._input[self._offset:self._offset + 2]
                                                                                                                                                if chunk34 == 'Ni':
                                                                                                                                                    address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                    self._offset = self._offset + 2
                                                                                                                                                else:
                                                                                                                                                    address0 = FAILURE
                                                                                                                                                    if self._offset > self._failure:
                                                                                                                                                        self._failure = self._offset
                                                                                                                                                        self._expected = []
                                                                                                                                                    if self._offset == self._failure:
                                                                                                                                                        self._expected.append('"Ni"')
                                                                                                                                                if address0 is FAILURE:
                                                                                                                                                    self._offset = index1
                                                                                                                                                    chunk35 = None
                                                                                                                                                    if self._offset < self._input_size:
                                                                                                                                                        chunk35 = self._input[self._offset:self._offset + 2]
                                                                                                                                                    if chunk35 == 'Ne':
                                                                                                                                                        address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                        self._offset = self._offset + 2
                                                                                                                                                    else:
                                                                                                                                                        address0 = FAILURE
                                                                                                                                                        if self._offset > self._failure:
                                                                                                                                                            self._failure = self._offset
                                                                                                                                                            self._expected = []
                                                                                                                                                        if self._offset == self._failure:
                                                                                                                                                            self._expected.append('"Ne"')
                                                                                                                                                    if address0 is FAILURE:
                                                                                                                                                        self._offset = index1
                                                                                                                                                        chunk36 = None
                                                                                                                                                        if self._offset < self._input_size:
                                                                                                                                                            chunk36 = self._input[self._offset:self._offset + 2]
                                                                                                                                                        if chunk36 == 'Nd':
                                                                                                                                                            address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                            self._offset = self._offset + 2
                                                                                                                                                        else:
                                                                                                                                                            address0 = FAILURE
                                                                                                                                                            if self._offset > self._failure:
                                                                                                                                                                self._failure = self._offset
                                                                                                                                                                self._expected = []
                                                                                                                                                            if self._offset == self._failure:
                                                                                                                                                                self._expected.append('"Nd"')
                                                                                                                                                        if address0 is FAILURE:
                                                                                                                                                            self._offset = index1
                                                                                                                                                            chunk37 = None
                                                                                                                                                            if self._offset < self._input_size:
                                                                                                                                                                chunk37 = self._input[self._offset:self._offset + 2]
                                                                                                                                                            if chunk37 == 'Nb':
                                                                                                                                                                address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                                self._offset = self._offset + 2
                                                                                                                                                            else:
                                                                                                                                                                address0 = FAILURE
                                                                                                                                                                if self._offset > self._failure:
                                                                                                                                                                    self._failure = self._offset
                                                                                                                                                                    self._expected = []
                                                                                                                                                                if self._offset == self._failure:
                                                                                                                                                                    self._expected.append('"Nb"')
                                                                                                                                                            if address0 is FAILURE:
                                                                                                                                                                self._offset = index1
                                                                                                                                                                chunk38 = None
                                                                                                                                                                if self._offset < self._input_size:
                                                                                                                                                                    chunk38 = self._input[self._offset:self._offset + 2]
                                                                                                                                                                if chunk38 == 'Na':
                                                                                                                                                                    address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                                    self._offset = self._offset + 2
                                                                                                                                                                else:
                                                                                                                                                                    address0 = FAILURE
                                                                                                                                                                    if self._offset > self._failure:
                                                                                                                                                                        self._failure = self._offset
                                                                                                                                                                        self._expected = []
                                                                                                                                                                    if self._offset == self._failure:
                                                                                                                                                                        self._expected.append('"Na"')
                                                                                                                                                                if address0 is FAILURE:
                                                                                                                                                                    self._offset = index1
                                                                                                                                                                    chunk39 = None
                                                                                                                                                                    if self._offset < self._input_size:
                                                                                                                                                                        chunk39 = self._input[self._offset:self._offset + 1]
                                                                                                                                                                    if chunk39 == 'N':
                                                                                                                                                                        address0 = self._actions.make_element(self._input, self._offset, self._offset + 1)
                                                                                                                                                                        self._offset = self._offset + 1
                                                                                                                                                                    else:
                                                                                                                                                                        address0 = FAILURE
                                                                                                                                                                        if self._offset > self._failure:
                                                                                                                                                                            self._failure = self._offset
                                                                                                                                                                            self._expected = []
                                                                                                                                                                        if self._offset == self._failure:
                                                                                                                                                                            self._expected.append('"N"')
                                                                                                                                                                    if address0 is FAILURE:
                                                                                                                                                                        self._offset = index1
                                                                                                                                                                        chunk40 = None
                                                                                                                                                                        if self._offset < self._input_size:
                                                                                                                                                                            chunk40 = self._input[self._offset:self._offset + 2]
                                                                                                                                                                        if chunk40 == 'Mo':
                                                                                                                                                                            address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                                            self._offset = self._offset + 2
                                                                                                                                                                        else:
                                                                                                                                                                            address0 = FAILURE
                                                                                                                                                                            if self._offset > self._failure:
                                                                                                                                                                                self._failure = self._offset
                                                                                                                                                                                self._expected = []
                                                                                                                                                                            if self._offset == self._failure:
                                                                                                                                                                                self._expected.append('"Mo"')
                                                                                                                                                                        if address0 is FAILURE:
                                                                                                                                                                            self._offset = index1
                                                                                                                                                                            chunk41 = None
                                                                                                                                                                            if self._offset < self._input_size:
                                                                                                                                                                                chunk41 = self._input[self._offset:self._offset + 2]
                                                                                                                                                                            if chunk41 == 'Mn':
                                                                                                                                                                                address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                                                self._offset = self._offset + 2
                                                                                                                                                                            else:
                                                                                                                                                                                address0 = FAILURE
                                                                                                                                                                                if self._offset > self._failure:
                                                                                                                                                                                    self._failure = self._offset
                                                                                                                                                                                    self._expected = []
                                                                                                                                                                                if self._offset == self._failure:
                                                                                                                                                                                    self._expected.append('"Mn"')
                                                                                                                                                                            if address0 is FAILURE:
                                                                                                                                                                                self._offset = index1
                                                                                                                                                                                chunk42 = None
                                                                                                                                                                                if self._offset < self._input_size:
                                                                                                                                                                                    chunk42 = self._input[self._offset:self._offset + 2]
                                                                                                                                                                                if chunk42 == 'Mg':
                                                                                                                                                                                    address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                                                    self._offset = self._offset + 2
                                                                                                                                                                                else:
                                                                                                                                                                                    address0 = FAILURE
                                                                                                                                                                                    if self._offset > self._failure:
                                                                                                                                                                                        self._failure = self._offset
                                                                                                                                                                                        self._expected = []
                                                                                                                                                                                    if self._offset == self._failure:
                                                                                                                                                                                        self._expected.append('"Mg"')
                                                                                                                                                                                if address0 is FAILURE:
                                                                                                                                                                                    self._offset = index1
                                                                                                                                                                                    chunk43 = None
                                                                                                                                                                                    if self._offset < self._input_size:
                                                                                                                                                                                        chunk43 = self._input[self._offset:self._offset + 2]
                                                                                                                                                                                    if chunk43 == 'Lu':
                                                                                                                                                                                        address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                                                        self._offset = self._offset + 2
                                                                                                                                                                                    else:
                                                                                                                                                                                        address0 = FAILURE
                                                                                                                                                                                        if self._offset > self._failure:
                                                                                                                                                                                            self._failure = self._offset
                                                                                                                                                                                            self._expected = []
                                                                                                                                                                                        if self._offset == self._failure:
                                                                                                                                                                                            self._expected.append('"Lu"')
                                                                                                                                                                                    if address0 is FAILURE:
                                                                                                                                                                                        self._offset = index1
                                                                                                                                                                                        chunk44 = None
                                                                                                                                                                                        if self._offset < self._input_size:
                                                                                                                                                                                            chunk44 = self._input[self._offset:self._offset + 2]
                                                                                                                                                                                        if chunk44 == 'Li':
                                                                                                                                                                                            address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                                                            self._offset = self._offset + 2
                                                                                                                                                                                        else:
                                                                                                                                                                                            address0 = FAILURE
                                                                                                                                                                                            if self._offset > self._failure:
                                                                                                                                                                                                self._failure = self._offset
                                                                                                                                                                                                self._expected = []
                                                                                                                                                                                            if self._offset == self._failure:
                                                                                                                                                                                                self._expected.append('"Li"')
                                                                                                                                                                                        if address0 is FAILURE:
                                                                                                                                                                                            self._offset = index1
                                                                                                                                                                                            chunk45 = None
                                                                                                                                                                                            if self._offset < self._input_size:
                                                                                                                                                                                                chunk45 = self._input[self._offset:self._offset + 2]
                                                                                                                                                                                            if chunk45 == 'La':
                                                                                                                                                                                                address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                                                                self._offset = self._offset + 2
                                                                                                                                                                                            else:
                                                                                                                                                                                                address0 = FAILURE
                                                                                                                                                                                                if self._offset > self._failure:
                                                                                                                                                                                                    self._failure = self._offset
                                                                                                                                                                                                    self._expected = []
                                                                                                                                                                                                if self._offset == self._failure:
                                                                                                                                                                                                    self._expected.append('"La"')
                                                                                                                                                                                            if address0 is FAILURE:
                                                                                                                                                                                                self._offset = index1
                                                                                                                                                                                                chunk46 = None
                                                                                                                                                                                                if self._offset < self._input_size:
                                                                                                                                                                                                    chunk46 = self._input[self._offset:self._offset + 2]
                                                                                                                                                                                                if chunk46 == 'Kr':
                                                                                                                                                                                                    address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                                                                    self._offset = self._offset + 2
                                                                                                                                                                                                else:
                                                                                                                                                                                                    address0 = FAILURE
                                                                                                                                                                                                    if self._offset > self._failure:
                                                                                                                                                                                                        self._failure = self._offset
                                                                                                                                                                                                        self._expected = []
                                                                                                                                                                                                    if self._offset == self._failure:
                                                                                                                                                                                                        self._expected.append('"Kr"')
                                                                                                                                                                                                if address0 is FAILURE:
                                                                                                                                                                                                    self._offset = index1
                                                                                                                                                                                                    chunk47 = None
                                                                                                                                                                                                    if self._offset < self._input_size:
                                                                                                                                                                                                        chunk47 = self._input[self._offset:self._offset + 1]
                                                                                                                                                                                                    if chunk47 == 'K':
                                                                                                                                                                                                        address0 = self._actions.make_element(self._input, self._offset, self._offset + 1)
                                                                                                                                                                                                        self._offset = self._offset + 1
                                                                                                                                                                                                    else:
                                                                                                                                                                                                        address0 = FAILURE
                                                                                                                                                                                                        if self._offset > self._failure:
                                                                                                                                                                                                            self._failure = self._offset
                                                                                                                                                                                                            self._expected = []
                                                                                                                                                                                                        if self._offset == self._failure:
                                                                                                                                                                                                            self._expected.append('"K"')
                                                                                                                                                                                                    if address0 is FAILURE:
                                                                                                                                                                                                        self._offset = index1
                                                                                                                                                                                                        chunk48 = None
                                                                                                                                                                                                        if self._offset < self._input_size:
                                                                                                                                                                                                            chunk48 = self._input[self._offset:self._offset + 2]
                                                                                                                                                                                                        if chunk48 == 'Ir':
                                                                                                                                                                                                            address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                                                                            self._offset = self._offset + 2
                                                                                                                                                                                                        else:
                                                                                                                                                                                                            address0 = FAILURE
                                                                                                                                                                                                            if self._offset > self._failure:
                                                                                                                                                                                                                self._failure = self._offset
                                                                                                                                                                                                                self._expected = []
                                                                                                                                                                                                            if self._offset == self._failure:
                                                                                                                                                                                                                self._expected.append('"Ir"')
                                                                                                                                                                                                        if address0 is FAILURE:
                                                                                                                                                                                                            self._offset = index1
                                                                                                                                                                                                            chunk49 = None
                                                                                                                                                                                                            if self._offset < self._input_size:
                                                                                                                                                                                                                chunk49 = self._input[self._offset:self._offset + 2]
                                                                                                                                                                                                            if chunk49 == 'In':
                                                                                                                                                                                                                address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                                                                                self._offset = self._offset + 2
                                                                                                                                                                                                            else:
                                                                                                                                                                                                                address0 = FAILURE
                                                                                                                                                                                                                if self._offset > self._failure:
                                                                                                                                                                                                                    self._failure = self._offset
                                                                                                                                                                                                                    self._expected = []
                                                                                                                                                                                                                if self._offset == self._failure:
                                                                                                                                                                                                                    self._expected.append('"In"')
                                                                                                                                                                                                            if address0 is FAILURE:
                                                                                                                                                                                                                self._offset = index1
                                                                                                                                                                                                                chunk50 = None
                                                                                                                                                                                                                if self._offset < self._input_size:
                                                                                                                                                                                                                    chunk50 = self._input[self._offset:self._offset + 1]
                                                                                                                                                                                                                if chunk50 == 'I':
                                                                                                                                                                                                                    address0 = self._actions.make_element(self._input, self._offset, self._offset + 1)
                                                                                                                                                                                                                    self._offset = self._offset + 1
                                                                                                                                                                                                                else:
                                                                                                                                                                                                                    address0 = FAILURE
                                                                                                                                                                                                                    if self._offset > self._failure:
                                                                                                                                                                                                                        self._failure = self._offset
                                                                                                                                                                                                                        self._expected = []
                                                                                                                                                                                                                    if self._offset == self._failure:
                                                                                                                                                                                                                        self._expected.append('"I"')
                                                                                                                                                                                                                if address0 is FAILURE:
                                                                                                                                                                                                                    self._offset = index1
                                                                                                                                                                                                                    chunk51 = None
                                                                                                                                                                                                                    if self._offset < self._input_size:
                                                                                                                                                                                                                        chunk51 = self._input[self._offset:self._offset + 2]
                                                                                                                                                                                                                    if chunk51 == 'Ho':
                                                                                                                                                                                                                        address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                                                                                        self._offset = self._offset + 2
                                                                                                                                                                                                                    else:
                                                                                                                                                                                                                        address0 = FAILURE
                                                                                                                                                                                                                        if self._offset > self._failure:
                                                                                                                                                                                                                            self._failure = self._offset
                                                                                                                                                                                                                            self._expected = []
                                                                                                                                                                                                                        if self._offset == self._failure:
                                                                                                                                                                                                                            self._expected.append('"Ho"')
                                                                                                                                                                                                                    if address0 is FAILURE:
                                                                                                                                                                                                                        self._offset = index1
                                                                                                                                                                                                                        chunk52 = None
                                                                                                                                                                                                                        if self._offset < self._input_size:
                                                                                                                                                                                                                            chunk52 = self._input[self._offset:self._offset + 2]
                                                                                                                                                                                                                        if chunk52 == 'Hg':
                                                                                                                                                                                                                            address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                                                                                            self._offset = self._offset + 2
                                                                                                                                                                                                                        else:
                                                                                                                                                                                                                            address0 = FAILURE
                                                                                                                                                                                                                            if self._offset > self._failure:
                                                                                                                                                                                                                                self._failure = self._offset
                                                                                                                                                                                                                                self._expected = []
                                                                                                                                                                                                                            if self._offset == self._failure:
                                                                                                                                                                                                                                self._expected.append('"Hg"')
                                                                                                                                                                                                                        if address0 is FAILURE:
                                                                                                                                                                                                                            self._offset = index1
                                                                                                                                                                                                                            chunk53 = None
                                                                                                                                                                                                                            if self._offset < self._input_size:
                                                                                                                                                                                                                                chunk53 = self._input[self._offset:self._offset + 2]
                                                                                                                                                                                                                            if chunk53 == 'Hf':
                                                                                                                                                                                                                                address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                                                                                                self._offset = self._offset + 2
                                                                                                                                                                                                                            else:
                                                                                                                                                                                                                                address0 = FAILURE
                                                                                                                                                                                                                                if self._offset > self._failure:
                                                                                                                                                                                                                                    self._failure = self._offset
                                                                                                                                                                                                                                    self._expected = []
                                                                                                                                                                                                                                if self._offset == self._failure:
                                                                                                                                                                                                                                    self._expected.append('"Hf"')
                                                                                                                                                                                                                            if address0 is FAILURE:
                                                                                                                                                                                                                                self._offset = index1
                                                                                                                                                                                                                                chunk54 = None
                                                                                                                                                                                                                                if self._offset < self._input_size:
                                                                                                                                                                                                                                    chunk54 = self._input[self._offset:self._offset + 2]
                                                                                                                                                                                                                                if chunk54 == 'He':
                                                                                                                                                                                                                                    address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                                                                                                    self._offset = self._offset + 2
                                                                                                                                                                                                                                else:
                                                                                                                                                                                                                                    address0 = FAILURE
                                                                                                                                                                                                                                    if self._offset > self._failure:
                                                                                                                                                                                                                                        self._failure = self._offset
                                                                                                                                                                                                                                        self._expected = []
                                                                                                                                                                                                                                    if self._offset == self._failure:
                                                                                                                                                                                                                                        self._expected.append('"He"')
                                                                                                                                                                                                                                if address0 is FAILURE:
                                                                                                                                                                                                                                    self._offset = index1
                                                                                                                                                                                                                                    chunk55 = None
                                                                                                                                                                                                                                    if self._offset < self._input_size:
                                                                                                                                                                                                                                        chunk55 = self._input[self._offset:self._offset + 1]
                                                                                                                                                                                                                                    if chunk55 == 'H':
                                                                                                                                                                                                                                        address0 = self._actions.make_element(self._input, self._offset, self._offset + 1)
                                                                                                                                                                                                                                        self._offset = self._offset + 1
                                                                                                                                                                                                                                    else:
                                                                                                                                                                                                                                        address0 = FAILURE
                                                                                                                                                                                                                                        if self._offset > self._failure:
                                                                                                                                                                                                                                            self._failure = self._offset
                                                                                                                                                                                                                                            self._expected = []
                                                                                                                                                                                                                                        if self._offset == self._failure:
                                                                                                                                                                                                                                            self._expected.append('"H"')
                                                                                                                                                                                                                                    if address0 is FAILURE:
                                                                                                                                                                                                                                        self._offset = index1
                                                                                                                                                                                                                                        chunk56 = None
                                                                                                                                                                                                                                        if self._offset < self._input_size:
                                                                                                                                                                                                                                            chunk56 = self._input[self._offset:self._offset + 2]
                                                                                                                                                                                                                                        if chunk56 == 'Ge':
                                                                                                                                                                                                                                            address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                                                                                                            self._offset = self._offset + 2
                                                                                                                                                                                                                                        else:
                                                                                                                                                                                                                                            address0 = FAILURE
                                                                                                                                                                                                                                            if self._offset > self._failure:
                                                                                                                                                                                                                                                self._failure = self._offset
                                                                                                                                                                                                                                                self._expected = []
                                                                                                                                                                                                                                            if self._offset == self._failure:
                                                                                                                                                                                                                                                self._expected.append('"Ge"')
                                                                                                                                                                                                                                        if address0 is FAILURE:
                                                                                                                                                                                                                                            self._offset = index1
                                                                                                                                                                                                                                            chunk57 = None
                                                                                                                                                                                                                                            if self._offset < self._input_size:
                                                                                                                                                                                                                                                chunk57 = self._input[self._offset:self._offset + 2]
                                                                                                                                                                                                                                            if chunk57 == 'Gd':
                                                                                                                                                                                                                                                address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                                                                                                                self._offset = self._offset + 2
                                                                                                                                                                                                                                            else:
                                                                                                                                                                                                                                                address0 = FAILURE
                                                                                                                                                                                                                                                if self._offset > self._failure:
                                                                                                                                                                                                                                                    self._failure = self._offset
                                                                                                                                                                                                                                                    self._expected = []
                                                                                                                                                                                                                                                if self._offset == self._failure:
                                                                                                                                                                                                                                                    self._expected.append('"Gd"')
                                                                                                                                                                                                                                            if address0 is FAILURE:
                                                                                                                                                                                                                                                self._offset = index1
                                                                                                                                                                                                                                                chunk58 = None
                                                                                                                                                                                                                                                if self._offset < self._input_size:
                                                                                                                                                                                                                                                    chunk58 = self._input[self._offset:self._offset + 2]
                                                                                                                                                                                                                                                if chunk58 == 'Ga':
                                                                                                                                                                                                                                                    address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                                                                                                                    self._offset = self._offset + 2
                                                                                                                                                                                                                                                else:
                                                                                                                                                                                                                                                    address0 = FAILURE
                                                                                                                                                                                                                                                    if self._offset > self._failure:
                                                                                                                                                                                                                                                        self._failure = self._offset
                                                                                                                                                                                                                                                        self._expected = []
                                                                                                                                                                                                                                                    if self._offset == self._failure:
                                                                                                                                                                                                                                                        self._expected.append('"Ga"')
                                                                                                                                                                                                                                                if address0 is FAILURE:
                                                                                                                                                                                                                                                    self._offset = index1
                                                                                                                                                                                                                                                    chunk59 = None
                                                                                                                                                                                                                                                    if self._offset < self._input_size:
                                                                                                                                                                                                                                                        chunk59 = self._input[self._offset:self._offset + 2]
                                                                                                                                                                                                                                                    if chunk59 == 'Fe':
                                                                                                                                                                                                                                                        address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                                                                                                                        self._offset = self._offset + 2
                                                                                                                                                                                                                                                    else:
                                                                                                                                                                                                                                                        address0 = FAILURE
                                                                                                                                                                                                                                                        if self._offset > self._failure:
                                                                                                                                                                                                                                                            self._failure = self._offset
                                                                                                                                                                                                                                                            self._expected = []
                                                                                                                                                                                                                                                        if self._offset == self._failure:
                                                                                                                                                                                                                                                            self._expected.append('"Fe"')
                                                                                                                                                                                                                                                    if address0 is FAILURE:
                                                                                                                                                                                                                                                        self._offset = index1
                                                                                                                                                                                                                                                        chunk60 = None
                                                                                                                                                                                                                                                        if self._offset < self._input_size:
                                                                                                                                                                                                                                                            chunk60 = self._input[self._offset:self._offset + 1]
                                                                                                                                                                                                                                                        if chunk60 == 'F':
                                                                                                                                                                                                                                                            address0 = self._actions.make_element(self._input, self._offset, self._offset + 1)
                                                                                                                                                                                                                                                            self._offset = self._offset + 1
                                                                                                                                                                                                                                                        else:
                                                                                                                                                                                                                                                            address0 = FAILURE
                                                                                                                                                                                                                                                            if self._offset > self._failure:
                                                                                                                                                                                                                                                                self._failure = self._offset
                                                                                                                                                                                                                                                                self._expected = []
                                                                                                                                                                                                                                                            if self._offset == self._failure:
                                                                                                                                                                                                                                                                self._expected.append('"F"')
                                                                                                                                                                                                                                                        if address0 is FAILURE:
                                                                                                                                                                                                                                                            self._offset = index1
                                                                                                                                                                                                                                                            chunk61 = None
                                                                                                                                                                                                                                                            if self._offset < self._input_size:
                                                                                                                                                                                                                                                                chunk61 = self._input[self._offset:self._offset + 2]
                                                                                                                                                                                                                                                            if chunk61 == 'Eu':
                                                                                                                                                                                                                                                                address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                                                                                                                                self._offset = self._offset + 2
                                                                                                                                                                                                                                                            else:
                                                                                                                                                                                                                                                                address0 = FAILURE
                                                                                                                                                                                                                                                                if self._offset > self._failure:
                                                                                                                                                                                                                                                                    self._failure = self._offset
                                                                                                                                                                                                                                                                    self._expected = []
                                                                                                                                                                                                                                                                if self._offset == self._failure:
                                                                                                                                                                                                                                                                    self._expected.append('"Eu"')
                                                                                                                                                                                                                                                            if address0 is FAILURE:
                                                                                                                                                                                                                                                                self._offset = index1
                                                                                                                                                                                                                                                                chunk62 = None
                                                                                                                                                                                                                                                                if self._offset < self._input_size:
                                                                                                                                                                                                                                                                    chunk62 = self._input[self._offset:self._offset + 2]
                                                                                                                                                                                                                                                                if chunk62 == 'Er':
                                                                                                                                                                                                                                                                    address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                                                                                                                                    self._offset = self._offset + 2
                                                                                                                                                                                                                                                                else:
                                                                                                                                                                                                                                                                    address0 = FAILURE
                                                                                                                                                                                                                                                                    if self._offset > self._failure:
                                                                                                                                                                                                                                                                        self._failure = self._offset
                                                                                                                                                                                                                                                                        self._expected = []
                                                                                                                                                                                                                                                                    if self._offset == self._failure:
                                                                                                                                                                                                                                                                        self._expected.append('"Er"')
                                                                                                                                                                                                                                                                if address0 is FAILURE:
                                                                                                                                                                                                                                                                    self._offset = index1
                                                                                                                                                                                                                                                                    chunk63 = None
                                                                                                                                                                                                                                                                    if self._offset < self._input_size:
                                                                                                                                                                                                                                                                        chunk63 = self._input[self._offset:self._offset + 2]
                                                                                                                                                                                                                                                                    if chunk63 == 'Dy':
                                                                                                                                                                                                                                                                        address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                                                                                                                                        self._offset = self._offset + 2
                                                                                                                                                                                                                                                                    else:
                                                                                                                                                                                                                                                                        address0 = FAILURE
                                                                                                                                                                                                                                                                        if self._offset > self._failure:
                                                                                                                                                                                                                                                                            self._failure = self._offset
                                                                                                                                                                                                                                                                            self._expected = []
                                                                                                                                                                                                                                                                        if self._offset == self._failure:
                                                                                                                                                                                                                                                                            self._expected.append('"Dy"')
                                                                                                                                                                                                                                                                    if address0 is FAILURE:
                                                                                                                                                                                                                                                                        self._offset = index1
                                                                                                                                                                                                                                                                        chunk64 = None
                                                                                                                                                                                                                                                                        if self._offset < self._input_size:
                                                                                                                                                                                                                                                                            chunk64 = self._input[self._offset:self._offset + 1]
                                                                                                                                                                                                                                                                        if chunk64 == 'D':
                                                                                                                                                                                                                                                                            address0 = self._actions.make_element(self._input, self._offset, self._offset + 1)
                                                                                                                                                                                                                                                                            self._offset = self._offset + 1
                                                                                                                                                                                                                                                                        else:
                                                                                                                                                                                                                                                                            address0 = FAILURE
                                                                                                                                                                                                                                                                            if self._offset > self._failure:
                                                                                                                                                                                                                                                                                self._failure = self._offset
                                                                                                                                                                                                                                                                                self._expected = []
                                                                                                                                                                                                                                                                            if self._offset == self._failure:
                                                                                                                                                                                                                                                                                self._expected.append('"D"')
                                                                                                                                                                                                                                                                        if address0 is FAILURE:
                                                                                                                                                                                                                                                                            self._offset = index1
                                                                                                                                                                                                                                                                            chunk65 = None
                                                                                                                                                                                                                                                                            if self._offset < self._input_size:
                                                                                                                                                                                                                                                                                chunk65 = self._input[self._offset:self._offset + 2]
                                                                                                                                                                                                                                                                            if chunk65 == 'Cu':
                                                                                                                                                                                                                                                                                address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                                                                                                                                                self._offset = self._offset + 2
                                                                                                                                                                                                                                                                            else:
                                                                                                                                                                                                                                                                                address0 = FAILURE
                                                                                                                                                                                                                                                                                if self._offset > self._failure:
                                                                                                                                                                                                                                                                                    self._failure = self._offset
                                                                                                                                                                                                                                                                                    self._expected = []
                                                                                                                                                                                                                                                                                if self._offset == self._failure:
                                                                                                                                                                                                                                                                                    self._expected.append('"Cu"')
                                                                                                                                                                                                                                                                            if address0 is FAILURE:
                                                                                                                                                                                                                                                                                self._offset = index1
                                                                                                                                                                                                                                                                                chunk66 = None
                                                                                                                                                                                                                                                                                if self._offset < self._input_size:
                                                                                                                                                                                                                                                                                    chunk66 = self._input[self._offset:self._offset + 2]
                                                                                                                                                                                                                                                                                if chunk66 == 'Cs':
                                                                                                                                                                                                                                                                                    address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                                                                                                                                                    self._offset = self._offset + 2
                                                                                                                                                                                                                                                                                else:
                                                                                                                                                                                                                                                                                    address0 = FAILURE
                                                                                                                                                                                                                                                                                    if self._offset > self._failure:
                                                                                                                                                                                                                                                                                        self._failure = self._offset
                                                                                                                                                                                                                                                                                        self._expected = []
                                                                                                                                                                                                                                                                                    if self._offset == self._failure:
                                                                                                                                                                                                                                                                                        self._expected.append('"Cs"')
                                                                                                                                                                                                                                                                                if address0 is FAILURE:
                                                                                                                                                                                                                                                                                    self._offset = index1
                                                                                                                                                                                                                                                                                    chunk67 = None
                                                                                                                                                                                                                                                                                    if self._offset < self._input_size:
                                                                                                                                                                                                                                                                                        chunk67 = self._input[self._offset:self._offset + 2]
                                                                                                                                                                                                                                                                                    if chunk67 == 'Cr':
                                                                                                                                                                                                                                                                                        address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                                                                                                                                                        self._offset = self._offset + 2
                                                                                                                                                                                                                                                                                    else:
                                                                                                                                                                                                                                                                                        address0 = FAILURE
                                                                                                                                                                                                                                                                                        if self._offset > self._failure:
                                                                                                                                                                                                                                                                                            self._failure = self._offset
                                                                                                                                                                                                                                                                                            self._expected = []
                                                                                                                                                                                                                                                                                        if self._offset == self._failure:
                                                                                                                                                                                                                                                                                            self._expected.append('"Cr"')
                                                                                                                                                                                                                                                                                    if address0 is FAILURE:
                                                                                                                                                                                                                                                                                        self._offset = index1
                                                                                                                                                                                                                                                                                        chunk68 = None
                                                                                                                                                                                                                                                                                        if self._offset < self._input_size:
                                                                                                                                                                                                                                                                                            chunk68 = self._input[self._offset:self._offset + 2]
                                                                                                                                                                                                                                                                                        if chunk68 == 'Co':
                                                                                                                                                                                                                                                                                            address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                                                                                                                                                            self._offset = self._offset + 2
                                                                                                                                                                                                                                                                                        else:
                                                                                                                                                                                                                                                                                            address0 = FAILURE
                                                                                                                                                                                                                                                                                            if self._offset > self._failure:
                                                                                                                                                                                                                                                                                                self._failure = self._offset
                                                                                                                                                                                                                                                                                                self._expected = []
                                                                                                                                                                                                                                                                                            if self._offset == self._failure:
                                                                                                                                                                                                                                                                                                self._expected.append('"Co"')
                                                                                                                                                                                                                                                                                        if address0 is FAILURE:
                                                                                                                                                                                                                                                                                            self._offset = index1
                                                                                                                                                                                                                                                                                            chunk69 = None
                                                                                                                                                                                                                                                                                            if self._offset < self._input_size:
                                                                                                                                                                                                                                                                                                chunk69 = self._input[self._offset:self._offset + 2]
                                                                                                                                                                                                                                                                                            if chunk69 == 'Cl':
                                                                                                                                                                                                                                                                                                address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                                                                                                                                                                self._offset = self._offset + 2
                                                                                                                                                                                                                                                                                            else:
                                                                                                                                                                                                                                                                                                address0 = FAILURE
                                                                                                                                                                                                                                                                                                if self._offset > self._failure:
                                                                                                                                                                                                                                                                                                    self._failure = self._offset
                                                                                                                                                                                                                                                                                                    self._expected = []
                                                                                                                                                                                                                                                                                                if self._offset == self._failure:
                                                                                                                                                                                                                                                                                                    self._expected.append('"Cl"')
                                                                                                                                                                                                                                                                                            if address0 is FAILURE:
                                                                                                                                                                                                                                                                                                self._offset = index1
                                                                                                                                                                                                                                                                                                chunk70 = None
                                                                                                                                                                                                                                                                                                if self._offset < self._input_size:
                                                                                                                                                                                                                                                                                                    chunk70 = self._input[self._offset:self._offset + 2]
                                                                                                                                                                                                                                                                                                if chunk70 == 'Ce':
                                                                                                                                                                                                                                                                                                    address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                                                                                                                                                                    self._offset = self._offset + 2
                                                                                                                                                                                                                                                                                                else:
                                                                                                                                                                                                                                                                                                    address0 = FAILURE
                                                                                                                                                                                                                                                                                                    if self._offset > self._failure:
                                                                                                                                                                                                                                                                                                        self._failure = self._offset
                                                                                                                                                                                                                                                                                                        self._expected = []
                                                                                                                                                                                                                                                                                                    if self._offset == self._failure:
                                                                                                                                                                                                                                                                                                        self._expected.append('"Ce"')
                                                                                                                                                                                                                                                                                                if address0 is FAILURE:
                                                                                                                                                                                                                                                                                                    self._offset = index1
                                                                                                                                                                                                                                                                                                    chunk71 = None
                                                                                                                                                                                                                                                                                                    if self._offset < self._input_size:
                                                                                                                                                                                                                                                                                                        chunk71 = self._input[self._offset:self._offset + 2]
                                                                                                                                                                                                                                                                                                    if chunk71 == 'Cd':
                                                                                                                                                                                                                                                                                                        address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                                                                                                                                                                        self._offset = self._offset + 2
                                                                                                                                                                                                                                                                                                    else:
                                                                                                                                                                                                                                                                                                        address0 = FAILURE
                                                                                                                                                                                                                                                                                                        if self._offset > self._failure:
                                                                                                                                                                                                                                                                                                            self._failure = self._offset
                                                                                                                                                                                                                                                                                                            self._expected = []
                                                                                                                                                                                                                                                                                                        if self._offset == self._failure:
                                                                                                                                                                                                                                                                                                            self._expected.append('"Cd"')
                                                                                                                                                                                                                                                                                                    if address0 is FAILURE:
                                                                                                                                                                                                                                                                                                        self._offset = index1
                                                                                                                                                                                                                                                                                                        chunk72 = None
                                                                                                                                                                                                                                                                                                        if self._offset < self._input_size:
                                                                                                                                                                                                                                                                                                            chunk72 = self._input[self._offset:self._offset + 2]
                                                                                                                                                                                                                                                                                                        if chunk72 == 'Ca':
                                                                                                                                                                                                                                                                                                            address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                                                                                                                                                                            self._offset = self._offset + 2
                                                                                                                                                                                                                                                                                                        else:
                                                                                                                                                                                                                                                                                                            address0 = FAILURE
                                                                                                                                                                                                                                                                                                            if self._offset > self._failure:
                                                                                                                                                                                                                                                                                                                self._failure = self._offset
                                                                                                                                                                                                                                                                                                                self._expected = []
                                                                                                                                                                                                                                                                                                            if self._offset == self._failure:
                                                                                                                                                                                                                                                                                                                self._expected.append('"Ca"')
                                                                                                                                                                                                                                                                                                        if address0 is FAILURE:
                                                                                                                                                                                                                                                                                                            self._offset = index1
                                                                                                                                                                                                                                                                                                            chunk73 = None
                                                                                                                                                                                                                                                                                                            if self._offset < self._input_size:
                                                                                                                                                                                                                                                                                                                chunk73 = self._input[self._offset:self._offset + 1]
                                                                                                                                                                                                                                                                                                            if chunk73 == 'C':
                                                                                                                                                                                                                                                                                                                address0 = self._actions.make_element(self._input, self._offset, self._offset + 1)
                                                                                                                                                                                                                                                                                                                self._offset = self._offset + 1
                                                                                                                                                                                                                                                                                                            else:
                                                                                                                                                                                                                                                                                                                address0 = FAILURE
                                                                                                                                                                                                                                                                                                                if self._offset > self._failure:
                                                                                                                                                                                                                                                                                                                    self._failure = self._offset
                                                                                                                                                                                                                                                                                                                    self._expected = []
                                                                                                                                                                                                                                                                                                                if self._offset == self._failure:
                                                                                                                                                                                                                                                                                                                    self._expected.append('"C"')
                                                                                                                                                                                                                                                                                                            if address0 is FAILURE:
                                                                                                                                                                                                                                                                                                                self._offset = index1
                                                                                                                                                                                                                                                                                                                chunk74 = None
                                                                                                                                                                                                                                                                                                                if self._offset < self._input_size:
                                                                                                                                                                                                                                                                                                                    chunk74 = self._input[self._offset:self._offset + 2]
                                                                                                                                                                                                                                                                                                                if chunk74 == 'Br':
                                                                                                                                                                                                                                                                                                                    address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                                                                                                                                                                                    self._offset = self._offset + 2
                                                                                                                                                                                                                                                                                                                else:
                                                                                                                                                                                                                                                                                                                    address0 = FAILURE
                                                                                                                                                                                                                                                                                                                    if self._offset > self._failure:
                                                                                                                                                                                                                                                                                                                        self._failure = self._offset
                                                                                                                                                                                                                                                                                                                        self._expected = []
                                                                                                                                                                                                                                                                                                                    if self._offset == self._failure:
                                                                                                                                                                                                                                                                                                                        self._expected.append('"Br"')
                                                                                                                                                                                                                                                                                                                if address0 is FAILURE:
                                                                                                                                                                                                                                                                                                                    self._offset = index1
                                                                                                                                                                                                                                                                                                                    chunk75 = None
                                                                                                                                                                                                                                                                                                                    if self._offset < self._input_size:
                                                                                                                                                                                                                                                                                                                        chunk75 = self._input[self._offset:self._offset + 2]
                                                                                                                                                                                                                                                                                                                    if chunk75 == 'Bi':
                                                                                                                                                                                                                                                                                                                        address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                                                                                                                                                                                        self._offset = self._offset + 2
                                                                                                                                                                                                                                                                                                                    else:
                                                                                                                                                                                                                                                                                                                        address0 = FAILURE
                                                                                                                                                                                                                                                                                                                        if self._offset > self._failure:
                                                                                                                                                                                                                                                                                                                            self._failure = self._offset
                                                                                                                                                                                                                                                                                                                            self._expected = []
                                                                                                                                                                                                                                                                                                                        if self._offset == self._failure:
                                                                                                                                                                                                                                                                                                                            self._expected.append('"Bi"')
                                                                                                                                                                                                                                                                                                                    if address0 is FAILURE:
                                                                                                                                                                                                                                                                                                                        self._offset = index1
                                                                                                                                                                                                                                                                                                                        chunk76 = None
                                                                                                                                                                                                                                                                                                                        if self._offset < self._input_size:
                                                                                                                                                                                                                                                                                                                            chunk76 = self._input[self._offset:self._offset + 2]
                                                                                                                                                                                                                                                                                                                        if chunk76 == 'Be':
                                                                                                                                                                                                                                                                                                                            address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                                                                                                                                                                                            self._offset = self._offset + 2
                                                                                                                                                                                                                                                                                                                        else:
                                                                                                                                                                                                                                                                                                                            address0 = FAILURE
                                                                                                                                                                                                                                                                                                                            if self._offset > self._failure:
                                                                                                                                                                                                                                                                                                                                self._failure = self._offset
                                                                                                                                                                                                                                                                                                                                self._expected = []
                                                                                                                                                                                                                                                                                                                            if self._offset == self._failure:
                                                                                                                                                                                                                                                                                                                                self._expected.append('"Be"')
                                                                                                                                                                                                                                                                                                                        if address0 is FAILURE:
                                                                                                                                                                                                                                                                                                                            self._offset = index1
                                                                                                                                                                                                                                                                                                                            chunk77 = None
                                                                                                                                                                                                                                                                                                                            if self._offset < self._input_size:
                                                                                                                                                                                                                                                                                                                                chunk77 = self._input[self._offset:self._offset + 2]
                                                                                                                                                                                                                                                                                                                            if chunk77 == 'Ba':
                                                                                                                                                                                                                                                                                                                                address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                                                                                                                                                                                                self._offset = self._offset + 2
                                                                                                                                                                                                                                                                                                                            else:
                                                                                                                                                                                                                                                                                                                                address0 = FAILURE
                                                                                                                                                                                                                                                                                                                                if self._offset > self._failure:
                                                                                                                                                                                                                                                                                                                                    self._failure = self._offset
                                                                                                                                                                                                                                                                                                                                    self._expected = []
                                                                                                                                                                                                                                                                                                                                if self._offset == self._failure:
                                                                                                                                                                                                                                                                                                                                    self._expected.append('"Ba"')
                                                                                                                                                                                                                                                                                                                            if address0 is FAILURE:
                                                                                                                                                                                                                                                                                                                                self._offset = index1
                                                                                                                                                                                                                                                                                                                                chunk78 = None
                                                                                                                                                                                                                                                                                                                                if self._offset < self._input_size:
                                                                                                                                                                                                                                                                                                                                    chunk78 = self._input[self._offset:self._offset + 1]
                                                                                                                                                                                                                                                                                                                                if chunk78 == 'B':
                                                                                                                                                                                                                                                                                                                                    address0 = self._actions.make_element(self._input, self._offset, self._offset + 1)
                                                                                                                                                                                                                                                                                                                                    self._offset = self._offset + 1
                                                                                                                                                                                                                                                                                                                                else:
                                                                                                                                                                                                                                                                                                                                    address0 = FAILURE
                                                                                                                                                                                                                                                                                                                                    if self._offset > self._failure:
                                                                                                                                                                                                                                                                                                                                        self._failure = self._offset
                                                                                                                                                                                                                                                                                                                                        self._expected = []
                                                                                                                                                                                                                                                                                                                                    if self._offset == self._failure:
                                                                                                                                                                                                                                                                                                                                        self._expected.append('"B"')
                                                                                                                                                                                                                                                                                                                                if address0 is FAILURE:
                                                                                                                                                                                                                                                                                                                                    self._offset = index1
                                                                                                                                                                                                                                                                                                                                    chunk79 = None
                                                                                                                                                                                                                                                                                                                                    if self._offset < self._input_size:
                                                                                                                                                                                                                                                                                                                                        chunk79 = self._input[self._offset:self._offset + 2]
                                                                                                                                                                                                                                                                                                                                    if chunk79 == 'Au':
                                                                                                                                                                                                                                                                                                                                        address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                                                                                                                                                                                                        self._offset = self._offset + 2
                                                                                                                                                                                                                                                                                                                                    else:
                                                                                                                                                                                                                                                                                                                                        address0 = FAILURE
                                                                                                                                                                                                                                                                                                                                        if self._offset > self._failure:
                                                                                                                                                                                                                                                                                                                                            self._failure = self._offset
                                                                                                                                                                                                                                                                                                                                            self._expected = []
                                                                                                                                                                                                                                                                                                                                        if self._offset == self._failure:
                                                                                                                                                                                                                                                                                                                                            self._expected.append('"Au"')
                                                                                                                                                                                                                                                                                                                                    if address0 is FAILURE:
                                                                                                                                                                                                                                                                                                                                        self._offset = index1
                                                                                                                                                                                                                                                                                                                                        chunk80 = None
                                                                                                                                                                                                                                                                                                                                        if self._offset < self._input_size:
                                                                                                                                                                                                                                                                                                                                            chunk80 = self._input[self._offset:self._offset + 2]
                                                                                                                                                                                                                                                                                                                                        if chunk80 == 'As':
                                                                                                                                                                                                                                                                                                                                            address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                                                                                                                                                                                                            self._offset = self._offset + 2
                                                                                                                                                                                                                                                                                                                                        else:
                                                                                                                                                                                                                                                                                                                                            address0 = FAILURE
                                                                                                                                                                                                                                                                                                                                            if self._offset > self._failure:
                                                                                                                                                                                                                                                                                                                                                self._failure = self._offset
                                                                                                                                                                                                                                                                                                                                                self._expected = []
                                                                                                                                                                                                                                                                                                                                            if self._offset == self._failure:
                                                                                                                                                                                                                                                                                                                                                self._expected.append('"As"')
                                                                                                                                                                                                                                                                                                                                        if address0 is FAILURE:
                                                                                                                                                                                                                                                                                                                                            self._offset = index1
                                                                                                                                                                                                                                                                                                                                            chunk81 = None
                                                                                                                                                                                                                                                                                                                                            if self._offset < self._input_size:
                                                                                                                                                                                                                                                                                                                                                chunk81 = self._input[self._offset:self._offset + 2]
                                                                                                                                                                                                                                                                                                                                            if chunk81 == 'Ar':
                                                                                                                                                                                                                                                                                                                                                address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                                                                                                                                                                                                                self._offset = self._offset + 2
                                                                                                                                                                                                                                                                                                                                            else:
                                                                                                                                                                                                                                                                                                                                                address0 = FAILURE
                                                                                                                                                                                                                                                                                                                                                if self._offset > self._failure:
                                                                                                                                                                                                                                                                                                                                                    self._failure = self._offset
                                                                                                                                                                                                                                                                                                                                                    self._expected = []
                                                                                                                                                                                                                                                                                                                                                if self._offset == self._failure:
                                                                                                                                                                                                                                                                                                                                                    self._expected.append('"Ar"')
                                                                                                                                                                                                                                                                                                                                            if address0 is FAILURE:
                                                                                                                                                                                                                                                                                                                                                self._offset = index1
                                                                                                                                                                                                                                                                                                                                                chunk82 = None
                                                                                                                                                                                                                                                                                                                                                if self._offset < self._input_size:
                                                                                                                                                                                                                                                                                                                                                    chunk82 = self._input[self._offset:self._offset + 2]
                                                                                                                                                                                                                                                                                                                                                if chunk82 == 'Al':
                                                                                                                                                                                                                                                                                                                                                    address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                                                                                                                                                                                                                    self._offset = self._offset + 2
                                                                                                                                                                                                                                                                                                                                                else:
                                                                                                                                                                                                                                                                                                                                                    address0 = FAILURE
                                                                                                                                                                                                                                                                                                                                                    if self._offset > self._failure:
                                                                                                                                                                                                                                                                                                                                                        self._failure = self._offset
                                                                                                                                                                                                                                                                                                                                                        self._expected = []
                                                                                                                                                                                                                                                                                                                                                    if self._offset == self._failure:
                                                                                                                                                                                                                                                                                                                                                        self._expected.append('"Al"')
                                                                                                                                                                                                                                                                                                                                                if address0 is FAILURE:
                                                                                                                                                                                                                                                                                                                                                    self._offset = index1
                                                                                                                                                                                                                                                                                                                                                    chunk83 = None
                                                                                                                                                                                                                                                                                                                                                    if self._offset < self._input_size:
                                                                                                                                                                                                                                                                                                                                                        chunk83 = self._input[self._offset:self._offset + 2]
                                                                                                                                                                                                                                                                                                                                                    if chunk83 == 'Ag':
                                                                                                                                                                                                                                                                                                                                                        address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                                                                                                                                                                                                                        self._offset = self._offset + 2
                                                                                                                                                                                                                                                                                                                                                    else:
                                                                                                                                                                                                                                                                                                                                                        address0 = FAILURE
                                                                                                                                                                                                                                                                                                                                                        if self._offset > self._failure:
                                                                                                                                                                                                                                                                                                                                                            self._failure = self._offset
                                                                                                                                                                                                                                                                                                                                                            self._expected = []
                                                                                                                                                                                                                                                                                                                                                        if self._offset == self._failure:
                                                                                                                                                                                                                                                                                                                                                            self._expected.append('"Ag"')
                                                                                                                                                                                                                                                                                                                                                    if address0 is FAILURE:
                                                                                                                                                                                                                                                                                                                                                        self._offset = index1
                                                                                                                                                                                                                                                                                                                                                        chunk84 = None
                                                                                                                                                                                                                                                                                                                                                        if self._offset < self._input_size:
                                                                                                                                                                                                                                                                                                                                                            chunk84 = self._input[self._offset:self._offset + 1]
                                                                                                                                                                                                                                                                                                                                                        if chunk84 == 'e':
                                                                                                                                                                                                                                                                                                                                                            address0 = self._actions.make_element(self._input, self._offset, self._offset + 1)
                                                                                                                                                                                                                                                                                                                                                            self._offset = self._offset + 1
                                                                                                                                                                                                                                                                                                                                                        else:
                                                                                                                                                                                                                                                                                                                                                            address0 = FAILURE
                                                                                                                                                                                                                                                                                                                                                            if self._offset > self._failure:
                                                                                                                                                                                                                                                                                                                                                                self._failure = self._offset
                                                                                                                                                                                                                                                                                                                                                                self._expected = []
                                                                                                                                                                                                                                                                                                                                                            if self._offset == self._failure:
                                                                                                                                                                                                                                                                                                                                                                self._expected.append('"e"')
                                                                                                                                                                                                                                                                                                                                                        if address0 is FAILURE:
                                                                                                                                                                                                                                                                                                                                                            self._offset = index1
        self._cache['element'][index0] = (address0, self._offset)
        return address0

    def _read_sub_formula(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['sub_formula'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        index1, elements0 = self._offset, []
        address1 = FAILURE
        chunk0 = None
        if self._offset < self._input_size:
            chunk0 = self._input[self._offset:self._offset + 1]
        if chunk0 == '(':
            address1 = nist_ion_descriptions_TreeNode(self._input[self._offset:self._offset + 1], self._offset)
            self._offset = self._offset + 1
        else:
            address1 = FAILURE
            if self._offset > self._failure:
                self._failure = self._offset
                self._expected = []
            if self._offset == self._failure:
                self._expected.append('"("')
        if address1 is not FAILURE:
            elements0.append(address1)
            address2 = FAILURE
            address2 = self._read_formula()
            if address2 is not FAILURE:
                elements0.append(address2)
                address3 = FAILURE
                chunk1 = None
                if self._offset < self._input_size:
                    chunk1 = self._input[self._offset:self._offset + 1]
                if chunk1 == ')':
                    address3 = nist_ion_descriptions_TreeNode(self._input[self._offset:self._offset + 1], self._offset)
                    self._offset = self._offset + 1
                else:
                    address3 = FAILURE
                    if self._offset > self._failure:
                        self._failure = self._offset
                        self._expected = []
                    if self._offset == self._failure:
                        self._expected.append('")"')
                if address3 is not FAILURE:
                    elements0.append(address3)
                else:
                    elements0 = None
                    self._offset = index1
            else:
                elements0 = None
                self._offset = index1
        else:
            elements0 = None
            self._offset = index1
        if elements0 is None:
            address0 = FAILURE
        else:
            address0 = self._actions.make_sub_formula(self._input, index1, self._offset, elements0)
            self._offset = self._offset
        self._cache['sub_formula'][index0] = (address0, self._offset)
        return address0

    def _read_count(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['count'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        index1 = self._offset
        address0 = self._read_n()
        if address0 is FAILURE:
            address0 = nist_ion_descriptions_TreeNode(self._input[index1:index1], index1)
            self._offset = index1
        self._cache['count'][index0] = (address0, self._offset)
        return address0

    def _read_n(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['n'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        index1, elements0 = self._offset, []
        address1 = FAILURE
        address1 = self._read_non_zero_digit()
        if address1 is not FAILURE:
            elements0.append(address1)
            address2 = FAILURE
            remaining0, index2, elements1, address3 = 0, self._offset, [], True
            while address3 is not FAILURE:
                address3 = self._read_digit()
                if address3 is not FAILURE:
                    elements1.append(address3)
                    remaining0 -= 1
            if remaining0 <= 0:
                address2 = nist_ion_descriptions_TreeNode(self._input[index2:self._offset], index2, elements1)
                self._offset = self._offset
            else:
                address2 = FAILURE
            if address2 is not FAILURE:
                elements0.append(address2)
            else:
                elements0 = None
                self._offset = index1
        else:
            elements0 = None
            self._offset = index1
        if elements0 is None:
            address0 = FAILURE
        else:
            address0 = nist_ion_descriptions_TreeNode8(self._input[index1:self._offset], index1, elements0)
            self._offset = self._offset
        self._cache['n'][index0] = (address0, self._offset)
        return address0

    def _read_non_zero_digit(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['non_zero_digit'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        chunk0 = None
        if self._offset < self._input_size:
            chunk0 = self._input[self._offset:self._offset + 1]
        if chunk0 is not None and nist_ion_descriptions_Grammar.REGEX_1.search(chunk0):
            address0 = nist_ion_descriptions_TreeNode(self._input[self._offset:self._offset + 1], self._offset)
            self._offset = self._offset + 1
        else:
            address0 = FAILURE
            if self._offset > self._failure:
                self._failure = self._offset
                self._expected = []
            if self._offset == self._failure:
                self._expected.append('[1-9]')
        self._cache['non_zero_digit'][index0] = (address0, self._offset)
        return address0

    def _read_digit(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['digit'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        chunk0 = None
        if self._offset < self._input_size:
            chunk0 = self._input[self._offset:self._offset + 1]
        if chunk0 is not None and nist_ion_descriptions_Grammar.REGEX_2.search(chunk0):
            address0 = nist_ion_descriptions_TreeNode(self._input[self._offset:self._offset + 1], self._offset)
            self._offset = self._offset + 1
        else:
            address0 = FAILURE
            if self._offset > self._failure:
                self._failure = self._offset
                self._expected = []
            if self._offset == self._failure:
                self._expected.append('[0-9]')
        self._cache['digit'][index0] = (address0, self._offset)
        return address0

    def _read_mass(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['mass'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        index1, elements0 = self._offset, []
        address1 = FAILURE
        index2 = self._offset
        chunk0 = None
        if self._offset < self._input_size:
            chunk0 = self._input[self._offset:self._offset + 1]
        if chunk0 == '0':
            address1 = nist_ion_descriptions_TreeNode(self._input[self._offset:self._offset + 1], self._offset)
            self._offset = self._offset + 1
        else:
            address1 = FAILURE
            if self._offset > self._failure:
                self._failure = self._offset
                self._expected = []
            if self._offset == self._failure:
                self._expected.append('"0"')
        if address1 is FAILURE:
            self._offset = index2
            address1 = self._read_n()
            if address1 is FAILURE:
                self._offset = index2
        if address1 is not FAILURE:
            elements0.append(address1)
            address2 = FAILURE
            address2 = self._read_decimal()
            if address2 is not FAILURE:
                elements0.append(address2)
            else:
                elements0 = None
                self._offset = index1
        else:
            elements0 = None
            self._offset = index1
        if elements0 is None:
            address0 = FAILURE
        else:
            address0 = self._actions.make_mass(self._input, index1, self._offset, elements0)
            self._offset = self._offset
        self._cache['mass'][index0] = (address0, self._offset)
        return address0

    def _read_decimal(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['decimal'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        index1 = self._offset
        index2, elements0 = self._offset, []
        address1 = FAILURE
        chunk0 = None
        if self._offset < self._input_size:
            chunk0 = self._input[self._offset:self._offset + 1]
        if chunk0 == '.':
            address1 = nist_ion_descriptions_TreeNode(self._input[self._offset:self._offset + 1], self._offset)
            self._offset = self._offset + 1
        else:
            address1 = FAILURE
            if self._offset > self._failure:
                self._failure = self._offset
                self._expected = []
            if self._offset == self._failure:
                self._expected.append('"."')
        if address1 is not FAILURE:
            elements0.append(address1)
            address2 = FAILURE
            remaining0, index3, elements1, address3 = 0, self._offset, [], True
            while address3 is not FAILURE:
                address3 = self._read_digit()
                if address3 is not FAILURE:
                    elements1.append(address3)
                    remaining0 -= 1
            if remaining0 <= 0:
                address2 = nist_ion_descriptions_TreeNode(self._input[index3:self._offset], index3, elements1)
                self._offset = self._offset
            else:
                address2 = FAILURE
            if address2 is not FAILURE:
                elements0.append(address2)
            else:
                elements0 = None
                self._offset = index2
        else:
            elements0 = None
            self._offset = index2
        if elements0 is None:
            address0 = FAILURE
        else:
            address0 = nist_ion_descriptions_TreeNode(self._input[index2:self._offset], index2, elements0)
            self._offset = self._offset
        if address0 is FAILURE:
            address0 = nist_ion_descriptions_TreeNode(self._input[index1:index1], index1)
            self._offset = index1
        self._cache['decimal'][index0] = (address0, self._offset)
        return address0


class nist_ion_descriptions_Parser(nist_ion_descriptions_Grammar):
    def __init__(self, input, actions, types):
        self._input = input
        self._input_size = len(input)
        self._actions = actions
        self._types = types
        self._offset = 0
        self._cache = defaultdict(dict)
        self._failure = 0
        self._expected = []

    def parse(self):
        tree = self._read_ion_type()
        if tree is not FAILURE and self._offset == self._input_size:
            return tree
        if not self._expected:
            self._failure = self._offset
            self._expected.append('<EOF>')
        raise nist_ion_descriptions_ParseError(nist_ion_descriptions_format_error(self._input, self._failure, self._expected))


def nist_ion_descriptions_format_error(input, offset, expected):
    lines, line_no, position = input.split('\n'), 0, 0
    while position <= offset:
        position += len(lines[line_no]) + 1
        line_no += 1
    message, line = 'Line ' + str(line_no) + ': expected ' + ', '.join(expected) + '\n', lines[line_no - 1]
    message += line + '\n'
    position -= len(line) + 1
    message += ' ' * (offset - position)
    return message + '^'

def nist_ion_descriptions_parse(input, actions=None, types=None):
    parser = nist_ion_descriptions_Parser(input, actions, types)
    return parser.parse()

# EMBEDDED: import formula

class formula_TreeNode(object):
    def __init__(self, text, offset, elements=None):
        self.text = text
        self.offset = offset
        self.elements = elements or []

    def __iter__(self):
        for el in self.elements:
            yield el


class formula_TreeNode1(formula_TreeNode):
    def __init__(self, text, offset, elements):
        super(formula_TreeNode1, self).__init__(text, offset, elements)
        self.element = elements[0]
        self.count = elements[1]


class formula_TreeNode2(formula_TreeNode):
    def __init__(self, text, offset, elements):
        super(formula_TreeNode2, self).__init__(text, offset, elements)
        self.non_zero_digit = elements[0]


class formula_ParseError(SyntaxError):
    pass


class formula_Grammar(object):
    REGEX_1 = re.compile('^[1-9]')
    REGEX_2 = re.compile('^[0-9]')

    def _read_formula(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['formula'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        remaining0, index1, elements0, address1 = 1, self._offset, [], True
        while address1 is not FAILURE:
            address1 = self._read_term()
            if address1 is not FAILURE:
                elements0.append(address1)
                remaining0 -= 1
        if remaining0 <= 0:
            address0 = formula_TreeNode(self._input[index1:self._offset], index1, elements0)
            self._offset = self._offset
        else:
            address0 = FAILURE
        self._cache['formula'][index0] = (address0, self._offset)
        return address0

    def _read_term(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['term'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        index1, elements0 = self._offset, []
        address1 = FAILURE
        address1 = self._read_element()
        if address1 is not FAILURE:
            elements0.append(address1)
            address2 = FAILURE
            address2 = self._read_count()
            if address2 is not FAILURE:
                elements0.append(address2)
            else:
                elements0 = None
                self._offset = index1
        else:
            elements0 = None
            self._offset = index1
        if elements0 is None:
            address0 = FAILURE
        else:
            address0 = self._actions.make_term(self._input, index1, self._offset, elements0)
            self._offset = self._offset
        self._cache['term'][index0] = (address0, self._offset)
        return address0

    def _read_element(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['element'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        index1 = self._offset
        chunk0 = None
        if self._offset < self._input_size:
            chunk0 = self._input[self._offset:self._offset + 2]
        if chunk0 == 'Zr':
            address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
            self._offset = self._offset + 2
        else:
            address0 = FAILURE
            if self._offset > self._failure:
                self._failure = self._offset
                self._expected = []
            if self._offset == self._failure:
                self._expected.append('"Zr"')
        if address0 is FAILURE:
            self._offset = index1
            chunk1 = None
            if self._offset < self._input_size:
                chunk1 = self._input[self._offset:self._offset + 2]
            if chunk1 == 'Zn':
                address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                self._offset = self._offset + 2
            else:
                address0 = FAILURE
                if self._offset > self._failure:
                    self._failure = self._offset
                    self._expected = []
                if self._offset == self._failure:
                    self._expected.append('"Zn"')
            if address0 is FAILURE:
                self._offset = index1
                chunk2 = None
                if self._offset < self._input_size:
                    chunk2 = self._input[self._offset:self._offset + 2]
                if chunk2 == 'Yb':
                    address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                    self._offset = self._offset + 2
                else:
                    address0 = FAILURE
                    if self._offset > self._failure:
                        self._failure = self._offset
                        self._expected = []
                    if self._offset == self._failure:
                        self._expected.append('"Yb"')
                if address0 is FAILURE:
                    self._offset = index1
                    chunk3 = None
                    if self._offset < self._input_size:
                        chunk3 = self._input[self._offset:self._offset + 1]
                    if chunk3 == 'Y':
                        address0 = self._actions.make_element(self._input, self._offset, self._offset + 1)
                        self._offset = self._offset + 1
                    else:
                        address0 = FAILURE
                        if self._offset > self._failure:
                            self._failure = self._offset
                            self._expected = []
                        if self._offset == self._failure:
                            self._expected.append('"Y"')
                    if address0 is FAILURE:
                        self._offset = index1
                        chunk4 = None
                        if self._offset < self._input_size:
                            chunk4 = self._input[self._offset:self._offset + 2]
                        if chunk4 == 'Xe':
                            address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                            self._offset = self._offset + 2
                        else:
                            address0 = FAILURE
                            if self._offset > self._failure:
                                self._failure = self._offset
                                self._expected = []
                            if self._offset == self._failure:
                                self._expected.append('"Xe"')
                        if address0 is FAILURE:
                            self._offset = index1
                            chunk5 = None
                            if self._offset < self._input_size:
                                chunk5 = self._input[self._offset:self._offset + 1]
                            if chunk5 == 'W':
                                address0 = self._actions.make_element(self._input, self._offset, self._offset + 1)
                                self._offset = self._offset + 1
                            else:
                                address0 = FAILURE
                                if self._offset > self._failure:
                                    self._failure = self._offset
                                    self._expected = []
                                if self._offset == self._failure:
                                    self._expected.append('"W"')
                            if address0 is FAILURE:
                                self._offset = index1
                                chunk6 = None
                                if self._offset < self._input_size:
                                    chunk6 = self._input[self._offset:self._offset + 1]
                                if chunk6 == 'V':
                                    address0 = self._actions.make_element(self._input, self._offset, self._offset + 1)
                                    self._offset = self._offset + 1
                                else:
                                    address0 = FAILURE
                                    if self._offset > self._failure:
                                        self._failure = self._offset
                                        self._expected = []
                                    if self._offset == self._failure:
                                        self._expected.append('"V"')
                                if address0 is FAILURE:
                                    self._offset = index1
                                    chunk7 = None
                                    if self._offset < self._input_size:
                                        chunk7 = self._input[self._offset:self._offset + 1]
                                    if chunk7 == 'U':
                                        address0 = self._actions.make_element(self._input, self._offset, self._offset + 1)
                                        self._offset = self._offset + 1
                                    else:
                                        address0 = FAILURE
                                        if self._offset > self._failure:
                                            self._failure = self._offset
                                            self._expected = []
                                        if self._offset == self._failure:
                                            self._expected.append('"U"')
                                    if address0 is FAILURE:
                                        self._offset = index1
                                        chunk8 = None
                                        if self._offset < self._input_size:
                                            chunk8 = self._input[self._offset:self._offset + 2]
                                        if chunk8 == 'Tm':
                                            address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                            self._offset = self._offset + 2
                                        else:
                                            address0 = FAILURE
                                            if self._offset > self._failure:
                                                self._failure = self._offset
                                                self._expected = []
                                            if self._offset == self._failure:
                                                self._expected.append('"Tm"')
                                        if address0 is FAILURE:
                                            self._offset = index1
                                            chunk9 = None
                                            if self._offset < self._input_size:
                                                chunk9 = self._input[self._offset:self._offset + 2]
                                            if chunk9 == 'Tl':
                                                address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                self._offset = self._offset + 2
                                            else:
                                                address0 = FAILURE
                                                if self._offset > self._failure:
                                                    self._failure = self._offset
                                                    self._expected = []
                                                if self._offset == self._failure:
                                                    self._expected.append('"Tl"')
                                            if address0 is FAILURE:
                                                self._offset = index1
                                                chunk10 = None
                                                if self._offset < self._input_size:
                                                    chunk10 = self._input[self._offset:self._offset + 2]
                                                if chunk10 == 'Ti':
                                                    address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                    self._offset = self._offset + 2
                                                else:
                                                    address0 = FAILURE
                                                    if self._offset > self._failure:
                                                        self._failure = self._offset
                                                        self._expected = []
                                                    if self._offset == self._failure:
                                                        self._expected.append('"Ti"')
                                                if address0 is FAILURE:
                                                    self._offset = index1
                                                    chunk11 = None
                                                    if self._offset < self._input_size:
                                                        chunk11 = self._input[self._offset:self._offset + 2]
                                                    if chunk11 == 'Th':
                                                        address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                        self._offset = self._offset + 2
                                                    else:
                                                        address0 = FAILURE
                                                        if self._offset > self._failure:
                                                            self._failure = self._offset
                                                            self._expected = []
                                                        if self._offset == self._failure:
                                                            self._expected.append('"Th"')
                                                    if address0 is FAILURE:
                                                        self._offset = index1
                                                        chunk12 = None
                                                        if self._offset < self._input_size:
                                                            chunk12 = self._input[self._offset:self._offset + 2]
                                                        if chunk12 == 'Te':
                                                            address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                            self._offset = self._offset + 2
                                                        else:
                                                            address0 = FAILURE
                                                            if self._offset > self._failure:
                                                                self._failure = self._offset
                                                                self._expected = []
                                                            if self._offset == self._failure:
                                                                self._expected.append('"Te"')
                                                        if address0 is FAILURE:
                                                            self._offset = index1
                                                            chunk13 = None
                                                            if self._offset < self._input_size:
                                                                chunk13 = self._input[self._offset:self._offset + 2]
                                                            if chunk13 == 'Tb':
                                                                address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                self._offset = self._offset + 2
                                                            else:
                                                                address0 = FAILURE
                                                                if self._offset > self._failure:
                                                                    self._failure = self._offset
                                                                    self._expected = []
                                                                if self._offset == self._failure:
                                                                    self._expected.append('"Tb"')
                                                            if address0 is FAILURE:
                                                                self._offset = index1
                                                                chunk14 = None
                                                                if self._offset < self._input_size:
                                                                    chunk14 = self._input[self._offset:self._offset + 2]
                                                                if chunk14 == 'Ta':
                                                                    address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                    self._offset = self._offset + 2
                                                                else:
                                                                    address0 = FAILURE
                                                                    if self._offset > self._failure:
                                                                        self._failure = self._offset
                                                                        self._expected = []
                                                                    if self._offset == self._failure:
                                                                        self._expected.append('"Ta"')
                                                                if address0 is FAILURE:
                                                                    self._offset = index1
                                                                    chunk15 = None
                                                                    if self._offset < self._input_size:
                                                                        chunk15 = self._input[self._offset:self._offset + 2]
                                                                    if chunk15 == 'Sr':
                                                                        address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                        self._offset = self._offset + 2
                                                                    else:
                                                                        address0 = FAILURE
                                                                        if self._offset > self._failure:
                                                                            self._failure = self._offset
                                                                            self._expected = []
                                                                        if self._offset == self._failure:
                                                                            self._expected.append('"Sr"')
                                                                    if address0 is FAILURE:
                                                                        self._offset = index1
                                                                        chunk16 = None
                                                                        if self._offset < self._input_size:
                                                                            chunk16 = self._input[self._offset:self._offset + 2]
                                                                        if chunk16 == 'Sn':
                                                                            address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                            self._offset = self._offset + 2
                                                                        else:
                                                                            address0 = FAILURE
                                                                            if self._offset > self._failure:
                                                                                self._failure = self._offset
                                                                                self._expected = []
                                                                            if self._offset == self._failure:
                                                                                self._expected.append('"Sn"')
                                                                        if address0 is FAILURE:
                                                                            self._offset = index1
                                                                            chunk17 = None
                                                                            if self._offset < self._input_size:
                                                                                chunk17 = self._input[self._offset:self._offset + 2]
                                                                            if chunk17 == 'Sm':
                                                                                address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                self._offset = self._offset + 2
                                                                            else:
                                                                                address0 = FAILURE
                                                                                if self._offset > self._failure:
                                                                                    self._failure = self._offset
                                                                                    self._expected = []
                                                                                if self._offset == self._failure:
                                                                                    self._expected.append('"Sm"')
                                                                            if address0 is FAILURE:
                                                                                self._offset = index1
                                                                                chunk18 = None
                                                                                if self._offset < self._input_size:
                                                                                    chunk18 = self._input[self._offset:self._offset + 2]
                                                                                if chunk18 == 'Si':
                                                                                    address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                    self._offset = self._offset + 2
                                                                                else:
                                                                                    address0 = FAILURE
                                                                                    if self._offset > self._failure:
                                                                                        self._failure = self._offset
                                                                                        self._expected = []
                                                                                    if self._offset == self._failure:
                                                                                        self._expected.append('"Si"')
                                                                                if address0 is FAILURE:
                                                                                    self._offset = index1
                                                                                    chunk19 = None
                                                                                    if self._offset < self._input_size:
                                                                                        chunk19 = self._input[self._offset:self._offset + 2]
                                                                                    if chunk19 == 'Se':
                                                                                        address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                        self._offset = self._offset + 2
                                                                                    else:
                                                                                        address0 = FAILURE
                                                                                        if self._offset > self._failure:
                                                                                            self._failure = self._offset
                                                                                            self._expected = []
                                                                                        if self._offset == self._failure:
                                                                                            self._expected.append('"Se"')
                                                                                    if address0 is FAILURE:
                                                                                        self._offset = index1
                                                                                        chunk20 = None
                                                                                        if self._offset < self._input_size:
                                                                                            chunk20 = self._input[self._offset:self._offset + 2]
                                                                                        if chunk20 == 'Sc':
                                                                                            address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                            self._offset = self._offset + 2
                                                                                        else:
                                                                                            address0 = FAILURE
                                                                                            if self._offset > self._failure:
                                                                                                self._failure = self._offset
                                                                                                self._expected = []
                                                                                            if self._offset == self._failure:
                                                                                                self._expected.append('"Sc"')
                                                                                        if address0 is FAILURE:
                                                                                            self._offset = index1
                                                                                            chunk21 = None
                                                                                            if self._offset < self._input_size:
                                                                                                chunk21 = self._input[self._offset:self._offset + 2]
                                                                                            if chunk21 == 'Sb':
                                                                                                address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                self._offset = self._offset + 2
                                                                                            else:
                                                                                                address0 = FAILURE
                                                                                                if self._offset > self._failure:
                                                                                                    self._failure = self._offset
                                                                                                    self._expected = []
                                                                                                if self._offset == self._failure:
                                                                                                    self._expected.append('"Sb"')
                                                                                            if address0 is FAILURE:
                                                                                                self._offset = index1
                                                                                                chunk22 = None
                                                                                                if self._offset < self._input_size:
                                                                                                    chunk22 = self._input[self._offset:self._offset + 1]
                                                                                                if chunk22 == 'S':
                                                                                                    address0 = self._actions.make_element(self._input, self._offset, self._offset + 1)
                                                                                                    self._offset = self._offset + 1
                                                                                                else:
                                                                                                    address0 = FAILURE
                                                                                                    if self._offset > self._failure:
                                                                                                        self._failure = self._offset
                                                                                                        self._expected = []
                                                                                                    if self._offset == self._failure:
                                                                                                        self._expected.append('"S"')
                                                                                                if address0 is FAILURE:
                                                                                                    self._offset = index1
                                                                                                    chunk23 = None
                                                                                                    if self._offset < self._input_size:
                                                                                                        chunk23 = self._input[self._offset:self._offset + 2]
                                                                                                    if chunk23 == 'Ru':
                                                                                                        address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                        self._offset = self._offset + 2
                                                                                                    else:
                                                                                                        address0 = FAILURE
                                                                                                        if self._offset > self._failure:
                                                                                                            self._failure = self._offset
                                                                                                            self._expected = []
                                                                                                        if self._offset == self._failure:
                                                                                                            self._expected.append('"Ru"')
                                                                                                    if address0 is FAILURE:
                                                                                                        self._offset = index1
                                                                                                        chunk24 = None
                                                                                                        if self._offset < self._input_size:
                                                                                                            chunk24 = self._input[self._offset:self._offset + 2]
                                                                                                        if chunk24 == 'Rh':
                                                                                                            address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                            self._offset = self._offset + 2
                                                                                                        else:
                                                                                                            address0 = FAILURE
                                                                                                            if self._offset > self._failure:
                                                                                                                self._failure = self._offset
                                                                                                                self._expected = []
                                                                                                            if self._offset == self._failure:
                                                                                                                self._expected.append('"Rh"')
                                                                                                        if address0 is FAILURE:
                                                                                                            self._offset = index1
                                                                                                            chunk25 = None
                                                                                                            if self._offset < self._input_size:
                                                                                                                chunk25 = self._input[self._offset:self._offset + 2]
                                                                                                            if chunk25 == 'Re':
                                                                                                                address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                self._offset = self._offset + 2
                                                                                                            else:
                                                                                                                address0 = FAILURE
                                                                                                                if self._offset > self._failure:
                                                                                                                    self._failure = self._offset
                                                                                                                    self._expected = []
                                                                                                                if self._offset == self._failure:
                                                                                                                    self._expected.append('"Re"')
                                                                                                            if address0 is FAILURE:
                                                                                                                self._offset = index1
                                                                                                                chunk26 = None
                                                                                                                if self._offset < self._input_size:
                                                                                                                    chunk26 = self._input[self._offset:self._offset + 2]
                                                                                                                if chunk26 == 'Rb':
                                                                                                                    address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                    self._offset = self._offset + 2
                                                                                                                else:
                                                                                                                    address0 = FAILURE
                                                                                                                    if self._offset > self._failure:
                                                                                                                        self._failure = self._offset
                                                                                                                        self._expected = []
                                                                                                                    if self._offset == self._failure:
                                                                                                                        self._expected.append('"Rb"')
                                                                                                                if address0 is FAILURE:
                                                                                                                    self._offset = index1
                                                                                                                    chunk27 = None
                                                                                                                    if self._offset < self._input_size:
                                                                                                                        chunk27 = self._input[self._offset:self._offset + 2]
                                                                                                                    if chunk27 == 'Pt':
                                                                                                                        address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                        self._offset = self._offset + 2
                                                                                                                    else:
                                                                                                                        address0 = FAILURE
                                                                                                                        if self._offset > self._failure:
                                                                                                                            self._failure = self._offset
                                                                                                                            self._expected = []
                                                                                                                        if self._offset == self._failure:
                                                                                                                            self._expected.append('"Pt"')
                                                                                                                    if address0 is FAILURE:
                                                                                                                        self._offset = index1
                                                                                                                        chunk28 = None
                                                                                                                        if self._offset < self._input_size:
                                                                                                                            chunk28 = self._input[self._offset:self._offset + 2]
                                                                                                                        if chunk28 == 'Pr':
                                                                                                                            address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                            self._offset = self._offset + 2
                                                                                                                        else:
                                                                                                                            address0 = FAILURE
                                                                                                                            if self._offset > self._failure:
                                                                                                                                self._failure = self._offset
                                                                                                                                self._expected = []
                                                                                                                            if self._offset == self._failure:
                                                                                                                                self._expected.append('"Pr"')
                                                                                                                        if address0 is FAILURE:
                                                                                                                            self._offset = index1
                                                                                                                            chunk29 = None
                                                                                                                            if self._offset < self._input_size:
                                                                                                                                chunk29 = self._input[self._offset:self._offset + 2]
                                                                                                                            if chunk29 == 'Pd':
                                                                                                                                address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                self._offset = self._offset + 2
                                                                                                                            else:
                                                                                                                                address0 = FAILURE
                                                                                                                                if self._offset > self._failure:
                                                                                                                                    self._failure = self._offset
                                                                                                                                    self._expected = []
                                                                                                                                if self._offset == self._failure:
                                                                                                                                    self._expected.append('"Pd"')
                                                                                                                            if address0 is FAILURE:
                                                                                                                                self._offset = index1
                                                                                                                                chunk30 = None
                                                                                                                                if self._offset < self._input_size:
                                                                                                                                    chunk30 = self._input[self._offset:self._offset + 2]
                                                                                                                                if chunk30 == 'Pb':
                                                                                                                                    address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                    self._offset = self._offset + 2
                                                                                                                                else:
                                                                                                                                    address0 = FAILURE
                                                                                                                                    if self._offset > self._failure:
                                                                                                                                        self._failure = self._offset
                                                                                                                                        self._expected = []
                                                                                                                                    if self._offset == self._failure:
                                                                                                                                        self._expected.append('"Pb"')
                                                                                                                                if address0 is FAILURE:
                                                                                                                                    self._offset = index1
                                                                                                                                    chunk31 = None
                                                                                                                                    if self._offset < self._input_size:
                                                                                                                                        chunk31 = self._input[self._offset:self._offset + 1]
                                                                                                                                    if chunk31 == 'P':
                                                                                                                                        address0 = self._actions.make_element(self._input, self._offset, self._offset + 1)
                                                                                                                                        self._offset = self._offset + 1
                                                                                                                                    else:
                                                                                                                                        address0 = FAILURE
                                                                                                                                        if self._offset > self._failure:
                                                                                                                                            self._failure = self._offset
                                                                                                                                            self._expected = []
                                                                                                                                        if self._offset == self._failure:
                                                                                                                                            self._expected.append('"P"')
                                                                                                                                    if address0 is FAILURE:
                                                                                                                                        self._offset = index1
                                                                                                                                        chunk32 = None
                                                                                                                                        if self._offset < self._input_size:
                                                                                                                                            chunk32 = self._input[self._offset:self._offset + 2]
                                                                                                                                        if chunk32 == 'Os':
                                                                                                                                            address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                            self._offset = self._offset + 2
                                                                                                                                        else:
                                                                                                                                            address0 = FAILURE
                                                                                                                                            if self._offset > self._failure:
                                                                                                                                                self._failure = self._offset
                                                                                                                                                self._expected = []
                                                                                                                                            if self._offset == self._failure:
                                                                                                                                                self._expected.append('"Os"')
                                                                                                                                        if address0 is FAILURE:
                                                                                                                                            self._offset = index1
                                                                                                                                            chunk33 = None
                                                                                                                                            if self._offset < self._input_size:
                                                                                                                                                chunk33 = self._input[self._offset:self._offset + 1]
                                                                                                                                            if chunk33 == 'O':
                                                                                                                                                address0 = self._actions.make_element(self._input, self._offset, self._offset + 1)
                                                                                                                                                self._offset = self._offset + 1
                                                                                                                                            else:
                                                                                                                                                address0 = FAILURE
                                                                                                                                                if self._offset > self._failure:
                                                                                                                                                    self._failure = self._offset
                                                                                                                                                    self._expected = []
                                                                                                                                                if self._offset == self._failure:
                                                                                                                                                    self._expected.append('"O"')
                                                                                                                                            if address0 is FAILURE:
                                                                                                                                                self._offset = index1
                                                                                                                                                chunk34 = None
                                                                                                                                                if self._offset < self._input_size:
                                                                                                                                                    chunk34 = self._input[self._offset:self._offset + 2]
                                                                                                                                                if chunk34 == 'Ni':
                                                                                                                                                    address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                    self._offset = self._offset + 2
                                                                                                                                                else:
                                                                                                                                                    address0 = FAILURE
                                                                                                                                                    if self._offset > self._failure:
                                                                                                                                                        self._failure = self._offset
                                                                                                                                                        self._expected = []
                                                                                                                                                    if self._offset == self._failure:
                                                                                                                                                        self._expected.append('"Ni"')
                                                                                                                                                if address0 is FAILURE:
                                                                                                                                                    self._offset = index1
                                                                                                                                                    chunk35 = None
                                                                                                                                                    if self._offset < self._input_size:
                                                                                                                                                        chunk35 = self._input[self._offset:self._offset + 2]
                                                                                                                                                    if chunk35 == 'Ne':
                                                                                                                                                        address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                        self._offset = self._offset + 2
                                                                                                                                                    else:
                                                                                                                                                        address0 = FAILURE
                                                                                                                                                        if self._offset > self._failure:
                                                                                                                                                            self._failure = self._offset
                                                                                                                                                            self._expected = []
                                                                                                                                                        if self._offset == self._failure:
                                                                                                                                                            self._expected.append('"Ne"')
                                                                                                                                                    if address0 is FAILURE:
                                                                                                                                                        self._offset = index1
                                                                                                                                                        chunk36 = None
                                                                                                                                                        if self._offset < self._input_size:
                                                                                                                                                            chunk36 = self._input[self._offset:self._offset + 2]
                                                                                                                                                        if chunk36 == 'Nd':
                                                                                                                                                            address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                            self._offset = self._offset + 2
                                                                                                                                                        else:
                                                                                                                                                            address0 = FAILURE
                                                                                                                                                            if self._offset > self._failure:
                                                                                                                                                                self._failure = self._offset
                                                                                                                                                                self._expected = []
                                                                                                                                                            if self._offset == self._failure:
                                                                                                                                                                self._expected.append('"Nd"')
                                                                                                                                                        if address0 is FAILURE:
                                                                                                                                                            self._offset = index1
                                                                                                                                                            chunk37 = None
                                                                                                                                                            if self._offset < self._input_size:
                                                                                                                                                                chunk37 = self._input[self._offset:self._offset + 2]
                                                                                                                                                            if chunk37 == 'Nb':
                                                                                                                                                                address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                                self._offset = self._offset + 2
                                                                                                                                                            else:
                                                                                                                                                                address0 = FAILURE
                                                                                                                                                                if self._offset > self._failure:
                                                                                                                                                                    self._failure = self._offset
                                                                                                                                                                    self._expected = []
                                                                                                                                                                if self._offset == self._failure:
                                                                                                                                                                    self._expected.append('"Nb"')
                                                                                                                                                            if address0 is FAILURE:
                                                                                                                                                                self._offset = index1
                                                                                                                                                                chunk38 = None
                                                                                                                                                                if self._offset < self._input_size:
                                                                                                                                                                    chunk38 = self._input[self._offset:self._offset + 2]
                                                                                                                                                                if chunk38 == 'Na':
                                                                                                                                                                    address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                                    self._offset = self._offset + 2
                                                                                                                                                                else:
                                                                                                                                                                    address0 = FAILURE
                                                                                                                                                                    if self._offset > self._failure:
                                                                                                                                                                        self._failure = self._offset
                                                                                                                                                                        self._expected = []
                                                                                                                                                                    if self._offset == self._failure:
                                                                                                                                                                        self._expected.append('"Na"')
                                                                                                                                                                if address0 is FAILURE:
                                                                                                                                                                    self._offset = index1
                                                                                                                                                                    chunk39 = None
                                                                                                                                                                    if self._offset < self._input_size:
                                                                                                                                                                        chunk39 = self._input[self._offset:self._offset + 1]
                                                                                                                                                                    if chunk39 == 'N':
                                                                                                                                                                        address0 = self._actions.make_element(self._input, self._offset, self._offset + 1)
                                                                                                                                                                        self._offset = self._offset + 1
                                                                                                                                                                    else:
                                                                                                                                                                        address0 = FAILURE
                                                                                                                                                                        if self._offset > self._failure:
                                                                                                                                                                            self._failure = self._offset
                                                                                                                                                                            self._expected = []
                                                                                                                                                                        if self._offset == self._failure:
                                                                                                                                                                            self._expected.append('"N"')
                                                                                                                                                                    if address0 is FAILURE:
                                                                                                                                                                        self._offset = index1
                                                                                                                                                                        chunk40 = None
                                                                                                                                                                        if self._offset < self._input_size:
                                                                                                                                                                            chunk40 = self._input[self._offset:self._offset + 2]
                                                                                                                                                                        if chunk40 == 'Mo':
                                                                                                                                                                            address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                                            self._offset = self._offset + 2
                                                                                                                                                                        else:
                                                                                                                                                                            address0 = FAILURE
                                                                                                                                                                            if self._offset > self._failure:
                                                                                                                                                                                self._failure = self._offset
                                                                                                                                                                                self._expected = []
                                                                                                                                                                            if self._offset == self._failure:
                                                                                                                                                                                self._expected.append('"Mo"')
                                                                                                                                                                        if address0 is FAILURE:
                                                                                                                                                                            self._offset = index1
                                                                                                                                                                            chunk41 = None
                                                                                                                                                                            if self._offset < self._input_size:
                                                                                                                                                                                chunk41 = self._input[self._offset:self._offset + 2]
                                                                                                                                                                            if chunk41 == 'Mn':
                                                                                                                                                                                address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                                                self._offset = self._offset + 2
                                                                                                                                                                            else:
                                                                                                                                                                                address0 = FAILURE
                                                                                                                                                                                if self._offset > self._failure:
                                                                                                                                                                                    self._failure = self._offset
                                                                                                                                                                                    self._expected = []
                                                                                                                                                                                if self._offset == self._failure:
                                                                                                                                                                                    self._expected.append('"Mn"')
                                                                                                                                                                            if address0 is FAILURE:
                                                                                                                                                                                self._offset = index1
                                                                                                                                                                                chunk42 = None
                                                                                                                                                                                if self._offset < self._input_size:
                                                                                                                                                                                    chunk42 = self._input[self._offset:self._offset + 2]
                                                                                                                                                                                if chunk42 == 'Mg':
                                                                                                                                                                                    address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                                                    self._offset = self._offset + 2
                                                                                                                                                                                else:
                                                                                                                                                                                    address0 = FAILURE
                                                                                                                                                                                    if self._offset > self._failure:
                                                                                                                                                                                        self._failure = self._offset
                                                                                                                                                                                        self._expected = []
                                                                                                                                                                                    if self._offset == self._failure:
                                                                                                                                                                                        self._expected.append('"Mg"')
                                                                                                                                                                                if address0 is FAILURE:
                                                                                                                                                                                    self._offset = index1
                                                                                                                                                                                    chunk43 = None
                                                                                                                                                                                    if self._offset < self._input_size:
                                                                                                                                                                                        chunk43 = self._input[self._offset:self._offset + 2]
                                                                                                                                                                                    if chunk43 == 'Lu':
                                                                                                                                                                                        address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                                                        self._offset = self._offset + 2
                                                                                                                                                                                    else:
                                                                                                                                                                                        address0 = FAILURE
                                                                                                                                                                                        if self._offset > self._failure:
                                                                                                                                                                                            self._failure = self._offset
                                                                                                                                                                                            self._expected = []
                                                                                                                                                                                        if self._offset == self._failure:
                                                                                                                                                                                            self._expected.append('"Lu"')
                                                                                                                                                                                    if address0 is FAILURE:
                                                                                                                                                                                        self._offset = index1
                                                                                                                                                                                        chunk44 = None
                                                                                                                                                                                        if self._offset < self._input_size:
                                                                                                                                                                                            chunk44 = self._input[self._offset:self._offset + 2]
                                                                                                                                                                                        if chunk44 == 'Li':
                                                                                                                                                                                            address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                                                            self._offset = self._offset + 2
                                                                                                                                                                                        else:
                                                                                                                                                                                            address0 = FAILURE
                                                                                                                                                                                            if self._offset > self._failure:
                                                                                                                                                                                                self._failure = self._offset
                                                                                                                                                                                                self._expected = []
                                                                                                                                                                                            if self._offset == self._failure:
                                                                                                                                                                                                self._expected.append('"Li"')
                                                                                                                                                                                        if address0 is FAILURE:
                                                                                                                                                                                            self._offset = index1
                                                                                                                                                                                            chunk45 = None
                                                                                                                                                                                            if self._offset < self._input_size:
                                                                                                                                                                                                chunk45 = self._input[self._offset:self._offset + 2]
                                                                                                                                                                                            if chunk45 == 'La':
                                                                                                                                                                                                address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                                                                self._offset = self._offset + 2
                                                                                                                                                                                            else:
                                                                                                                                                                                                address0 = FAILURE
                                                                                                                                                                                                if self._offset > self._failure:
                                                                                                                                                                                                    self._failure = self._offset
                                                                                                                                                                                                    self._expected = []
                                                                                                                                                                                                if self._offset == self._failure:
                                                                                                                                                                                                    self._expected.append('"La"')
                                                                                                                                                                                            if address0 is FAILURE:
                                                                                                                                                                                                self._offset = index1
                                                                                                                                                                                                chunk46 = None
                                                                                                                                                                                                if self._offset < self._input_size:
                                                                                                                                                                                                    chunk46 = self._input[self._offset:self._offset + 2]
                                                                                                                                                                                                if chunk46 == 'Kr':
                                                                                                                                                                                                    address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                                                                    self._offset = self._offset + 2
                                                                                                                                                                                                else:
                                                                                                                                                                                                    address0 = FAILURE
                                                                                                                                                                                                    if self._offset > self._failure:
                                                                                                                                                                                                        self._failure = self._offset
                                                                                                                                                                                                        self._expected = []
                                                                                                                                                                                                    if self._offset == self._failure:
                                                                                                                                                                                                        self._expected.append('"Kr"')
                                                                                                                                                                                                if address0 is FAILURE:
                                                                                                                                                                                                    self._offset = index1
                                                                                                                                                                                                    chunk47 = None
                                                                                                                                                                                                    if self._offset < self._input_size:
                                                                                                                                                                                                        chunk47 = self._input[self._offset:self._offset + 1]
                                                                                                                                                                                                    if chunk47 == 'K':
                                                                                                                                                                                                        address0 = self._actions.make_element(self._input, self._offset, self._offset + 1)
                                                                                                                                                                                                        self._offset = self._offset + 1
                                                                                                                                                                                                    else:
                                                                                                                                                                                                        address0 = FAILURE
                                                                                                                                                                                                        if self._offset > self._failure:
                                                                                                                                                                                                            self._failure = self._offset
                                                                                                                                                                                                            self._expected = []
                                                                                                                                                                                                        if self._offset == self._failure:
                                                                                                                                                                                                            self._expected.append('"K"')
                                                                                                                                                                                                    if address0 is FAILURE:
                                                                                                                                                                                                        self._offset = index1
                                                                                                                                                                                                        chunk48 = None
                                                                                                                                                                                                        if self._offset < self._input_size:
                                                                                                                                                                                                            chunk48 = self._input[self._offset:self._offset + 2]
                                                                                                                                                                                                        if chunk48 == 'Ir':
                                                                                                                                                                                                            address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                                                                            self._offset = self._offset + 2
                                                                                                                                                                                                        else:
                                                                                                                                                                                                            address0 = FAILURE
                                                                                                                                                                                                            if self._offset > self._failure:
                                                                                                                                                                                                                self._failure = self._offset
                                                                                                                                                                                                                self._expected = []
                                                                                                                                                                                                            if self._offset == self._failure:
                                                                                                                                                                                                                self._expected.append('"Ir"')
                                                                                                                                                                                                        if address0 is FAILURE:
                                                                                                                                                                                                            self._offset = index1
                                                                                                                                                                                                            chunk49 = None
                                                                                                                                                                                                            if self._offset < self._input_size:
                                                                                                                                                                                                                chunk49 = self._input[self._offset:self._offset + 2]
                                                                                                                                                                                                            if chunk49 == 'In':
                                                                                                                                                                                                                address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                                                                                self._offset = self._offset + 2
                                                                                                                                                                                                            else:
                                                                                                                                                                                                                address0 = FAILURE
                                                                                                                                                                                                                if self._offset > self._failure:
                                                                                                                                                                                                                    self._failure = self._offset
                                                                                                                                                                                                                    self._expected = []
                                                                                                                                                                                                                if self._offset == self._failure:
                                                                                                                                                                                                                    self._expected.append('"In"')
                                                                                                                                                                                                            if address0 is FAILURE:
                                                                                                                                                                                                                self._offset = index1
                                                                                                                                                                                                                chunk50 = None
                                                                                                                                                                                                                if self._offset < self._input_size:
                                                                                                                                                                                                                    chunk50 = self._input[self._offset:self._offset + 1]
                                                                                                                                                                                                                if chunk50 == 'I':
                                                                                                                                                                                                                    address0 = self._actions.make_element(self._input, self._offset, self._offset + 1)
                                                                                                                                                                                                                    self._offset = self._offset + 1
                                                                                                                                                                                                                else:
                                                                                                                                                                                                                    address0 = FAILURE
                                                                                                                                                                                                                    if self._offset > self._failure:
                                                                                                                                                                                                                        self._failure = self._offset
                                                                                                                                                                                                                        self._expected = []
                                                                                                                                                                                                                    if self._offset == self._failure:
                                                                                                                                                                                                                        self._expected.append('"I"')
                                                                                                                                                                                                                if address0 is FAILURE:
                                                                                                                                                                                                                    self._offset = index1
                                                                                                                                                                                                                    chunk51 = None
                                                                                                                                                                                                                    if self._offset < self._input_size:
                                                                                                                                                                                                                        chunk51 = self._input[self._offset:self._offset + 2]
                                                                                                                                                                                                                    if chunk51 == 'Ho':
                                                                                                                                                                                                                        address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                                                                                        self._offset = self._offset + 2
                                                                                                                                                                                                                    else:
                                                                                                                                                                                                                        address0 = FAILURE
                                                                                                                                                                                                                        if self._offset > self._failure:
                                                                                                                                                                                                                            self._failure = self._offset
                                                                                                                                                                                                                            self._expected = []
                                                                                                                                                                                                                        if self._offset == self._failure:
                                                                                                                                                                                                                            self._expected.append('"Ho"')
                                                                                                                                                                                                                    if address0 is FAILURE:
                                                                                                                                                                                                                        self._offset = index1
                                                                                                                                                                                                                        chunk52 = None
                                                                                                                                                                                                                        if self._offset < self._input_size:
                                                                                                                                                                                                                            chunk52 = self._input[self._offset:self._offset + 2]
                                                                                                                                                                                                                        if chunk52 == 'Hg':
                                                                                                                                                                                                                            address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                                                                                            self._offset = self._offset + 2
                                                                                                                                                                                                                        else:
                                                                                                                                                                                                                            address0 = FAILURE
                                                                                                                                                                                                                            if self._offset > self._failure:
                                                                                                                                                                                                                                self._failure = self._offset
                                                                                                                                                                                                                                self._expected = []
                                                                                                                                                                                                                            if self._offset == self._failure:
                                                                                                                                                                                                                                self._expected.append('"Hg"')
                                                                                                                                                                                                                        if address0 is FAILURE:
                                                                                                                                                                                                                            self._offset = index1
                                                                                                                                                                                                                            chunk53 = None
                                                                                                                                                                                                                            if self._offset < self._input_size:
                                                                                                                                                                                                                                chunk53 = self._input[self._offset:self._offset + 2]
                                                                                                                                                                                                                            if chunk53 == 'Hf':
                                                                                                                                                                                                                                address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                                                                                                self._offset = self._offset + 2
                                                                                                                                                                                                                            else:
                                                                                                                                                                                                                                address0 = FAILURE
                                                                                                                                                                                                                                if self._offset > self._failure:
                                                                                                                                                                                                                                    self._failure = self._offset
                                                                                                                                                                                                                                    self._expected = []
                                                                                                                                                                                                                                if self._offset == self._failure:
                                                                                                                                                                                                                                    self._expected.append('"Hf"')
                                                                                                                                                                                                                            if address0 is FAILURE:
                                                                                                                                                                                                                                self._offset = index1
                                                                                                                                                                                                                                chunk54 = None
                                                                                                                                                                                                                                if self._offset < self._input_size:
                                                                                                                                                                                                                                    chunk54 = self._input[self._offset:self._offset + 2]
                                                                                                                                                                                                                                if chunk54 == 'He':
                                                                                                                                                                                                                                    address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                                                                                                    self._offset = self._offset + 2
                                                                                                                                                                                                                                else:
                                                                                                                                                                                                                                    address0 = FAILURE
                                                                                                                                                                                                                                    if self._offset > self._failure:
                                                                                                                                                                                                                                        self._failure = self._offset
                                                                                                                                                                                                                                        self._expected = []
                                                                                                                                                                                                                                    if self._offset == self._failure:
                                                                                                                                                                                                                                        self._expected.append('"He"')
                                                                                                                                                                                                                                if address0 is FAILURE:
                                                                                                                                                                                                                                    self._offset = index1
                                                                                                                                                                                                                                    chunk55 = None
                                                                                                                                                                                                                                    if self._offset < self._input_size:
                                                                                                                                                                                                                                        chunk55 = self._input[self._offset:self._offset + 1]
                                                                                                                                                                                                                                    if chunk55 == 'H':
                                                                                                                                                                                                                                        address0 = self._actions.make_element(self._input, self._offset, self._offset + 1)
                                                                                                                                                                                                                                        self._offset = self._offset + 1
                                                                                                                                                                                                                                    else:
                                                                                                                                                                                                                                        address0 = FAILURE
                                                                                                                                                                                                                                        if self._offset > self._failure:
                                                                                                                                                                                                                                            self._failure = self._offset
                                                                                                                                                                                                                                            self._expected = []
                                                                                                                                                                                                                                        if self._offset == self._failure:
                                                                                                                                                                                                                                            self._expected.append('"H"')
                                                                                                                                                                                                                                    if address0 is FAILURE:
                                                                                                                                                                                                                                        self._offset = index1
                                                                                                                                                                                                                                        chunk56 = None
                                                                                                                                                                                                                                        if self._offset < self._input_size:
                                                                                                                                                                                                                                            chunk56 = self._input[self._offset:self._offset + 2]
                                                                                                                                                                                                                                        if chunk56 == 'Ge':
                                                                                                                                                                                                                                            address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                                                                                                            self._offset = self._offset + 2
                                                                                                                                                                                                                                        else:
                                                                                                                                                                                                                                            address0 = FAILURE
                                                                                                                                                                                                                                            if self._offset > self._failure:
                                                                                                                                                                                                                                                self._failure = self._offset
                                                                                                                                                                                                                                                self._expected = []
                                                                                                                                                                                                                                            if self._offset == self._failure:
                                                                                                                                                                                                                                                self._expected.append('"Ge"')
                                                                                                                                                                                                                                        if address0 is FAILURE:
                                                                                                                                                                                                                                            self._offset = index1
                                                                                                                                                                                                                                            chunk57 = None
                                                                                                                                                                                                                                            if self._offset < self._input_size:
                                                                                                                                                                                                                                                chunk57 = self._input[self._offset:self._offset + 2]
                                                                                                                                                                                                                                            if chunk57 == 'Gd':
                                                                                                                                                                                                                                                address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                                                                                                                self._offset = self._offset + 2
                                                                                                                                                                                                                                            else:
                                                                                                                                                                                                                                                address0 = FAILURE
                                                                                                                                                                                                                                                if self._offset > self._failure:
                                                                                                                                                                                                                                                    self._failure = self._offset
                                                                                                                                                                                                                                                    self._expected = []
                                                                                                                                                                                                                                                if self._offset == self._failure:
                                                                                                                                                                                                                                                    self._expected.append('"Gd"')
                                                                                                                                                                                                                                            if address0 is FAILURE:
                                                                                                                                                                                                                                                self._offset = index1
                                                                                                                                                                                                                                                chunk58 = None
                                                                                                                                                                                                                                                if self._offset < self._input_size:
                                                                                                                                                                                                                                                    chunk58 = self._input[self._offset:self._offset + 2]
                                                                                                                                                                                                                                                if chunk58 == 'Ga':
                                                                                                                                                                                                                                                    address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                                                                                                                    self._offset = self._offset + 2
                                                                                                                                                                                                                                                else:
                                                                                                                                                                                                                                                    address0 = FAILURE
                                                                                                                                                                                                                                                    if self._offset > self._failure:
                                                                                                                                                                                                                                                        self._failure = self._offset
                                                                                                                                                                                                                                                        self._expected = []
                                                                                                                                                                                                                                                    if self._offset == self._failure:
                                                                                                                                                                                                                                                        self._expected.append('"Ga"')
                                                                                                                                                                                                                                                if address0 is FAILURE:
                                                                                                                                                                                                                                                    self._offset = index1
                                                                                                                                                                                                                                                    chunk59 = None
                                                                                                                                                                                                                                                    if self._offset < self._input_size:
                                                                                                                                                                                                                                                        chunk59 = self._input[self._offset:self._offset + 2]
                                                                                                                                                                                                                                                    if chunk59 == 'Fe':
                                                                                                                                                                                                                                                        address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                                                                                                                        self._offset = self._offset + 2
                                                                                                                                                                                                                                                    else:
                                                                                                                                                                                                                                                        address0 = FAILURE
                                                                                                                                                                                                                                                        if self._offset > self._failure:
                                                                                                                                                                                                                                                            self._failure = self._offset
                                                                                                                                                                                                                                                            self._expected = []
                                                                                                                                                                                                                                                        if self._offset == self._failure:
                                                                                                                                                                                                                                                            self._expected.append('"Fe"')
                                                                                                                                                                                                                                                    if address0 is FAILURE:
                                                                                                                                                                                                                                                        self._offset = index1
                                                                                                                                                                                                                                                        chunk60 = None
                                                                                                                                                                                                                                                        if self._offset < self._input_size:
                                                                                                                                                                                                                                                            chunk60 = self._input[self._offset:self._offset + 1]
                                                                                                                                                                                                                                                        if chunk60 == 'F':
                                                                                                                                                                                                                                                            address0 = self._actions.make_element(self._input, self._offset, self._offset + 1)
                                                                                                                                                                                                                                                            self._offset = self._offset + 1
                                                                                                                                                                                                                                                        else:
                                                                                                                                                                                                                                                            address0 = FAILURE
                                                                                                                                                                                                                                                            if self._offset > self._failure:
                                                                                                                                                                                                                                                                self._failure = self._offset
                                                                                                                                                                                                                                                                self._expected = []
                                                                                                                                                                                                                                                            if self._offset == self._failure:
                                                                                                                                                                                                                                                                self._expected.append('"F"')
                                                                                                                                                                                                                                                        if address0 is FAILURE:
                                                                                                                                                                                                                                                            self._offset = index1
                                                                                                                                                                                                                                                            chunk61 = None
                                                                                                                                                                                                                                                            if self._offset < self._input_size:
                                                                                                                                                                                                                                                                chunk61 = self._input[self._offset:self._offset + 2]
                                                                                                                                                                                                                                                            if chunk61 == 'Eu':
                                                                                                                                                                                                                                                                address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                                                                                                                                self._offset = self._offset + 2
                                                                                                                                                                                                                                                            else:
                                                                                                                                                                                                                                                                address0 = FAILURE
                                                                                                                                                                                                                                                                if self._offset > self._failure:
                                                                                                                                                                                                                                                                    self._failure = self._offset
                                                                                                                                                                                                                                                                    self._expected = []
                                                                                                                                                                                                                                                                if self._offset == self._failure:
                                                                                                                                                                                                                                                                    self._expected.append('"Eu"')
                                                                                                                                                                                                                                                            if address0 is FAILURE:
                                                                                                                                                                                                                                                                self._offset = index1
                                                                                                                                                                                                                                                                chunk62 = None
                                                                                                                                                                                                                                                                if self._offset < self._input_size:
                                                                                                                                                                                                                                                                    chunk62 = self._input[self._offset:self._offset + 2]
                                                                                                                                                                                                                                                                if chunk62 == 'Er':
                                                                                                                                                                                                                                                                    address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                                                                                                                                    self._offset = self._offset + 2
                                                                                                                                                                                                                                                                else:
                                                                                                                                                                                                                                                                    address0 = FAILURE
                                                                                                                                                                                                                                                                    if self._offset > self._failure:
                                                                                                                                                                                                                                                                        self._failure = self._offset
                                                                                                                                                                                                                                                                        self._expected = []
                                                                                                                                                                                                                                                                    if self._offset == self._failure:
                                                                                                                                                                                                                                                                        self._expected.append('"Er"')
                                                                                                                                                                                                                                                                if address0 is FAILURE:
                                                                                                                                                                                                                                                                    self._offset = index1
                                                                                                                                                                                                                                                                    chunk63 = None
                                                                                                                                                                                                                                                                    if self._offset < self._input_size:
                                                                                                                                                                                                                                                                        chunk63 = self._input[self._offset:self._offset + 2]
                                                                                                                                                                                                                                                                    if chunk63 == 'Dy':
                                                                                                                                                                                                                                                                        address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                                                                                                                                        self._offset = self._offset + 2
                                                                                                                                                                                                                                                                    else:
                                                                                                                                                                                                                                                                        address0 = FAILURE
                                                                                                                                                                                                                                                                        if self._offset > self._failure:
                                                                                                                                                                                                                                                                            self._failure = self._offset
                                                                                                                                                                                                                                                                            self._expected = []
                                                                                                                                                                                                                                                                        if self._offset == self._failure:
                                                                                                                                                                                                                                                                            self._expected.append('"Dy"')
                                                                                                                                                                                                                                                                    if address0 is FAILURE:
                                                                                                                                                                                                                                                                        self._offset = index1
                                                                                                                                                                                                                                                                        chunk64 = None
                                                                                                                                                                                                                                                                        if self._offset < self._input_size:
                                                                                                                                                                                                                                                                            chunk64 = self._input[self._offset:self._offset + 1]
                                                                                                                                                                                                                                                                        if chunk64 == 'D':
                                                                                                                                                                                                                                                                            address0 = self._actions.make_element(self._input, self._offset, self._offset + 1)
                                                                                                                                                                                                                                                                            self._offset = self._offset + 1
                                                                                                                                                                                                                                                                        else:
                                                                                                                                                                                                                                                                            address0 = FAILURE
                                                                                                                                                                                                                                                                            if self._offset > self._failure:
                                                                                                                                                                                                                                                                                self._failure = self._offset
                                                                                                                                                                                                                                                                                self._expected = []
                                                                                                                                                                                                                                                                            if self._offset == self._failure:
                                                                                                                                                                                                                                                                                self._expected.append('"D"')
                                                                                                                                                                                                                                                                        if address0 is FAILURE:
                                                                                                                                                                                                                                                                            self._offset = index1
                                                                                                                                                                                                                                                                            chunk65 = None
                                                                                                                                                                                                                                                                            if self._offset < self._input_size:
                                                                                                                                                                                                                                                                                chunk65 = self._input[self._offset:self._offset + 2]
                                                                                                                                                                                                                                                                            if chunk65 == 'Cu':
                                                                                                                                                                                                                                                                                address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                                                                                                                                                self._offset = self._offset + 2
                                                                                                                                                                                                                                                                            else:
                                                                                                                                                                                                                                                                                address0 = FAILURE
                                                                                                                                                                                                                                                                                if self._offset > self._failure:
                                                                                                                                                                                                                                                                                    self._failure = self._offset
                                                                                                                                                                                                                                                                                    self._expected = []
                                                                                                                                                                                                                                                                                if self._offset == self._failure:
                                                                                                                                                                                                                                                                                    self._expected.append('"Cu"')
                                                                                                                                                                                                                                                                            if address0 is FAILURE:
                                                                                                                                                                                                                                                                                self._offset = index1
                                                                                                                                                                                                                                                                                chunk66 = None
                                                                                                                                                                                                                                                                                if self._offset < self._input_size:
                                                                                                                                                                                                                                                                                    chunk66 = self._input[self._offset:self._offset + 2]
                                                                                                                                                                                                                                                                                if chunk66 == 'Cs':
                                                                                                                                                                                                                                                                                    address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                                                                                                                                                    self._offset = self._offset + 2
                                                                                                                                                                                                                                                                                else:
                                                                                                                                                                                                                                                                                    address0 = FAILURE
                                                                                                                                                                                                                                                                                    if self._offset > self._failure:
                                                                                                                                                                                                                                                                                        self._failure = self._offset
                                                                                                                                                                                                                                                                                        self._expected = []
                                                                                                                                                                                                                                                                                    if self._offset == self._failure:
                                                                                                                                                                                                                                                                                        self._expected.append('"Cs"')
                                                                                                                                                                                                                                                                                if address0 is FAILURE:
                                                                                                                                                                                                                                                                                    self._offset = index1
                                                                                                                                                                                                                                                                                    chunk67 = None
                                                                                                                                                                                                                                                                                    if self._offset < self._input_size:
                                                                                                                                                                                                                                                                                        chunk67 = self._input[self._offset:self._offset + 2]
                                                                                                                                                                                                                                                                                    if chunk67 == 'Cr':
                                                                                                                                                                                                                                                                                        address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                                                                                                                                                        self._offset = self._offset + 2
                                                                                                                                                                                                                                                                                    else:
                                                                                                                                                                                                                                                                                        address0 = FAILURE
                                                                                                                                                                                                                                                                                        if self._offset > self._failure:
                                                                                                                                                                                                                                                                                            self._failure = self._offset
                                                                                                                                                                                                                                                                                            self._expected = []
                                                                                                                                                                                                                                                                                        if self._offset == self._failure:
                                                                                                                                                                                                                                                                                            self._expected.append('"Cr"')
                                                                                                                                                                                                                                                                                    if address0 is FAILURE:
                                                                                                                                                                                                                                                                                        self._offset = index1
                                                                                                                                                                                                                                                                                        chunk68 = None
                                                                                                                                                                                                                                                                                        if self._offset < self._input_size:
                                                                                                                                                                                                                                                                                            chunk68 = self._input[self._offset:self._offset + 2]
                                                                                                                                                                                                                                                                                        if chunk68 == 'Co':
                                                                                                                                                                                                                                                                                            address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                                                                                                                                                            self._offset = self._offset + 2
                                                                                                                                                                                                                                                                                        else:
                                                                                                                                                                                                                                                                                            address0 = FAILURE
                                                                                                                                                                                                                                                                                            if self._offset > self._failure:
                                                                                                                                                                                                                                                                                                self._failure = self._offset
                                                                                                                                                                                                                                                                                                self._expected = []
                                                                                                                                                                                                                                                                                            if self._offset == self._failure:
                                                                                                                                                                                                                                                                                                self._expected.append('"Co"')
                                                                                                                                                                                                                                                                                        if address0 is FAILURE:
                                                                                                                                                                                                                                                                                            self._offset = index1
                                                                                                                                                                                                                                                                                            chunk69 = None
                                                                                                                                                                                                                                                                                            if self._offset < self._input_size:
                                                                                                                                                                                                                                                                                                chunk69 = self._input[self._offset:self._offset + 2]
                                                                                                                                                                                                                                                                                            if chunk69 == 'Cl':
                                                                                                                                                                                                                                                                                                address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                                                                                                                                                                self._offset = self._offset + 2
                                                                                                                                                                                                                                                                                            else:
                                                                                                                                                                                                                                                                                                address0 = FAILURE
                                                                                                                                                                                                                                                                                                if self._offset > self._failure:
                                                                                                                                                                                                                                                                                                    self._failure = self._offset
                                                                                                                                                                                                                                                                                                    self._expected = []
                                                                                                                                                                                                                                                                                                if self._offset == self._failure:
                                                                                                                                                                                                                                                                                                    self._expected.append('"Cl"')
                                                                                                                                                                                                                                                                                            if address0 is FAILURE:
                                                                                                                                                                                                                                                                                                self._offset = index1
                                                                                                                                                                                                                                                                                                chunk70 = None
                                                                                                                                                                                                                                                                                                if self._offset < self._input_size:
                                                                                                                                                                                                                                                                                                    chunk70 = self._input[self._offset:self._offset + 2]
                                                                                                                                                                                                                                                                                                if chunk70 == 'Ce':
                                                                                                                                                                                                                                                                                                    address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                                                                                                                                                                    self._offset = self._offset + 2
                                                                                                                                                                                                                                                                                                else:
                                                                                                                                                                                                                                                                                                    address0 = FAILURE
                                                                                                                                                                                                                                                                                                    if self._offset > self._failure:
                                                                                                                                                                                                                                                                                                        self._failure = self._offset
                                                                                                                                                                                                                                                                                                        self._expected = []
                                                                                                                                                                                                                                                                                                    if self._offset == self._failure:
                                                                                                                                                                                                                                                                                                        self._expected.append('"Ce"')
                                                                                                                                                                                                                                                                                                if address0 is FAILURE:
                                                                                                                                                                                                                                                                                                    self._offset = index1
                                                                                                                                                                                                                                                                                                    chunk71 = None
                                                                                                                                                                                                                                                                                                    if self._offset < self._input_size:
                                                                                                                                                                                                                                                                                                        chunk71 = self._input[self._offset:self._offset + 2]
                                                                                                                                                                                                                                                                                                    if chunk71 == 'Cd':
                                                                                                                                                                                                                                                                                                        address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                                                                                                                                                                        self._offset = self._offset + 2
                                                                                                                                                                                                                                                                                                    else:
                                                                                                                                                                                                                                                                                                        address0 = FAILURE
                                                                                                                                                                                                                                                                                                        if self._offset > self._failure:
                                                                                                                                                                                                                                                                                                            self._failure = self._offset
                                                                                                                                                                                                                                                                                                            self._expected = []
                                                                                                                                                                                                                                                                                                        if self._offset == self._failure:
                                                                                                                                                                                                                                                                                                            self._expected.append('"Cd"')
                                                                                                                                                                                                                                                                                                    if address0 is FAILURE:
                                                                                                                                                                                                                                                                                                        self._offset = index1
                                                                                                                                                                                                                                                                                                        chunk72 = None
                                                                                                                                                                                                                                                                                                        if self._offset < self._input_size:
                                                                                                                                                                                                                                                                                                            chunk72 = self._input[self._offset:self._offset + 2]
                                                                                                                                                                                                                                                                                                        if chunk72 == 'Ca':
                                                                                                                                                                                                                                                                                                            address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                                                                                                                                                                            self._offset = self._offset + 2
                                                                                                                                                                                                                                                                                                        else:
                                                                                                                                                                                                                                                                                                            address0 = FAILURE
                                                                                                                                                                                                                                                                                                            if self._offset > self._failure:
                                                                                                                                                                                                                                                                                                                self._failure = self._offset
                                                                                                                                                                                                                                                                                                                self._expected = []
                                                                                                                                                                                                                                                                                                            if self._offset == self._failure:
                                                                                                                                                                                                                                                                                                                self._expected.append('"Ca"')
                                                                                                                                                                                                                                                                                                        if address0 is FAILURE:
                                                                                                                                                                                                                                                                                                            self._offset = index1
                                                                                                                                                                                                                                                                                                            chunk73 = None
                                                                                                                                                                                                                                                                                                            if self._offset < self._input_size:
                                                                                                                                                                                                                                                                                                                chunk73 = self._input[self._offset:self._offset + 1]
                                                                                                                                                                                                                                                                                                            if chunk73 == 'C':
                                                                                                                                                                                                                                                                                                                address0 = self._actions.make_element(self._input, self._offset, self._offset + 1)
                                                                                                                                                                                                                                                                                                                self._offset = self._offset + 1
                                                                                                                                                                                                                                                                                                            else:
                                                                                                                                                                                                                                                                                                                address0 = FAILURE
                                                                                                                                                                                                                                                                                                                if self._offset > self._failure:
                                                                                                                                                                                                                                                                                                                    self._failure = self._offset
                                                                                                                                                                                                                                                                                                                    self._expected = []
                                                                                                                                                                                                                                                                                                                if self._offset == self._failure:
                                                                                                                                                                                                                                                                                                                    self._expected.append('"C"')
                                                                                                                                                                                                                                                                                                            if address0 is FAILURE:
                                                                                                                                                                                                                                                                                                                self._offset = index1
                                                                                                                                                                                                                                                                                                                chunk74 = None
                                                                                                                                                                                                                                                                                                                if self._offset < self._input_size:
                                                                                                                                                                                                                                                                                                                    chunk74 = self._input[self._offset:self._offset + 2]
                                                                                                                                                                                                                                                                                                                if chunk74 == 'Br':
                                                                                                                                                                                                                                                                                                                    address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                                                                                                                                                                                    self._offset = self._offset + 2
                                                                                                                                                                                                                                                                                                                else:
                                                                                                                                                                                                                                                                                                                    address0 = FAILURE
                                                                                                                                                                                                                                                                                                                    if self._offset > self._failure:
                                                                                                                                                                                                                                                                                                                        self._failure = self._offset
                                                                                                                                                                                                                                                                                                                        self._expected = []
                                                                                                                                                                                                                                                                                                                    if self._offset == self._failure:
                                                                                                                                                                                                                                                                                                                        self._expected.append('"Br"')
                                                                                                                                                                                                                                                                                                                if address0 is FAILURE:
                                                                                                                                                                                                                                                                                                                    self._offset = index1
                                                                                                                                                                                                                                                                                                                    chunk75 = None
                                                                                                                                                                                                                                                                                                                    if self._offset < self._input_size:
                                                                                                                                                                                                                                                                                                                        chunk75 = self._input[self._offset:self._offset + 2]
                                                                                                                                                                                                                                                                                                                    if chunk75 == 'Bi':
                                                                                                                                                                                                                                                                                                                        address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                                                                                                                                                                                        self._offset = self._offset + 2
                                                                                                                                                                                                                                                                                                                    else:
                                                                                                                                                                                                                                                                                                                        address0 = FAILURE
                                                                                                                                                                                                                                                                                                                        if self._offset > self._failure:
                                                                                                                                                                                                                                                                                                                            self._failure = self._offset
                                                                                                                                                                                                                                                                                                                            self._expected = []
                                                                                                                                                                                                                                                                                                                        if self._offset == self._failure:
                                                                                                                                                                                                                                                                                                                            self._expected.append('"Bi"')
                                                                                                                                                                                                                                                                                                                    if address0 is FAILURE:
                                                                                                                                                                                                                                                                                                                        self._offset = index1
                                                                                                                                                                                                                                                                                                                        chunk76 = None
                                                                                                                                                                                                                                                                                                                        if self._offset < self._input_size:
                                                                                                                                                                                                                                                                                                                            chunk76 = self._input[self._offset:self._offset + 2]
                                                                                                                                                                                                                                                                                                                        if chunk76 == 'Be':
                                                                                                                                                                                                                                                                                                                            address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                                                                                                                                                                                            self._offset = self._offset + 2
                                                                                                                                                                                                                                                                                                                        else:
                                                                                                                                                                                                                                                                                                                            address0 = FAILURE
                                                                                                                                                                                                                                                                                                                            if self._offset > self._failure:
                                                                                                                                                                                                                                                                                                                                self._failure = self._offset
                                                                                                                                                                                                                                                                                                                                self._expected = []
                                                                                                                                                                                                                                                                                                                            if self._offset == self._failure:
                                                                                                                                                                                                                                                                                                                                self._expected.append('"Be"')
                                                                                                                                                                                                                                                                                                                        if address0 is FAILURE:
                                                                                                                                                                                                                                                                                                                            self._offset = index1
                                                                                                                                                                                                                                                                                                                            chunk77 = None
                                                                                                                                                                                                                                                                                                                            if self._offset < self._input_size:
                                                                                                                                                                                                                                                                                                                                chunk77 = self._input[self._offset:self._offset + 2]
                                                                                                                                                                                                                                                                                                                            if chunk77 == 'Ba':
                                                                                                                                                                                                                                                                                                                                address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                                                                                                                                                                                                self._offset = self._offset + 2
                                                                                                                                                                                                                                                                                                                            else:
                                                                                                                                                                                                                                                                                                                                address0 = FAILURE
                                                                                                                                                                                                                                                                                                                                if self._offset > self._failure:
                                                                                                                                                                                                                                                                                                                                    self._failure = self._offset
                                                                                                                                                                                                                                                                                                                                    self._expected = []
                                                                                                                                                                                                                                                                                                                                if self._offset == self._failure:
                                                                                                                                                                                                                                                                                                                                    self._expected.append('"Ba"')
                                                                                                                                                                                                                                                                                                                            if address0 is FAILURE:
                                                                                                                                                                                                                                                                                                                                self._offset = index1
                                                                                                                                                                                                                                                                                                                                chunk78 = None
                                                                                                                                                                                                                                                                                                                                if self._offset < self._input_size:
                                                                                                                                                                                                                                                                                                                                    chunk78 = self._input[self._offset:self._offset + 1]
                                                                                                                                                                                                                                                                                                                                if chunk78 == 'B':
                                                                                                                                                                                                                                                                                                                                    address0 = self._actions.make_element(self._input, self._offset, self._offset + 1)
                                                                                                                                                                                                                                                                                                                                    self._offset = self._offset + 1
                                                                                                                                                                                                                                                                                                                                else:
                                                                                                                                                                                                                                                                                                                                    address0 = FAILURE
                                                                                                                                                                                                                                                                                                                                    if self._offset > self._failure:
                                                                                                                                                                                                                                                                                                                                        self._failure = self._offset
                                                                                                                                                                                                                                                                                                                                        self._expected = []
                                                                                                                                                                                                                                                                                                                                    if self._offset == self._failure:
                                                                                                                                                                                                                                                                                                                                        self._expected.append('"B"')
                                                                                                                                                                                                                                                                                                                                if address0 is FAILURE:
                                                                                                                                                                                                                                                                                                                                    self._offset = index1
                                                                                                                                                                                                                                                                                                                                    chunk79 = None
                                                                                                                                                                                                                                                                                                                                    if self._offset < self._input_size:
                                                                                                                                                                                                                                                                                                                                        chunk79 = self._input[self._offset:self._offset + 2]
                                                                                                                                                                                                                                                                                                                                    if chunk79 == 'Au':
                                                                                                                                                                                                                                                                                                                                        address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                                                                                                                                                                                                        self._offset = self._offset + 2
                                                                                                                                                                                                                                                                                                                                    else:
                                                                                                                                                                                                                                                                                                                                        address0 = FAILURE
                                                                                                                                                                                                                                                                                                                                        if self._offset > self._failure:
                                                                                                                                                                                                                                                                                                                                            self._failure = self._offset
                                                                                                                                                                                                                                                                                                                                            self._expected = []
                                                                                                                                                                                                                                                                                                                                        if self._offset == self._failure:
                                                                                                                                                                                                                                                                                                                                            self._expected.append('"Au"')
                                                                                                                                                                                                                                                                                                                                    if address0 is FAILURE:
                                                                                                                                                                                                                                                                                                                                        self._offset = index1
                                                                                                                                                                                                                                                                                                                                        chunk80 = None
                                                                                                                                                                                                                                                                                                                                        if self._offset < self._input_size:
                                                                                                                                                                                                                                                                                                                                            chunk80 = self._input[self._offset:self._offset + 2]
                                                                                                                                                                                                                                                                                                                                        if chunk80 == 'As':
                                                                                                                                                                                                                                                                                                                                            address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                                                                                                                                                                                                            self._offset = self._offset + 2
                                                                                                                                                                                                                                                                                                                                        else:
                                                                                                                                                                                                                                                                                                                                            address0 = FAILURE
                                                                                                                                                                                                                                                                                                                                            if self._offset > self._failure:
                                                                                                                                                                                                                                                                                                                                                self._failure = self._offset
                                                                                                                                                                                                                                                                                                                                                self._expected = []
                                                                                                                                                                                                                                                                                                                                            if self._offset == self._failure:
                                                                                                                                                                                                                                                                                                                                                self._expected.append('"As"')
                                                                                                                                                                                                                                                                                                                                        if address0 is FAILURE:
                                                                                                                                                                                                                                                                                                                                            self._offset = index1
                                                                                                                                                                                                                                                                                                                                            chunk81 = None
                                                                                                                                                                                                                                                                                                                                            if self._offset < self._input_size:
                                                                                                                                                                                                                                                                                                                                                chunk81 = self._input[self._offset:self._offset + 2]
                                                                                                                                                                                                                                                                                                                                            if chunk81 == 'Ar':
                                                                                                                                                                                                                                                                                                                                                address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                                                                                                                                                                                                                self._offset = self._offset + 2
                                                                                                                                                                                                                                                                                                                                            else:
                                                                                                                                                                                                                                                                                                                                                address0 = FAILURE
                                                                                                                                                                                                                                                                                                                                                if self._offset > self._failure:
                                                                                                                                                                                                                                                                                                                                                    self._failure = self._offset
                                                                                                                                                                                                                                                                                                                                                    self._expected = []
                                                                                                                                                                                                                                                                                                                                                if self._offset == self._failure:
                                                                                                                                                                                                                                                                                                                                                    self._expected.append('"Ar"')
                                                                                                                                                                                                                                                                                                                                            if address0 is FAILURE:
                                                                                                                                                                                                                                                                                                                                                self._offset = index1
                                                                                                                                                                                                                                                                                                                                                chunk82 = None
                                                                                                                                                                                                                                                                                                                                                if self._offset < self._input_size:
                                                                                                                                                                                                                                                                                                                                                    chunk82 = self._input[self._offset:self._offset + 2]
                                                                                                                                                                                                                                                                                                                                                if chunk82 == 'Al':
                                                                                                                                                                                                                                                                                                                                                    address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                                                                                                                                                                                                                    self._offset = self._offset + 2
                                                                                                                                                                                                                                                                                                                                                else:
                                                                                                                                                                                                                                                                                                                                                    address0 = FAILURE
                                                                                                                                                                                                                                                                                                                                                    if self._offset > self._failure:
                                                                                                                                                                                                                                                                                                                                                        self._failure = self._offset
                                                                                                                                                                                                                                                                                                                                                        self._expected = []
                                                                                                                                                                                                                                                                                                                                                    if self._offset == self._failure:
                                                                                                                                                                                                                                                                                                                                                        self._expected.append('"Al"')
                                                                                                                                                                                                                                                                                                                                                if address0 is FAILURE:
                                                                                                                                                                                                                                                                                                                                                    self._offset = index1
                                                                                                                                                                                                                                                                                                                                                    chunk83 = None
                                                                                                                                                                                                                                                                                                                                                    if self._offset < self._input_size:
                                                                                                                                                                                                                                                                                                                                                        chunk83 = self._input[self._offset:self._offset + 2]
                                                                                                                                                                                                                                                                                                                                                    if chunk83 == 'Ag':
                                                                                                                                                                                                                                                                                                                                                        address0 = self._actions.make_element(self._input, self._offset, self._offset + 2)
                                                                                                                                                                                                                                                                                                                                                        self._offset = self._offset + 2
                                                                                                                                                                                                                                                                                                                                                    else:
                                                                                                                                                                                                                                                                                                                                                        address0 = FAILURE
                                                                                                                                                                                                                                                                                                                                                        if self._offset > self._failure:
                                                                                                                                                                                                                                                                                                                                                            self._failure = self._offset
                                                                                                                                                                                                                                                                                                                                                            self._expected = []
                                                                                                                                                                                                                                                                                                                                                        if self._offset == self._failure:
                                                                                                                                                                                                                                                                                                                                                            self._expected.append('"Ag"')
                                                                                                                                                                                                                                                                                                                                                    if address0 is FAILURE:
                                                                                                                                                                                                                                                                                                                                                        self._offset = index1
                                                                                                                                                                                                                                                                                                                                                        chunk84 = None
                                                                                                                                                                                                                                                                                                                                                        if self._offset < self._input_size:
                                                                                                                                                                                                                                                                                                                                                            chunk84 = self._input[self._offset:self._offset + 1]
                                                                                                                                                                                                                                                                                                                                                        if chunk84 == 'e':
                                                                                                                                                                                                                                                                                                                                                            address0 = self._actions.make_element(self._input, self._offset, self._offset + 1)
                                                                                                                                                                                                                                                                                                                                                            self._offset = self._offset + 1
                                                                                                                                                                                                                                                                                                                                                        else:
                                                                                                                                                                                                                                                                                                                                                            address0 = FAILURE
                                                                                                                                                                                                                                                                                                                                                            if self._offset > self._failure:
                                                                                                                                                                                                                                                                                                                                                                self._failure = self._offset
                                                                                                                                                                                                                                                                                                                                                                self._expected = []
                                                                                                                                                                                                                                                                                                                                                            if self._offset == self._failure:
                                                                                                                                                                                                                                                                                                                                                                self._expected.append('"e"')
                                                                                                                                                                                                                                                                                                                                                        if address0 is FAILURE:
                                                                                                                                                                                                                                                                                                                                                            self._offset = index1
        self._cache['element'][index0] = (address0, self._offset)
        return address0

    def _read_count(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['count'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        index1 = self._offset
        address0 = self._read_n()
        if address0 is FAILURE:
            address0 = formula_TreeNode(self._input[index1:index1], index1)
            self._offset = index1
        self._cache['count'][index0] = (address0, self._offset)
        return address0

    def _read_n(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['n'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        index1, elements0 = self._offset, []
        address1 = FAILURE
        address1 = self._read_non_zero_digit()
        if address1 is not FAILURE:
            elements0.append(address1)
            address2 = FAILURE
            remaining0, index2, elements1, address3 = 0, self._offset, [], True
            while address3 is not FAILURE:
                address3 = self._read_digit()
                if address3 is not FAILURE:
                    elements1.append(address3)
                    remaining0 -= 1
            if remaining0 <= 0:
                address2 = formula_TreeNode(self._input[index2:self._offset], index2, elements1)
                self._offset = self._offset
            else:
                address2 = FAILURE
            if address2 is not FAILURE:
                elements0.append(address2)
            else:
                elements0 = None
                self._offset = index1
        else:
            elements0 = None
            self._offset = index1
        if elements0 is None:
            address0 = FAILURE
        else:
            address0 = formula_TreeNode2(self._input[index1:self._offset], index1, elements0)
            self._offset = self._offset
        self._cache['n'][index0] = (address0, self._offset)
        return address0

    def _read_non_zero_digit(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['non_zero_digit'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        chunk0 = None
        if self._offset < self._input_size:
            chunk0 = self._input[self._offset:self._offset + 1]
        if chunk0 is not None and formula_Grammar.REGEX_1.search(chunk0):
            address0 = formula_TreeNode(self._input[self._offset:self._offset + 1], self._offset)
            self._offset = self._offset + 1
        else:
            address0 = FAILURE
            if self._offset > self._failure:
                self._failure = self._offset
                self._expected = []
            if self._offset == self._failure:
                self._expected.append('[1-9]')
        self._cache['non_zero_digit'][index0] = (address0, self._offset)
        return address0

    def _read_digit(self):
        address0, index0 = FAILURE, self._offset
        cached = self._cache['digit'].get(index0)
        if cached:
            self._offset = cached[1]
            return cached[0]
        chunk0 = None
        if self._offset < self._input_size:
            chunk0 = self._input[self._offset:self._offset + 1]
        if chunk0 is not None and formula_Grammar.REGEX_2.search(chunk0):
            address0 = formula_TreeNode(self._input[self._offset:self._offset + 1], self._offset)
            self._offset = self._offset + 1
        else:
            address0 = FAILURE
            if self._offset > self._failure:
                self._failure = self._offset
                self._expected = []
            if self._offset == self._failure:
                self._expected.append('[0-9]')
        self._cache['digit'][index0] = (address0, self._offset)
        return address0


class formula_Parser(formula_Grammar):
    def __init__(self, input, actions, types):
        self._input = input
        self._input_size = len(input)
        self._actions = actions
        self._types = types
        self._offset = 0
        self._cache = defaultdict(dict)
        self._failure = 0
        self._expected = []

    def parse(self):
        tree = self._read_formula()
        if tree is not FAILURE and self._offset == self._input_size:
            return tree
        if not self._expected:
            self._failure = self._offset
            self._expected.append('<EOF>')
        raise formula_ParseError(formula_format_error(self._input, self._failure, self._expected))


def formula_format_error(input, offset, expected):
    lines, line_no, position = input.split('\n'), 0, 0
    while position <= offset:
        position += len(lines[line_no]) + 1
        line_no += 1
    message, line = 'Line ' + str(line_no) + ': expected ' + ', '.join(expected) + '\n', lines[line_no - 1]
    message += line + '\n'
    position -= len(line) + 1
    message += ' ' * (offset - position)
    return message + '^'

def formula_parse(input, actions=None, types=None):
    parser = formula_Parser(input, actions, types)
    return parser.parse()

__version__ = "0.3"

start_time = time.time()

#
# Process Command Line Arguments (UNPLZ version)
#

study = sys.argv[1]  # .sqlite3
features = sys.argv[2]  # .features
exclusion_list_csv = sys.argv[3]  # "Blank, ISTD"

exclusion_list = []
if exclusion_list_csv != "":
    for group in exclusion_list_csv.strip().split(","):
        exclusion_list.append(group.strip())
 
MZ_TOLERANCE = float(sys.argv[4])  # 15.0
RT_TOLERANCE = float(sys.argv[5])  # 0.2
RT_WINDOW = float(sys.argv[6])  # 0.5
filename = os.path.basename(study).split(".")[0]

# output: .quantified

MS1_DBNAME = study
input_filename = features

#
# Set up our cursor
#
con = sqlite3.connect(MS1_DBNAME)
cur = con.cursor()

#
# First, a sanity check (somewhat repetitive to later code, but this is temporary and will be removed when all unsafe raw2sql
# generation will have been eliminated from the lab, along with any incorrect sqlite3 file...
#

#
# Test for rawfile.ID > 0 is historical and left for backwards compatibility with a long forgotten encoding standard regarding negative rawfile IDs!!!
#

if exclusion_list:
    predicted_sql_string = 'SELECT COUNT (DISTINCT name) from rawfile, metadata where rawfile.ID = metadata.rawfile and rawfile.ID > 0 and metadata.attribute = "Group" and metadata.value not in (' + ','.join(['?']*len(exclusion_list)) + ')'
else:
    predicted_sql_string = 'SELECT COUNT (DISTINCT name) from rawfile where rawfile.ID > 0'

sample_num = cur.execute(predicted_sql_string, exclusion_list).fetchone()[0]

if exclusion_list:
    observed_sql_string = 'SELECT COUNT (DISTINCT scans.rawfile) from scans, metadata where scans.rawfile = metadata.rawfile and scans.rawfile > 0 and metadata.attribute = "Group" and metadata.value not in (' + ','.join(['?']*len(exclusion_list)) + ')'
else:
    observed_sql_string = 'SELECT COUNT (DISTINCT rawfile) from scans where scans.rawfile > 0'
observed = cur.execute(observed_sql_string, exclusion_list).fetchone()[0]

if sample_num != observed:
    print("Sanity check failure: expected samples != observed files!!!",
          file=sys.stderr,
          flush=True)
    sys.exit(-1)

#
# Second, load mass_translation and time_translation factors, if they are available...
# TODO: Potentially factor this code out into a module that manages access to our db format.
#

try:
    mass_translation_factor = cur.execute(
        "SELECT value from sequence where attribute = 'mass_translation_factor'"
    ).fetchone()[0]
    time_translation_factor = cur.execute(
        "SELECT value from sequence where attribute = 'time_translation_factor'"
    ).fetchone()[0]
except:
    mass_translation_factor = 10000  # 1 = 0.0001 Da
    time_translation_factor = 1000  # 1 = 0.001 seconds

#
# Load immutable scan information, which will be necessary (e.g. for default zero intensity per rawfile x rt)
#

if exclusion_list:
    SAMPLES_SQL = 'SELECT DISTINCT name from rawfile, metadata where rawfile.ID = metadata.rawfile and rawfile.ID > 0 and metadata.attribute = "Group" and metadata.value not in (' + ','.join(['?']*len(exclusion_list)) + ') order by rawfile.ID'
else:
    SAMPLES_SQL = 'SELECT DISTINCT name from rawfile where ID > 0 order by ID'

samples = [entry[0] for entry in cur.execute(SAMPLES_SQL, exclusion_list)]

# NOTE: sample[0] often corresponds to ID = 1 -- IDs start at 1 so offsets in samples will _not_ immediately correspond to ID!!!

if exclusion_list:
    SCAN_SQL = 'SELECT scans.rawfile, scans.rt from scans, metadata where scans.rawfile = metadata.rawfile and scans.rawfile > 0 and scans.polarity = ? and scans.scan_type = "MS1" and metadata.attribute = "Group" and metadata.value not in (' + ','.join(['?']*len(exclusion_list)) + ') order by scans.rawfile, scans.rt'
else:
    SCAN_SQL = 'SELECT scans.rawfile, scans.rt from scans where scans.rawfile > 0 and scans.polarity = ? and scans.scan_type = "MS1" order by scans.rawfile, scans.rt'

pos_rawfile_rt_pairs = list(cur.execute(SCAN_SQL, ["+"] + exclusion_list))
neg_rawfile_rt_pairs = list(cur.execute(SCAN_SQL, ["-"] + exclusion_list))

if exclusion_list:
    EXICS_SQL = 'SELECT ms1_peaks.rawfile, ms1_peaks.rt, ms1_peaks.intensity, ms1_peaks.mz from ms1_peaks, metadata where ms1_peaks.rawfile = metadata.rawfile and ms1_peaks.rawfile > 0 and ms1_peaks.mz >= ? and ms1_peaks.mz <= ? and ms1_peaks.rt >= ? and ms1_peaks.rt <= ? and metadata.attribute = "Group" and metadata.value not in (' + ','.join(['?']*len(exclusion_list)) + ') order by ms1_peaks.rawfile, ms1_peaks.rt, ms1_peaks.intensity'
else:
    EXICS_SQL = 'SELECT ms1_peaks.rawfile, ms1_peaks.rt, ms1_peaks.intensity, ms1_peaks.mz from ms1_peaks where ms1_peaks.rawfile > 0 and ms1_peaks.mz >= ? and ms1_peaks.mz <= ? and ms1_peaks.rt >= ? and ms1_peaks.rt <= ? order by ms1_peaks.rawfile, ms1_peaks.rt, ms1_peaks.intensity'


def exics(polarity, mz, rt_start, rt_stop, mz_tol, exclusion_list):
    # retention times are assumed to be provided in minutes...
    # TODO: modify signature to remove polarity, for now keep in mind that mz is
    #       already negative when polarity is "-"
    # cur = con.cursor()
    xics = {}
    if polarity == "+":
        rawfile_rts = pos_rawfile_rt_pairs
    else:
        rawfile_rts = neg_rawfile_rt_pairs
    for (rawfile, rt) in rawfile_rts:
        if rawfile not in xics:
            xics[rawfile] = {}
        # Note that while the xics include data-pairs for all RTs,
        # the ones with non-zero data are, in fact, constrained by
        # rt_start and rt_stop...
        xics[rawfile][rt] = (
            0, 0
        )  # Setting the intensity to zero could mask a "real" zero in the data (for negative m/z values)... Assuming those are allowed.

    if polarity == "+":
        mz_low = mz * (1.0 - mz_tol)
        mz_high = mz * (1.0 + mz_tol)
    else:
        mz_high = mz * (1.0 - mz_tol)
        mz_low = mz * (1.0 + mz_tol)

    mz_low = round(mz_low * mass_translation_factor)
    mz_high = round(mz_high * mass_translation_factor)
    rt_start = round(rt_start * 60 * time_translation_factor
                     )  # time_translation_factor is in seconds not minutes
    rt_stop = round(rt_stop * 60 * time_translation_factor
                    )  # time_translation_factor is in seconds not minutes

    cur.execute(EXICS_SQL, [mz_low, mz_high, rt_start, rt_stop] + exclusion_list)
    for (rawfile, rt, intensity, omz) in cur:
        if polarity == "+":
            xics[rawfile][rt] = max(xics[rawfile][rt], (intensity, omz))
        else:
            xics[rawfile][rt] = max(
                xics[rawfile][rt],
                (intensity, -1 *
                 omz))  # Here a (0, -100) would lose out to the default (0, 0)

    float_min_time_factor = 60.0 * float(time_translation_factor)
    float_mass_factor = float(mass_translation_factor)
    xic_list = []
    prev_rawfile = 0
    for rawfile in xics:
        assert (
            rawfile > prev_rawfile
        )  # this should be true based on dictionary semantics in python, but better safe than sorry :-)
        prev_rawfile = rawfile
        xic_list.append(
            list(
                map(
                    lambda rt__int_mz: (
                        rt__int_mz[0] / float_min_time_factor,
                        (rt__int_mz[1][0], rt__int_mz[1][1] / float_mass_factor
                         ),
                    ),
                    xics[rawfile].items(),
                )))

    # cur.close()
    return xic_list


# reference_masses = [{"name": "Hydrogen", "symbol": "H", "mass": 1007825035}, {"name": "Silicon", "symbol": "Si", "mass": 27976926530}, {"name": "Lithium", "symbol": "Li", "mass": 7016003000}, {"name": "Boron", "symbol": "B", "mass": 11009305500}, {"name": "Carbon", "symbol": "C", "mass": 12000000000}, {"name": "Nitrogen", "symbol": "N", "mass": 14003074000}, {"name": "Oxygen", "symbol": "O", "mass": 15994914630}, {"name": "Fluorine", "symbol": "F", "mass": 18998403220}, {"name": "Sodium", "symbol": "Na", "mass": 22989767700}, {"name": "Magnesium", "symbol": "Mg", "mass": 23985042300}, {"name": "Phosphorous", "symbol": "P", "mass": 30973762000}, {"name": "Sulfur", "symbol": "S", "mass": 31972070700}, {"name": "Chlorine", "symbol": "Cl", "mass": 34968852720}, {"name": "Potassium", "symbol": "K", "mass": 38963707400}, {"name": "Calcium", "symbol": "Ca", "mass": 39962590600}, {"name": "Chromium", "symbol": "Cr", "mass": 51940509800}, {"name": "Manganese", "symbol": "Mn", "mass": 54938047100}, {"name": "Iron", "symbol": "Fe", "mass": 55934939300}, {"name": "Nickel", "symbol": "Ni", "mass": 57935346200}, {"name": "Cobalt", "symbol": "Co", "mass": 58933197600}, {"name": "Copper", "symbol": "Cu", "mass": 62929598900}, {"name": "Zinc", "symbol": "Zn", "mass": 63929144800}, {"name": "Arsenic", "symbol": "As", "mass": 74921594200}, {"name": "Bromine", "symbol": "Br", "mass": 78918336100}, {"name": "Selenium", "symbol": "Se", "mass": 79916519600}, {"name": "Molybdenum", "symbol": "Mo", "mass": 97905407300}, {"name": "Palladium", "symbol": "Pd", "mass": 105903478000}, {"name": "Silver", "symbol": "Ag", "mass": 106905092000}, {"name": "Cadmium", "symbol": "Cd", "mass": 113903357000}, {"name": "Iodine", "symbol": "I", "mass": 126904473000}, {"name": "Gold", "symbol": "Au", "mass": 196966543000}, {"name": "Mercury", "symbol": "Hg", "mass": 201970617000}]

# atomic_mass = {}
# symbols = []
# for entry in reference_masses:
#     atomic_mass[entry["symbol"]] = entry["mass"] * 0.000000001
#     symbols.append(entry["symbol"])

# symbols.sort(key=len, reverse=True)

proton = 1.00727647
electron = 0.00054858

C13_delta = 1.003354838  # https://en.wikipedia.org/wiki/Isotopes_of_carbon
N15_delta = 0.9970348934  # https://en.wikipedia.org/wiki/Isotopes_of_nitrogen
O18_delta = 2.0042463804  # https://en.wikipedia.org/wiki/Isotopes_of_oxygen

digits = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]


def find_first_nonmember(string, reference):
    i = 0
    while i < len(string):
        if string[i] not in reference:
            break
        i += 1
    return i


def parse_labeling_part(
    metabolite,
    labeling_part,
    is_molecular_formula,
    c_counter,
    n_counter,
    o_counter,
    part_of_pair=False,
):
    complete_labeling_part = labeling_part[:]
    M_label = ""
    if (not labeling_part.startswith("13C")
            and not labeling_part.startswith("15N")
            and not labeling_part.startswith("18O")):
        print(
            f"Invalid labeling label {labeling_part} for metabolite {metabolite}!!!",
            file=sys.stderr,
            flush=True)
        sys.exit(-1)
    if labeling_part.startswith("13C"):
        M_label = "13C"
    if labeling_part.startswith("15N"):
        M_label = "15N"
    if labeling_part.startswith("18O"):
        M_label = "18O"
    labeling_part = labeling_part[
        3:]  # not sure what this means, may need to change for 18O
    if (not labeling_part.startswith("[")) and (not is_molecular_formula):
        print(
            f"Cannot expand {complete_labeling_part} for {metabolite} when the provided 'formula' is an m/z value!!!",
            file=sys.stderr,
            flush=True)
        sys.exit(-1)
    if labeling_part.startswith("["):
        labeling_part = labeling_part[1:(-1)]
        if "-" in labeling_part:
            range_spec = labeling_part.split("-")
            M_range = list(range(int(range_spec[0]), int(range_spec[1]) + 1))
        else:
            M_range = [int(labeling_part)]
    else:
        if M_label == "13C":
            if part_of_pair:
                M_range = [c_counter]
            else:
                M_range = list(range(0, c_counter + 1))
        else:
            if M_label == "15N":
                if part_of_pair:
                    M_range = [n_counter]
                else:
                    M_range = list(range(0, n_counter + 1))
            else:
                if M_label == "18O":
                    if part_of_pair:
                        M_range = [o_counter]
                    else:
                        M_range = list(range(0, o_counter + 1))
                else:
                    print("Unknown Label", file=sys.stderr, flush=True)
    return (M_label, M_range)


def calc_labeling_label_delta(M_label, M_value):
    if M_label == "13C":
        return M_value * C13_delta
    if M_label == "15N":
        return M_value * N15_delta
    if M_label == "18O":
        return M_value * O18_delta
    print("Incorrect labeling requirements encountered: {M_label}, {M_value}",
          file=sys.stderr,
          flush=True)
    sys.exit(-1)


def parse_labeling_requirements(metabolite, labeling, base_mz,
                                is_molecular_formula, c_counter, n_counter,
                                o_counter):
    M_suffixes = []
    M_mzs = []

    if labeling.startswith('"'):
        labeling = labeling[1:(-1)]

    if not labeling:  # An empty labeling field will be ignored
        return ([], [])

    if "," in labeling:
        labeling_parts = labeling.split(",")
        (M1_label, M1_range) = parse_labeling_part(
            metabolite,
            labeling_parts[0],
            is_molecular_formula,
            c_counter,
            n_counter,
            o_counter,
            True,
        )
        (M2_label, M2_range) = parse_labeling_part(
            metabolite,
            labeling_parts[1],
            is_molecular_formula,
            c_counter,
            n_counter,
            o_counter,
            True,
        )
        assert len(M1_range) == 1
        assert len(M2_range) == 1
        M_suffixes = [f"-{M1_label},{M2_label}-{M1_range[0]},{M2_range[0]}"]
        if base_mz > 0:
            M_mzs = [
                base_mz + calc_labeling_label_delta(M1_label, M1_range[0]) +
                calc_labeling_label_delta(M2_label, M2_range[0])
            ]
        else:
            M_mzs = [
                base_mz - calc_labeling_label_delta(M1_label, M1_range[0]) -
                calc_labeling_label_delta(M2_label, M2_range[0])
            ]
    else:
        (M_label, M_range) = parse_labeling_part(metabolite, labeling,
                                                 is_molecular_formula,
                                                 c_counter, n_counter,
                                                 o_counter)
        for M_value in M_range:
            M_suffixes.append(f"-{M_label}-{M_value}")
            if base_mz > 0:
                M_mzs.append(base_mz +
                             calc_labeling_label_delta(M_label, M_value))
            else:
                M_mzs.append(base_mz -
                             calc_labeling_label_delta(M_label, M_value))
    return (M_suffixes, M_mzs)


metabolites = set()

metabolite_2_formula = {}
metabolite_2_mz = {}
metabolite_2_observed = {}
metabolite_2_rs = {}
metabolite_2_measurements = {}

print(f"loading XIC request file: {input_filename}", flush=True)

(rows, unmatched, unexpected) = loader(
    input_filename,
    {
        "Metabolite": {
            "field": "metabolite",
            "constructor": str,
            "required": True,
            "description": "Metabolite name.",
        },
        "Formula": {
            "field": "formula",
            "constructor": str,
            "required": True,
            "description": "Formula or m/z value.",
        },
        "InChIKey": {
            "field": "inchikey",
            "constructor": str,
            "required": False,
            "description": "InChIKey.",
        },
        "Labeling": {
            "field": "labeling",
            "constructor": str,
            "required": False,
            "description": "Labeling scheme assumed for the given metabolite.",
        },
        "Ion Type": {
            "field": "ion_type",
            "constructor": str,
            "required": True,
            "description": "Ionization type.",
        },
        # Either RT or RT Start+End must be present...
        "RT (min)": {
            "field": "rt",
            "constructor": float,
            "required": False,
            "description": "RT (in minutes).",
        },
        "RT Start (min)": {
            "field": "rt_start",
            "constructor": float,
            "required": False,
            "description": "RT window start (in minutes).",
        },
        "RT End (min)": {
            "field": "rt_stop",
            "constructor": float,
            "required": False,
            "description": "RT window end (in minutes).",
        },
        "m/z Tolerance (ppm)": {
            "field": "mz_tol",
            "constructor": float,
            "required": False,
            "description": "m/z tolerance in PPM.",
        },
        "RT Tolerance (min)": {
            "field": "rt_tol",
            "constructor": float,
            "required": False,
            "description": "RT tolerance (in minutes).",
        },
        "FDR": {
            "field": "fdr",
            "constructor": int,
            "required": False,
            "description": "FDR of Metabolite ID.",
        },
    },
)


def refined_max(an_xic, tight_start, tight_stop):
    return max(
        (intensity, mz, t) for (t, (intensity, mz)) in an_xic
        if tight_start <= t <= tight_stop
    )  # This will fail if tight_start to tight_stop is too narrow to afford even one scan per sample!


def imposed_max(an_xic, rt):
    for (t, (intensity, mz)) in an_xic:
        if t == rt:
            return (intensity, mz, t)
    print("imposed rt did not exist in the target xic!",
          file=sys.stderr,
          flush=True)
    sys.exit(-1)


def robust_max(aList):
    if not aList:
        return 0.0
    return max(aList)


output = open(f"{os.getcwd()}/output/quantified/{filename}.quantified", "w")
if "inchikey" in unmatched and "labeling" in unmatched and "fdr" in unmatched:
    print(
        "\t".join([
            "Metabolite",
            "Formula",
            "Ion Type",
            "RT Start (min)",
            "RT End (min)",
            "m/z Tolerance (ppm)",
            "RT Tolerance (min)",
            "mz",
            "obs_mz",
            "ppm",
            "winner",
            "RT",
            "RT_min",
            "RT_max",
            "RT_range",
            "detections",
        ] + samples),
        file=output,
    )
elif "inchikey" in unmatched and "labeling" in unmatched and "fdr" not in unmatched:
    print(
        "\t".join([
            "Metabolite",
            "Formula",
            "FDR",
            "Ion Type",
            "RT Start (min)",
            "RT End (min)",
            "m/z Tolerance (ppm)",
            "RT Tolerance (min)",
            "mz",
            "obs_mz",
            "ppm",
            "winner",
            "RT",
            "RT_min",
            "RT_max",
            "RT_range",
            "detections",
        ] + samples),
        file=output,
    )
elif "inchikey" in unmatched and "fdr" in unmatched:
    print(
        "\t".join([
            "Metabolite",
            "Formula",
            "Labeling",
            "Ion Type",
            "RT Start (min)",
            "RT End (min)",
            "m/z Tolerance (ppm)",
            "RT Tolerance (min)",
            "mz",
            "obs_mz",
            "ppm",
            "winner",
            "is_global_winner",
            "RT",
            "RT_min",
            "RT_max",
            "RT_range",
            "detections",
        ] + samples),
        file=output,
    )
elif "inchikey" in unmatched and "fdr" not in unmatched:
    print(
        "\t".join([
            "Metabolite",
            "Formula",
            "FDR",
            "Labeling",
            "Ion Type",
            "RT Start (min)",
            "RT End (min)",
            "m/z Tolerance (ppm)",
            "RT Tolerance (min)",
            "mz",
            "obs_mz",
            "ppm",
            "winner",
            "is_global_winner",
            "RT",
            "RT_min",
            "RT_max",
            "RT_range",
            "detections",
        ] + samples),
        file=output,
    )
elif "labeling" in unmatched and "fdr" in unmatched:
    print(
        "\t".join([
            "Metabolite",
            "Formula",
            "InChIKey",
            "Ion Type",
            "RT Start (min)",
            "RT End (min)",
            "m/z Tolerance (ppm)",
            "RT Tolerance (min)",
            "mz",
            "obs_mz",
            "ppm",
            "winner",
            "RT",
            "RT_min",
            "RT_max",
            "RT_range",
            "detections",
        ] + samples),
        file=output,
    )
elif "labeling" in unmatched and "fdr" not in unmatched:
    print(
        "\t".join([
            "Metabolite",
            "Formula",
            "InChIKey",
            "FDR",
            "Ion Type",
            "RT Start (min)",
            "RT End (min)",
            "m/z Tolerance (ppm)",
            "RT Tolerance (min)",
            "mz",
            "obs_mz",
            "ppm",
            "winner",
            "RT",
            "RT_min",
            "RT_max",
            "RT_range",
            "detections",
        ] + samples),
        file=output,
    )
elif "fdr" in unmatched:
    print(
        "\t".join([
            "Metabolite",
            "Formula",
            "InChIKey",
            "Labeling",
            "Ion Type",
            "RT Start (min)",
            "RT End (min)",
            "m/z Tolerance (ppm)",
            "RT Tolerance (min)",
            "mz",
            "obs_mz",
            "ppm",
            "winner",
            "is_global_winner",
            "RT",
            "RT_min",
            "RT_max",
            "RT_range",
            "detections",
        ] + samples),
        file=output,
    )
else:
    print(
        "\t".join([
            "Metabolite",
            "Formula",
            "InChIKey",
            "FDR",
            "Labeling",
            "Ion Type",
            "RT Start (min)",
            "RT End (min)",
            "m/z Tolerance (ppm)",
            "RT Tolerance (min)",
            "mz",
            "obs_mz",
            "ppm",
            "winner",
            "is_global_winner",
            "RT",
            "RT_min",
            "RT_max",
            "RT_range",
            "detections",
        ] + samples),
        file=output,
    )


def process_entry(an_entry):
    (row, M_suffixes, M_mzs, M_measurements) = an_entry
    mega_max = []
    for M_offset in range(len(M_suffixes)):
        measurements = M_measurements[M_offset]
        maxima = list(
            map(lambda x: robust_max([pair for (rt, pair) in x]),
                measurements))
        winner_pair = max(enumerate(maxima),
                          key=lambda i_max_int: i_max_int[1]
                          )  # winner_pair = (offset, (intensity, mz))
        # winner_sample = samples[winner_pair[0]]
        (the_rt, the_pair) = max(
            measurements[winner_pair[0]],
            key=lambda x: x[1])  # the_pair should equal winner_pair[1]
        mega_max.append(
            (the_pair[0], M_offset, the_rt)  # the_pair[0] == intensity
        )  # (what intensity, which isotope, when)
    mega_max.sort(reverse=True)
    mega_winner_intensity = mega_max[0][0]
    # mega_winner_sample = mega_max[0][1]
    mega_winner_offset = mega_max[0][1]
    mega_winner_rt = mega_max[0][2]
    # mega_winner_mz = mega_max[0][3]
    sample_winner_rts = []
    for sample_offset in range(len(M_measurements[0])):
        isotope_maxima = []
        for M_offset in range(len(M_suffixes)):
            try:
                isotope_maxima.append(
                    refined_max(
                        M_measurements[M_offset][sample_offset],
                        mega_winner_rt - row.rt_tol,
                        mega_winner_rt + row.rt_tol,
                    ))
            except:
                print(
                    f"--> skipping row with insufficient coverage in sample {samples[sample_offset]} (in range: [{mega_winner_rt - row.rt_tol} - {mega_winner_rt + row.rt_tol}])!!!",
                    flush=True)
                return
        isotope_maxima.sort(key=lambda x: x[2])
        middle = len(isotope_maxima) // 2
        if (len(isotope_maxima) % 2) :
            sample_winner = isotope_maxima[middle]
        else:
            left_winner = isotope_maxima[middle - 1]
            right_winner = isotope_maxima[middle]
            if abs(left_winner[2] - mega_winner_rt) <= abs(right_winner[2] - mega_winner_rt):
                sample_winner = left_winner
            else:
                sample_winner = right_winner
        # sample_winner = max(isotope_maxima) <-- we used to over-emphasize intensity over the wisdom of the crows...
        sample_winner_rts.append(sample_winner[2])
    for M_offset in range(len(M_suffixes)):
        measurements = M_measurements[M_offset]
        if M_offset == mega_winner_offset:
            is_global_winner = "Yes"
        else:
            is_global_winner = "No"
        if mega_winner_intensity == 0.0:
            rt_min = 0.0
            rt_max = 0.0
            rt_range = 0.0
            finalized = ["0"] * len(measurements)
            local_winner_mz = 0.0
            local_winner_sample = ""
            local_winner_rt = 0.0
            local_max = 0.0
            ppm = 0.0
            detections = 0
        else:
            # finalized_vals = list(map(lambda x: refined_max(x, mega_winner_rt - row.rt_tol, mega_winner_rt + row.rt_tol), measurements))
            finalized_vals = list(
                map(lambda x: imposed_max(*x),
                    zip(measurements, sample_winner_rts)))
            local_winner_mz = 0.0
            local_winner_sample = ""
            local_winner_rt = 0.0
            local_max = 0.0
            sample_offset = -1
            rts = []
            for x in finalized_vals:
                sample_offset += 1
                if x[0] > 0.0:
                    rts.append(x[2])
                if x[0] > local_max:
                    local_max = x[0]
                    local_winner_mz = x[1]
                    local_winner_rt = x[2]
                    local_winner_sample = samples[sample_offset]
            detections = len(rts)
            if not rts:
                rt_min = 0
                rt_max = 0
                rt_range = 0
                ppm = 0
            else:
                rt_min = min(rts)
                rt_max = max(rts)
                rt_range = rt_max - rt_min
                if row.polarity == "+":
                    ppm = (1000000.0 * (local_winner_mz - M_mzs[M_offset]) /
                           M_mzs[M_offset])
                else:
                    ppm = (1000000.0 *
                           (((-1) * local_winner_mz) - M_mzs[M_offset]) /
                           M_mzs[M_offset])

            finalized = list(
                map(lambda x: "%.0f" % x,
                    map(lambda pair: pair[0], finalized_vals)))
        if "inchikey" in unmatched and "labeling" in unmatched and "fdr" in unmatched:
            print(
                "\t".join([
                    row.metabolite + M_suffixes[M_offset],
                    row.formula + M_suffixes[M_offset],
                    row.ion_type,
                    "%.2f" % row.rt_start,
                    "%.2f" % row.rt_stop,
                    "%.1f" % (row.mz_tol * 1000000.0),
                    "%.2f" % row.rt_tol,
                    "%.4f" % abs(M_mzs[M_offset]),
                    "%.4f" % abs(local_winner_mz),
                    "%.1f" % ppm,
                    local_winner_sample,
                    "%.2f" % local_winner_rt,
                    "%.2f" % rt_min,
                    "%.2f" % rt_max,
                    "%.2f" % rt_range,
                    "%d" % detections,
                ] + finalized),
                file=output,
            )
        elif "inchikey" in unmatched and "labeling" in unmatched and "fdr" not in unmatched:
            print(
                "\t".join([
                    row.metabolite + M_suffixes[M_offset],
                    row.formula + M_suffixes[M_offset],
                    "%d" % row.fdr,
                    row.ion_type,
                    "%.2f" % row.rt_start,
                    "%.2f" % row.rt_stop,
                    "%.1f" % (row.mz_tol * 1000000.0),
                    "%.2f" % row.rt_tol,
                    "%.4f" % abs(M_mzs[M_offset]),
                    "%.4f" % abs(local_winner_mz),
                    "%.1f" % ppm,
                    local_winner_sample,
                    "%.2f" % local_winner_rt,
                    "%.2f" % rt_min,
                    "%.2f" % rt_max,
                    "%.2f" % rt_range,
                    "%d" % detections,
                ] + finalized),
                file=output,
            )
        elif "inchikey" in unmatched and "fdr" in unmatched:
            print(
                "\t".join([
                    row.metabolite + M_suffixes[M_offset],
                    row.formula + M_suffixes[M_offset],
                    row.labeling,
                    row.ion_type,
                    "%.2f" % row.rt_start,
                    "%.2f" % row.rt_stop,
                    "%.1f" % (row.mz_tol * 1000000.0),
                    "%.2f" % row.rt_tol,
                    "%.4f" % abs(M_mzs[M_offset]),
                    "%.4f" % abs(local_winner_mz),
                    "%.1f" % ppm,
                    local_winner_sample,
                    is_global_winner,
                    "%.2f" % local_winner_rt,
                    "%.2f" % rt_min,
                    "%.2f" % rt_max,
                    "%.2f" % rt_range,
                    "%d" % detections,
                ] + finalized),
                file=output,
            )
        elif "inchikey" in unmatched and "fdr" not in unmatched:
            print(
                "\t".join([
                    row.metabolite + M_suffixes[M_offset],
                    row.formula + M_suffixes[M_offset],
                    "%d" % row.fdr,
                    row.labeling,
                    row.ion_type,
                    "%.2f" % row.rt_start,
                    "%.2f" % row.rt_stop,
                    "%.1f" % (row.mz_tol * 1000000.0),
                    "%.2f" % row.rt_tol,
                    "%.4f" % abs(M_mzs[M_offset]),
                    "%.4f" % abs(local_winner_mz),
                    "%.1f" % ppm,
                    local_winner_sample,
                    is_global_winner,
                    "%.2f" % local_winner_rt,
                    "%.2f" % rt_min,
                    "%.2f" % rt_max,
                    "%.2f" % rt_range,
                    "%d" % detections,
                ] + finalized),
                file=output,
            )
        elif "labeling" in unmatched and "fdr" in unmatched:
            print(
                "\t".join([
                    row.metabolite + M_suffixes[M_offset],
                    row.formula + M_suffixes[M_offset],
                    row.inchikey + M_suffixes[M_offset],
                    row.ion_type,
                    "%.2f" % row.rt_start,
                    "%.2f" % row.rt_stop,
                    "%.1f" % (row.mz_tol * 1000000.0),
                    "%.2f" % row.rt_tol,
                    "%.4f" % abs(M_mzs[M_offset]),
                    "%.4f" % abs(local_winner_mz),
                    "%.1f" % ppm,
                    local_winner_sample,
                    "%.2f" % local_winner_rt,
                    "%.2f" % rt_min,
                    "%.2f" % rt_max,
                    "%.2f" % rt_range,
                    "%d" % detections,
                ] + finalized),
                file=output,
            )
        elif "labeling" in unmatched and "fdr" not in unmatched:
            print(
                "\t".join([
                    row.metabolite + M_suffixes[M_offset],
                    row.formula + M_suffixes[M_offset],
                    row.inchikey + M_suffixes[M_offset],
                    "%d" % row.fdr,
                    row.ion_type,
                    "%.2f" % row.rt_start,
                    "%.2f" % row.rt_stop,
                    "%.1f" % (row.mz_tol * 1000000.0),
                    "%.2f" % row.rt_tol,
                    "%.4f" % abs(M_mzs[M_offset]),
                    "%.4f" % abs(local_winner_mz),
                    "%.1f" % ppm,
                    local_winner_sample,
                    "%.2f" % local_winner_rt,
                    "%.2f" % rt_min,
                    "%.2f" % rt_max,
                    "%.2f" % rt_range,
                    "%d" % detections,
                ] + finalized),
                file=output,
            )
        elif "fdr" in unmatched:
            print(
                "\t".join([
                    row.metabolite + M_suffixes[M_offset],
                    row.formula + M_suffixes[M_offset],
                    row.inchikey + M_suffixes[M_offset],
                    row.labeling,
                    row.ion_type,
                    "%.2f" % row.rt_start,
                    "%.2f" % row.rt_stop,
                    "%.1f" % (row.mz_tol * 1000000.0),
                    "%.2f" % row.rt_tol,
                    "%.4f" % abs(M_mzs[M_offset]),
                    "%.4f" % abs(local_winner_mz),
                    "%.1f" % ppm,
                    local_winner_sample,
                    is_global_winner,
                    "%.2f" % local_winner_rt,
                    "%.2f" % rt_min,
                    "%.2f" % rt_max,
                    "%.2f" % rt_range,
                    "%d" % detections,
                ] + finalized),
                file=output,
            )
        else:
            print(
                "\t".join([
                    row.metabolite + M_suffixes[M_offset],
                    row.formula + M_suffixes[M_offset],
                    row.inchikey + M_suffixes[M_offset],
                    "%d" % row.fdr,
                    row.labeling,
                    row.ion_type,
                    "%.2f" % row.rt_start,
                    "%.2f" % row.rt_stop,
                    "%.1f" % (row.mz_tol * 1000000.0),
                    "%.2f" % row.rt_tol,
                    "%.4f" % abs(M_mzs[M_offset]),
                    "%.4f" % abs(local_winner_mz),
                    "%.1f" % ppm,
                    local_winner_sample,
                    is_global_winner,
                    "%.2f" % local_winner_rt,
                    "%.2f" % rt_min,
                    "%.2f" % rt_max,
                    "%.2f" % rt_range,
                    "%d" % detections,
                ] + finalized),
                file=output,
            )
    output.flush()


for row in rows:
    print(f"Processing {row.metabolite}: ", end="", flush=True)
    if ("rt" not in vars(row)) and (not (("rt_start" in vars(row)) and
                                         ("rt_stop" in vars(row)))):
        print(f"--> skipping row with insufficient information!!!", flush=True)
        continue
    before = time.time()
    if not (("rt_start" in vars(row)) and ("rt_stop" in vars(row))):
        row["rt_start"] = max(row["rt"] - (RT_WINDOW / 2), 0.0)
        row["rt_stop"] = row["rt"] + (RT_WINDOW / 2)
    if "mz_tol" not in vars(row):
        row["mz_tol"] = MZ_TOLERANCE
    row.mz_tol = row.mz_tol / 1000000.0
    if "rt_tol" not in vars(row):
        row["rt_tol"] = RT_TOLERANCE
    is_molecular_formula = True
    c_counter = 0
    n_counter = 0
    o_counter = 0
    try:
        row.mz = float(row.formula)
        is_molecular_formula = False
        if row.mz > 0.0:
            row.polarity = "+"
        else:
            row.polarity = "-"
    except ValueError:
        # (the_mz, c_counter, n_counter, o_counter) = parse_formula(row.formula)
        parsed_formula = formula_parse(row.formula,
                                       actions=Formula_Actions())
        the_mz = 0.0
        c_counter = 0
        n_counter = 0
        o_counter = 0
        for term in parsed_formula:
            the_mz += term["mass"]
            if term["atom"] == "C":
                c_counter += term["count"]
            if term["atom"] == "O":
                o_counter += term["count"]
            if term["atom"] == "N":
                n_counter += term["count"]
        parsed = nist_ion_descriptions_parse(row.ion_type,
                                             actions=Actions())
        row.polarity = row.ion_type[-1]
        charge = 0
        z_string = parsed["z"]
        if z_string == "+":
            charge = 1
        elif z_string == "-":
            charge = -1
        else:
            if row.polarity == "+":
                charge = int(z_string[:(-1)])
            else:
                charge = (-1) * int(z_string[:(-1)])
        row.mz = ((the_mz * parsed["molecular_ion_count"]) + parsed["delta"] -
                  (charge * electron)) / charge
    if "labeling" in unmatched:
        exics_list = [
            exics(row.polarity, row.mz, row.rt_start, row.rt_stop, row.mz_tol, exclusion_list)
        ]
        process_entry((row, [""], [row.mz], exics_list))
    else:
        (M_suffixes, M_values) = parse_labeling_requirements(
            row.metabolite,
            row.labeling,
            row.mz,
            is_molecular_formula,
            c_counter,
            n_counter,
            o_counter,
        )
        if not M_suffixes:
            exics_list = [
                exics(row.polarity, row.mz, row.rt_start, row.rt_stop,
                      row.mz_tol, exclusion_list)
            ]
            process_entry((row, [""], [row.mz], exics_list))
        else:
            exics_list = list(
                map(
                    lambda m_value: exics(row.polarity, m_value, row.rt_start,
                                          row.rt_stop, row.mz_tol, exclusion_list),
                    M_values,
                ))
            process_entry((row, M_suffixes, M_values, exics_list))
    after = time.time()
    print(
        f"{len(exics_list)} GICs in: {after - before :.2f} seconds ({(after - before) / len(exics_list) :.2f} / GIC)...",
        flush=True)

output.close()

stop_time = time.time()

print(
    f"Skeleton processed {len(rows)} entries in {stop_time - start_time :.2f} seconds.",
    flush=True)
