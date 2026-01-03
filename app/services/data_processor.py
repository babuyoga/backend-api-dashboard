"""Data processing functions for the Finance Dashboard API."""

from __future__ import annotations
import pandas as pd
import numpy as np
from collections import defaultdict
from typing import Any, Dict, List, Tuple
from app.utils.helpers import (
    _group_by_job, _load_rows, _to_number, period_to_label,
    safe_str, safe_num, _longest_nonempty, filter_by_project,
    _first_nonempty, _normalize_project_groups, merge_or_longest
)


def table_to_nested_json(df: pd.DataFrame, projno) -> Dict[str, List[Dict[str, Any]]]:
    req = ["iProjNo_group", "iProjNo", "cSegment", "iProjYear", "cPackage", "cPeriod", "cElementCode", "TYP", "cType",
           "rForecast", "rYearAct", "cSubDesc2", "cSubDesc3", "cClient", "cProjDesc", "cProjMgr", "cClientDesc", "cMajorDesc", "cBookDesc"]
    miss = [c for c in req if c not in df.columns]
    if miss:
        raise ValueError(f"Missing required columns in DataFrame: {miss}")

    d = filter_by_project(df[req].copy(), projno)
    d[["rForecast", "rYearAct"]] = d[["rForecast", "rYearAct"]].apply(lambda col: col.apply(safe_num))
    d["period_label"] = d["cPeriod"].map(period_to_label)
    d["section"] = d["cSegment"].map(safe_str) + " - " + d["cMajorDesc"].map(safe_str)

    entry_keys = ["period_label", "iProjNo_group", "section", "TYP"]
    d = d.sort_values(["period_label", "iProjNo_group", "section", "TYP", "cSubDesc2", "cSubDesc3"])

    # 1) Definitely check if this is working, the code generated was summing inside nested loops, that was expensive. This does a pre-sum at the deepest level (entry + cat2 + cat3) → faster than summing inside nested loops. Hence check if this is working, if not revert to the generated code. 
    deep = (d.groupby(entry_keys + ["cSubDesc2", "cSubDesc3", "cClient", "cProjDesc", "cProjMgr", "cClientDesc", "cMajorDesc", "cBookDesc"], dropna=False)[["rForecast", "rYearAct"]]
              .sum().reset_index())

    # 2) Build result
    result: Dict[str, List[Dict[str, Any]]] = {}
    for ek, g in deep.groupby(entry_keys, dropna=False):
        period_label, job_no, section, cost_type = ek
        cost_lines = []
        for cat2, g2 in g.groupby("cSubDesc2", dropna=False):
            children = [{
                "category": (safe_str(cat3) or safe_str(cat2)),
                "forecast_costs_at_completion": float(rf),
                "ytd_actual": float(ya),
            } for cat3, rf, ya in g2[["cSubDesc3", "rForecast", "rYearAct"]].itertuples(index=False, name=None)]

            cost_lines.append({
                "category": safe_str(cat2),
                "forecast_costs_at_completion": float(g2["rForecast"].sum()),
                "ytd_actual": float(g2["rYearAct"].sum()),
                "children": children,
            })

        entry = {
            "job_no": safe_str(job_no),
            "description": safe_str(_longest_nonempty(g['cProjDesc'])),
            "client": safe_str(_longest_nonempty(g["cClientDesc"])),
            "section": safe_str(section),
            "cost_type": safe_str(cost_type),
            "Total_forecast_costs_at_completion": float(sum(x["forecast_costs_at_completion"] for x in cost_lines)),
            "Total_ytd_actual": float(sum(x["ytd_actual"] for x in cost_lines)),
            "costLines": cost_lines,
        }
        result.setdefault(period_label, []).append(entry)

    return result


