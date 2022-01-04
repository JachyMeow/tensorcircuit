"""
visualization on circuits
"""

from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np


def gate_name_trans(gate_name: str) -> Tuple[int, str]:
    ctrl_number = 0
    while gate_name[ctrl_number] == "c":
        ctrl_number += 1
    return ctrl_number, gate_name[ctrl_number:]


def qir2tex(
    qir: List[Dict[str, Any]],
    n: int,
    init: Optional[List[str]] = None,
    measure: Optional[List[str]] = None,
    rcompress: bool = False,
    lcompress: bool = False,
    return_string_table: bool = False,
) -> Union[str, Tuple[str, List[List[str]]]]:
    # flag for applied layers
    flag = np.zeros(n, dtype=int)
    tex_string_table: List[List[str]] = [[] for _ in range(n)]

    # initial state presentation
    if init is None:
        for i in range(n):
            tex_string_table[i].append(r"\lstick{$\ket{0}$}")
    else:
        for i in range(n):
            if init[i]:
                tex_string_table[i].append(r"\lstick{$\ket{" + init[i] + r"}$}")
            else:
                tex_string_table[i].append(r"\lstick{}")

    # apply gates in qir
    for x in qir:

        idx = x["index"]
        gate_length = len(idx)
        if x["name"].startswith("invisible"):
            p = max(flag[min(idx) : max(idx) + 1]) + 1
            for i in range(min(idx), max(idx) + 1):
                tex_string_table[i] += [r"\qw "] * (p - flag[i] - 1)
                tex_string_table[i] += [r"\ghost{" + x["name"][7:] + "}\qw "]
                flag[i] = p
        else:
            ctrl_number, gate_name = gate_name_trans(x["name"])

            if "ctrl" in x.keys():
                ctrlbits = x["ctrl"]
            else:
                ctrlbits = [1] * ctrl_number

            low_idx = min(idx[ctrl_number:])
            high_idx = max(idx[ctrl_number:])

            p = max(flag[min(idx) : max(idx) + 1]) + 1
            for i in range(min(idx), max(idx) + 1):
                tex_string_table[i] += [r"\qw "] * (p - flag[i])
                flag[i] = p

            # control qubits
            for i in range(ctrl_number):
                if ctrlbits[i]:
                    ctrlstr = r"\ctrl{"
                else:
                    ctrlstr = r"\octrl{"
                ctrli = idx[i]
                if ctrli < low_idx:
                    tex_string_table[ctrli][-1] = ctrlstr + str(low_idx - ctrli) + r"} "
                elif ctrli > high_idx:
                    tex_string_table[ctrli][-1] = (
                        ctrlstr + str(high_idx - ctrli) + r"} "
                    )
                else:
                    tex_string_table[ctrli][-1] = ctrlstr + r"} "

            # controlled gate
            for i in range(min(idx), max(idx) + 1):
                # r" \qw " rather than r"\qw " represent that a vline will cross at this point
                # (flag for further compression operation)
                if tex_string_table[i][-1] == r"\qw ":
                    tex_string_table[i][-1] = r" \qw "

            if gate_length - ctrl_number == 1:
                if gate_name == "not":
                    tex_string_table[idx[ctrl_number]][-1] = r"\targ{} "
                elif gate_name == "phase":
                    tex_string_table[idx[ctrl_number]][-1] = r"\phase{} "
                #             elif gate_name == "none":
                #                 tex_string_table[idx[ctrl_number]][-1] = r"\ghost{}\qw "
                else:
                    tex_string_table[idx[ctrl_number]][-1] = (
                        r"\gate{" + gate_name + r"} "
                    )
            else:
                # multiqubits gate case
                idxp = np.sort(idx[ctrl_number:])
                p = 0
                vl = 0
                hi = 0
                while p < len(idxp):
                    if vl != 0:
                        tex_string_table[idxp[p - 1]][-1] = (
                            tex_string_table[idxp[p - 1]][-1]
                            + r"\vcw{"
                            + str(vl)
                            + r"} "
                            + r"\vqw{"
                            + str(vl)
                            + r"} "
                        )
                    li = idxp[p]
                    while p < len(idxp) - 1:
                        if idxp[p + 1] - idxp[p] == 1:
                            p = p + 1
                        else:
                            break
                    hi = idxp[p]
                    tex_string_table[li][-1] = (
                        r"\gate[" + str(hi + 1 - li) + r"]{" + gate_name + r"} "
                    )
                    p = p + 1
                    if p < len(idxp):
                        vl = idxp[p] - idxp[p - 1]
                # delete qwires on gate's qubits
                for i in idx:
                    if tex_string_table[i][-1] == r" \qw ":
                        tex_string_table[i][-1] = " "

    p = max(flag)
    for i in range(n):
        tex_string_table[i] += [r"\qw "] * (p - flag[i])

    #             # old version: linethrought
    #             for i in range(low_idx, high_idx + 1):
    #                 if (tex_string_table[i][-1] == r"\qw "):
    #                     tex_string_table[i][-1] = r"\linethrough "
    #             for i in idx[ctrl_number:]:
    #                 tex_string_table[i][-1] = r" "
    #             tex_string_table[low_idx][-1] = r"\gate[" + str(high_idx + 1 - low_idx) + r"]{" + gate_name + r"} "

    # right compression
    if rcompress:
        for i in range(n):
            while (tex_string_table[i][-1] == r"\qw ") | (
                tex_string_table[i][-1] == r" \qw "
            ):
                if tex_string_table[i][-1] == r"\qw ":
                    tex_string_table[i].pop()
                else:
                    p = 1
                    while p < len(tex_string_table[i]):
                        if tex_string_table[i][-p] == r" \qw ":
                            p += 1
                        else:
                            break
                    if tex_string_table[i][-p] == r"\qw ":
                        tex_string_table[i] = tex_string_table[i][:-p]
                    else:
                        break
    # left compression
    if lcompress:
        for i in range(n):
            p = 0
            lstring = len(tex_string_table[i])
            while p + 1 < lstring - 1:
                if tex_string_table[i][p + 1] == r"\qw ":
                    tex_string_table[i][p + 1] = r" "
                    p += 1
                else:
                    break
            tmp = tex_string_table[i][0]
            tex_string_table[i][0] = tex_string_table[i][p]
            tex_string_table[i][p] = tmp

    # measurement
    if measure is None:
        for i in range(n - 1):
            tex_string_table[i].append(r"\qw \\")
        tex_string_table[n - 1].append(r"\qw ")
    else:
        for i in range(n):
            if not measure[i]:
                tex_string_table[i].append(r"\qw \\")
            else:
                tex_string_table[i].append(r"\meter{" + measure[i] + r"} \\")
        tex_string_table[-1][-1] = tex_string_table[-1][-1][:-2]

    texcode = r"\begin{quantikz}" + "\n"
    for i in range(n):
        for x in tex_string_table[i]:  # type: ignore
            texcode += x + r"&"  # type: ignore
        texcode = texcode[:-1] + "\n"
    texcode += r"\end{quantikz}"

    if return_string_table:
        return texcode, tex_string_table
    else:
        return texcode