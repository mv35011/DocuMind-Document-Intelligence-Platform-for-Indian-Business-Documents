from collections import defaultdict
from decimal import Decimal
from typing import Any, Dict, List, Optional, Set, Tuple
from documind.extraction.normalize import (
    normalize_date,
    normalize_identifier,
    normalize_indian_amount,
    normalize_whitespace,
)

try:
    from scipy.optimize import linear_sum_assignment
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False


def normalize_value_for_eval(key: str, val: Any) -> Any:
    """Normalizes predicted and ground truth values before metric comparison."""
    if val is None:
        return None

    lower_key = key.lower()
    if "date" in lower_key:
        d = normalize_date(val)
        return d.isoformat() if d else str(val).strip()

    if any(k in lower_key for k in ["total", "subtotal", "tax", "cgst", "sgst", "igst", "cess", "balance", "debit", "credit", "price", "amount", "value", "quantity"]):
        amt = normalize_indian_amount(val)
        return float(amt) if amt is not None else val

    if any(k in lower_key for k in ["gstin", "pan", "ifsc"]):
        return normalize_identifier(str(val))

    if isinstance(val, str):
        return normalize_whitespace(val.lower())

    return val


def values_match(gold_val: Any, pred_val: Any, key: str = "") -> bool:
    """Determines whether predicted and gold leaf values match."""
    g_norm = normalize_value_for_eval(key, gold_val)
    p_norm = normalize_value_for_eval(key, pred_val)

    if g_norm is None and p_norm is None:
        return True
    if g_norm is None or p_norm is None:
        return False

    if isinstance(g_norm, (int, float)) and isinstance(p_norm, (int, float)):
        return abs(g_norm - p_norm) <= 0.01

    return str(g_norm) == str(p_norm)


def flatten_leaf_fields(data: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
    """Flattens nested dictionaries into dotted paths for field-level comparison."""
    items: Dict[str, Any] = {}
    for k, v in data.items():
        if k in ["line_items", "transactions"]:
            # Handled separately by Hungarian matcher
            continue
        full_key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            items.update(flatten_leaf_fields(v, full_key))
        else:
            items[full_key] = v
    return items


def compute_field_metrics(
    gold_records: List[Dict[str, Any]],
    pred_records: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Computes field-level micro, macro, and per-field precision, recall, and F1."""
    per_field_tp = defaultdict(int)
    per_field_fp = defaultdict(int)
    per_field_fn = defaultdict(int)

    all_fields: Set[str] = set()

    for gold, pred in zip(gold_records, pred_records):
        g_flat = flatten_leaf_fields(gold)
        p_flat = flatten_leaf_fields(pred)

        keys = set(g_flat.keys()) | set(p_flat.keys())
        all_fields.update(keys)

        for k in keys:
            g_val = g_flat.get(k)
            p_val = p_flat.get(k)

            # Both null -> ignored
            if g_val is None and p_val is None:
                continue
            elif g_val is not None and p_val is None:
                per_field_fn[k] += 1
            elif g_val is None and p_val is not None:
                per_field_fp[k] += 1
            else:
                if values_match(g_val, p_val, k):
                    per_field_tp[k] += 1
                else:
                    per_field_fp[k] += 1
                    per_field_fn[k] += 1

    per_field_results = {}
    macro_f1_sum = 0.0

    total_tp = sum(per_field_tp.values())
    total_fp = sum(per_field_fp.values())
    total_fn = sum(per_field_fn.values())

    micro_p = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
    micro_r = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0
    micro_f1 = 2 * micro_p * micro_r / (micro_p + micro_r) if (micro_p + micro_r) > 0 else 0.0

    for f in sorted(all_fields):
        tp = per_field_tp[f]
        fp = per_field_fp[f]
        fn = per_field_fn[f]

        p = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        r = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * p * r / (p + r) if (p + r) > 0 else 0.0
        macro_f1_sum += f1

        per_field_results[f] = {
            "precision": round(p, 4),
            "recall": round(r, 4),
            "f1": round(f1, 4),
            "tp": tp,
            "fp": fp,
            "fn": fn,
        }

    macro_f1 = macro_f1_sum / len(all_fields) if all_fields else 0.0

    return {
        "micro_precision": round(micro_p, 4),
        "micro_recall": round(micro_r, 4),
        "micro_f1": round(micro_f1, 4),
        "macro_f1": round(macro_f1, 4),
        "per_field": per_field_results,
    }


def compute_hungarian_row_matching(
    gold_rows: List[Dict[str, Any]],
    pred_rows: List[Dict[str, Any]],
    key_fields: Tuple[str, str] = ("description", "taxable_value"),
) -> Dict[str, float]:
    """Matches line items / transaction rows using Hungarian algorithm on similarity."""
    if not gold_rows and not pred_rows:
        return {"precision": 1.0, "recall": 1.0, "f1": 1.0}
    if not gold_rows or not pred_rows:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0}

    # Build cost matrix
    cost_matrix = []
    for g in gold_rows:
        row_costs = []
        for p in pred_rows:
            # Simple similarity cost: 0.0 is perfect match, 1.0 is total mismatch
            desc_match = values_match(g.get("description"), p.get("description"), "description")
            amt_match = values_match(g.get(key_fields[1]), p.get(key_fields[1]), key_fields[1])
            cost = 1.0 - (0.5 * float(desc_match) + 0.5 * float(amt_match))
            row_costs.append(cost)
        cost_matrix.append(row_costs)

    matched_count = 0
    if HAS_SCIPY:
        row_ind, col_ind = linear_sum_assignment(cost_matrix)
        for r, c in zip(row_ind, col_ind):
            if cost_matrix[r][c] <= 0.5:  # At least one field matched
                matched_count += 1
    else:
        # Greedy fallback
        used_cols = set()
        for r in range(len(gold_rows)):
            best_col = -1
            best_cost = 0.5
            for c in range(len(pred_rows)):
                if c not in used_cols and cost_matrix[r][c] <= best_cost:
                    best_cost = cost_matrix[r][c]
                    best_col = c
            if best_col != -1:
                used_cols.add(best_col)
                matched_count += 1

    p = matched_count / len(pred_rows) if pred_rows else 0.0
    r = matched_count / len(gold_rows) if gold_rows else 0.0
    f1 = 2 * p * r / (p + r) if (p + r) > 0 else 0.0

    return {
        "item_precision": round(p, 4),
        "item_recall": round(r, 4),
        "item_f1": round(f1, 4),
    }