def preprocess_df_collapse_projects(df_all: pd.DataFrame, sum_col: str) -> pd.DataFrame:
    req = {"iProjNo_group", "iProjYear", "cProjDesc", "cClientDesc", sum_col}
    miss = req.difference(df_all.columns)
    if miss:
        raise KeyError(f"Missing required columns: {sorted(miss)}")

    df = df_all[["iProjNo_group", "iProjYear", "cProjDesc", "cClientDesc", sum_col]].copy()
    df[sum_col] = pd.to_numeric(df[sum_col], errors="coerce").fillna(0.0)

    return (df.groupby("iProjNo_group", dropna=False, sort=False)
              .agg(iProjYear=("iProjYear", _first_nonempty),
                   cProjDesc=("cProjDesc", _longest_nonempty),
                   cClientDesc=("cClientDesc", _longest_nonempty),
                   **{sum_col: (sum_col, "sum")})
              .reset_index()
              .rename(columns={"iProjNo_group": "iProjNo"}))


def combine_projects_rows(df: pd.DataFrame, project_groups: dict, key_cols=None, sum_cols=None) -> pd.DataFrame:
    if key_cols is None:
        key_cols = ["iProjYear", "cSegment", "cPeriod", "TYP", "cType"]

    # de-dupe key_cols
    key_cols = list(dict.fromkeys(key_cols))

    req = ["iProjNo"] + key_cols
    miss = [c for c in req if c not in df.columns]
    if miss:
        raise KeyError(f"Missing required columns in df: {miss}")

    out = df.copy()

    # map iProjNo -> group label
    proj_to_label = _normalize_project_groups(project_groups)
    out["iProjNo_int"] = pd.to_numeric(out["iProjNo"], errors="coerce").astype("Int64")
    out["iProjNo_group"] = out["iProjNo_int"].map(proj_to_label).fillna(out["iProjNo_int"].astype(str))

    group_cols = ["iProjNo_group"] + key_cols

    # normalize sum_cols
    if sum_cols is None:
        sum_cols = []
    elif isinstance(sum_cols, str):
        sum_cols = [sum_cols]

    def first_nonnull(s: pd.Series):
        s = s.dropna()
        return s.iloc[0] if len(s) else pd.NA

    agg = {c: "sum" for c in sum_cols if c in out.columns}
    for c in out.columns:
        if c in group_cols or c in agg or c == "iProjNo_int":
            continue
        agg[c] = first_nonnull

    combined = out.groupby(group_cols, dropna=False, as_index=False, sort=False).agg(agg)
    combined = combined[combined['cType'] == 'F']
    if combined.empty:
        return combined

    combined["cSubDesc2"] = combined["cSubDesc2"].replace("", pd.NA)
    combined["cSubDesc3"] = combined["cSubDesc3"].replace("", pd.NA).fillna(combined["cSubDesc2"])
    major = combined["cMajorDesc"].fillna("").astype(str)
    combined.loc[major.str.contains("variation", case=False, na=False), "TYP"] = "70 - Variations"
    combined = combined.loc[~combined["TYP"].fillna("").astype(str).str.contains("Revenue", case=False, na=False)].copy()

    text_cols = [c for c in ["cProjDesc", "cBookDesc", "cClientDesc", "cMainDesc", "cClient", "cBook", "cProjMgr"] if c in combined.columns]
    if text_cols:
        merged = (combined.groupby("iProjNo_group", dropna=False)[text_cols]
                          .transform(merge_or_longest))
        combined[text_cols] = merged

    return combined


