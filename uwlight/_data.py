"""Loading of the packaged coefficient tables.

Every table is a CSV shipped inside the package. Each row carries a ``status``
column recording what is known about that particular value; nothing is
silently cleaned up on the way in.
"""

from __future__ import annotations

import csv
from functools import lru_cache
from importlib import resources

import numpy as np

#: Values whose ``status`` is one of these should not be used without the
#: caller being told. See README sections 1-6.
QUESTIONABLE = frozenset({"suspect", "missing", "extrapolated",
                          "model_extrapolation", "reconstructed"})


def _read(name: str) -> list[dict[str, str]]:
    path = resources.files("uwlight.data").joinpath(name)
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


@lru_cache(maxsize=None)
def _rows(name: str) -> tuple[dict[str, str], ...]:
    return tuple(_read(name))


def _to_float(text: str) -> float:
    return float(text) if text.strip() else float("nan")


@lru_cache(maxsize=None)
def spectrum(
    filename: str,
    water_type: str,
    quantity: str | None,
    value_column: str,
) -> tuple[np.ndarray, np.ndarray, tuple[str, ...]]:
    """Return ``(wavelengths, values, statuses)`` for one series.

    Rows whose value is empty are kept, with the value set to NaN, so that a
    gap in the published table stays visible instead of being interpolated
    across without comment.
    """
    wl: list[float] = []
    values: list[float] = []
    statuses: list[str] = []
    for row in _rows(filename):
        if row.get("water_type") != water_type:
            continue
        if quantity is not None and row.get("quantity") != quantity:
            continue
        wl.append(float(row["wavelength_nm"]))
        values.append(_to_float(row[value_column]))
        statuses.append(row.get("status", ""))
    if not wl:
        raise KeyError(
            f"no rows in {filename} for water_type={water_type!r}"
            + (f", quantity={quantity!r}" if quantity else "")
        )
    order = np.argsort(wl)
    return (
        np.asarray(wl, dtype=float)[order],
        np.asarray(values, dtype=float)[order],
        tuple(statuses[i] for i in order),
    )


@lru_cache(maxsize=None)
def notes(filename: str, water_type: str, quantity: str | None) -> dict[float, str]:
    """Map wavelength to the ``note`` column, for rows that carry one."""
    out: dict[float, str] = {}
    for row in _rows(filename):
        if row.get("water_type") != water_type:
            continue
        if quantity is not None and row.get("quantity") != quantity:
            continue
        note = row.get("note", "").strip()
        if note:
            out[float(row["wavelength_nm"])] = note
    return out


@lru_cache(maxsize=None)
def austin_model() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return ``(wavelengths, M, Kw)`` from Austin & Petzold (1986) Table IV."""
    rows = _rows("austin1986_model.csv")
    wl = np.array([float(r["wavelength_nm"]) for r in rows])
    m = np.array([float(r["M_slope"]) for r in rows])
    kw = np.array([float(r["Kw_pure_seawater_per_m"]) for r in rows])
    order = np.argsort(wl)
    return wl[order], m[order], kw[order]


@lru_cache(maxsize=None)
def b_from_c_ratio() -> tuple[np.ndarray, dict[str, np.ndarray]]:
    """Return ``(wavelengths, {statistic: ratio})`` from Smart (2007) Table 1."""
    rows = _rows("smart2007_b_from_c.csv")
    wl = sorted({float(r["wavelength_nm"]) for r in rows})
    out: dict[str, np.ndarray] = {}
    for stat in ("average", "min", "max"):
        by_wl = {
            float(r["wavelength_nm"]): float(r["b_minus_bw_over_c_minus_cw"])
            for r in rows
            if r["statistic"] == stat
        }
        out[stat] = np.array([by_wl[w] for w in wl])
    return np.array(wl), out