def compute_forecast_diff(path_to_jsons: List[str], metric: str) -> Dict[str, Any]:
    if not isinstance(path_to_jsons, (list, tuple)) or len(path_to_jsons) != 2:
        raise ValueError("Provide exactly two JSON file paths: [path_file_1, path_file_2].")

    p1, p2 = path_to_jsons
    rows1, period1 = _load_rows(str(p1))
    rows2, period2 = _load_rows(str(p2))

    proj1 = _group_by_job(rows1)
    proj2 = _group_by_job(rows2)

    all_jobs = set(proj1.keys()) | set(proj2.keys())
    out: Dict[str, Any] = {"projects": {}}

    for job in sorted(all_jobs):
        items1 = proj1.get(job, [])
        items2 = proj2.get(job, [])

        total1 = sum(
            _to_number(r.get(f"Total_{metric}"))
            for r in items1
            if r.get("cost_type") and "revenue" not in str(r.get("cost_type")).lower()
        )
        total2 = sum(
            _to_number(r.get(f"Total_{metric}"))
            for r in items2
            if r.get("cost_type") and "revenue" not in str(r.get("cost_type")).lower()
        )

        # Unified aggregation (keeps cost_type -> parent -> child)
        total_ct1, parent_ct1, child_ct1 = aggregate_costlines_trajectory(items1, metric, exclude_revenue=True)
        total_ct2, parent_ct2, child_ct2 = aggregate_costlines_trajectory(items2, metric, exclude_revenue=True)

        description = _longest_nonempty([r.get("description") for r in items1 + items2]) or ""
        client = _longest_nonempty([r.get("client") for r in items1 + items2]) or ""

        # -----------------------------
        # B) Increases by MAIN COST TYPE  (cost_type totals)
        # -----------------------------
        cost_types = set(total_ct1.keys()) | set(total_ct2.keys())
        cost_type_blocks = []

        for ct in sorted(cost_types):
            c1 = total_ct1.get(ct, 0.0)
            c2 = total_ct2.get(ct, 0.0)

            # -----------------------------
            # A) Increases by PARENT under this cost type
            # -----------------------------
            parents1 = parent_ct1.get(ct, {}) or {}
            parents2 = parent_ct2.get(ct, {}) or {}
            parent_keys = set(parents1.keys()) | set(parents2.keys())

            parent_blocks = []
            for parent_cat in sorted(parent_keys):
                p1_val = parents1.get(parent_cat, 0.0)
                p2_val = parents2.get(parent_cat, 0.0)

                # -----------------------------
                # C) Increases by CHILD under this parent + cost type
                # -----------------------------
                kids1 = (child_ct1.get(ct, {}).get(parent_cat, {})) or {}
                kids2 = (child_ct2.get(ct, {}).get(parent_cat, {})) or {}
                child_keys = set(kids1.keys()) | set(kids2.keys())

                child_blocks = []
                for child_cat in sorted(child_keys):
                    v1_child = kids1.get(child_cat, 0.0)
                    v2_child = kids2.get(child_cat, 0.0)
                    child_blocks.append({
                        "category": child_cat,
                        "file1_metric": v1_child,
                        "file2_metric": v2_child,
                        "difference": v2_child - v1_child,
                    })

                parent_blocks.append({
                    "category": parent_cat,
                    "file1_metric": p1_val,
                    "file2_metric": p2_val,
                    "difference": p2_val - p1_val,
                    "children": sorted(child_blocks, key=lambda x: x["difference"], reverse=True),
                })

            cost_type_blocks.append({
                "category": ct,
                "file1_metric": c1,
                "file2_metric": c2,
                "difference": c2 - c1,
                "subcategories": sorted(parent_blocks, key=lambda x: x["difference"], reverse=True),
            })

        out["projects"][job] = {
            "project_meta": {
                "description": description,
                "client": client,
            },
            f"total_{metric}": {
                "period1": period1,
                "period2": period2,
                "file1": total1,
                "file2": total2,
                "difference": total2 - total1
            },

            "costline_increases_trajectory": sorted(
                cost_type_blocks, key=lambda x: x["difference"], reverse=True
            )
        }

    return out


def aggregate_costlines_trajectory(
    items: List[Dict[str, Any]],
    metric: str,
    exclude_revenue: bool = True,
) -> Tuple[
    Dict[str, float],                               # total_by_cost_type
    Dict[str, Dict[str, float]],                    # parent_by_cost_type
    Dict[str, Dict[str, Dict[str, float]]],         # child_by_cost_type[parent][child]
]:
    # 1) totals per cost type
    total_by_cost_type: Dict[str, float] = defaultdict(float)

    # 2) parent totals nested under cost type
    parent_by_cost_type: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))

    # 3) child totals nested cost_type -> parent -> child
    child_by_cost_type: Dict[str, Dict[str, Dict[str, float]]] = defaultdict(
        lambda: defaultdict(lambda: defaultdict(float))
    )

    for r in items:
        raw_cost_type = (r.get("cost_type") or "").strip()
        cost_type_lc = raw_cost_type.lower()

        if exclude_revenue and "revenue" in cost_type_lc:
            continue

        section = (r.get("section") or "")
        is_variation_section = "variation" in str(section).lower()

        bucket_cost_type = "70 - variations" if is_variation_section else raw_cost_type.lower() or "uncategorized"
        for cl in (r.get("costLines") or []):
            parent_cat = cl.get("category") if not pd.isna(cl.get("category")) else "Uncategorized"
            parent_fc = _to_number(cl.get(f"{metric}"))
            total_by_cost_type[bucket_cost_type] += parent_fc
            parent_by_cost_type[bucket_cost_type][parent_cat] += parent_fc

            for child in (cl.get("children") or []):
                child_cat = child.get("category") if not pd.isna(child.get("category")) else "Uncategorized"
                child_fc = _to_number(child.get(f"{metric}"))
                child_by_cost_type[bucket_cost_type][parent_cat][child_cat] += child_fc

    return (
        dict(total_by_cost_type),
        {ct: dict(parents) for ct, parents in parent_by_cost_type.items()},
        {ct: {p: dict(ch) for p, ch in parents.items()} for ct, parents in child_by_cost_type.items()}
    )


def hand_crafted_summary(EAC_cost_change, metric):
    parts = ""
    for job_no, proj in EAC_cost_change.items():
        desc = proj["project_meta"]["description"]
        total_diff = proj[f"total_{metric}"]["difference"]
        p1 = proj[f'total_{metric}']['period1']
        p2 = proj[f'total_{metric}']['period2']
        parts += f"Job No: {job_no}\nDescription: {desc}\nThe {metric} for {p1} is {proj[f'total_{metric}']['file1']/1000} million and for {p2} is {proj[f'total_{metric}']['file2']/1000} million\n"
        diff = "an increase" if total_diff >= 0 else "a decrease"
        parts += f"There is {diff} in the total {metric} from {p1} to {p2}: {total_diff/1000:,.2f} million\n\n"
        costlines_main = proj["costline_increases_trajectory"]

        for costline in costlines_main:

            cat = costline["category"]
            f1 = costline["file1_metric"]
            f2 = costline["file2_metric"]
            diff = costline["difference"]
            if diff == 0:
                continue
            change = "increase" if diff >= 0 else "decrease"
            parts += "Main Cost Type:\n"
            parts += f"  - {cat}: from {f1/1000:,.2f} million to {f2/1000:,.2f} million ({change} of {diff/1000:,.2f} million)\n\n"


            for subcostline in costline["subcategories"]:
                cat = subcostline["category"]
                f1 = subcostline["file1_metric"]
                f2 = subcostline["file2_metric"]
                diff = subcostline["difference"]
                if diff == 0:
                    continue
                change = "increase" if diff >= 0 else "decrease"
                parts += "Subcategory:\n"
                parts += f"  - {cat}: from {f1/1000:,.2f} million to {f2/1000:,.2f} million ({change} of {diff/1000:,.2f} million)\n\n"

                parts += f"Sub-sub Category of {cat}:\n"
                for subsubcostline in subcostline["children"]:
                    cat = subsubcostline["category"]
                    parent_cat = subcostline["category"]
                    f1 = subsubcostline["file1_metric"]
                    f2 = subsubcostline["file2_metric"]
                    diff = subsubcostline["difference"]
                    if diff == 0:
                        continue
                    change = "increase" if diff >= 0 else "decrease"
                    parts += f"  - {cat}: from {f1/1000:,.2f} million to {f2/1000:,.2f} million ({change} of {diff/1000:,.2f} million)\n\n"
    return parts
