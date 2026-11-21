from eval.metrics import compute_field_metrics, compute_hungarian_row_matching, values_match


def test_values_match_money():
    assert values_match("1,23,456.50", "123456.50", "taxable_total") is True
    assert values_match(123456.50, 123456.505, "taxable_total") is True
    assert values_match(100.0, 105.0, "taxable_total") is False


def test_values_match_dates():
    assert values_match("15/02/2025", "2025-02-15", "invoice_date") is True
    assert values_match("15 Feb 2025", "2025-02-15", "invoice_date") is True
    assert values_match("2025-01-01", "2025-01-02", "invoice_date") is False


def test_compute_field_metrics_simple():
    gold = [
        {"invoice_number": "INV-01", "grand_total": 1000.0, "supplier": {"name": "Tata"}},
        {"invoice_number": "INV-02", "grand_total": 2000.0, "supplier": {"name": "Reliance"}},
    ]
    pred = [
        {"invoice_number": "INV-01", "grand_total": 1000.0, "supplier": {"name": "Tata"}},  # 3 TP
        {"invoice_number": "INV-02", "grand_total": 9999.0, "supplier": {"name": "Reliance"}},  # 2 TP, 1 FP/FN
    ]

    res = compute_field_metrics(gold, pred)
    # 5 TP, 1 FP, 1 FN -> precision = 5/6, recall = 5/6, f1 = 5/6
    assert res["micro_precision"] == round(5 / 6, 4)
    assert res["micro_recall"] == round(5 / 6, 4)
    assert res["micro_f1"] == round(5 / 6, 4)


def test_hungarian_row_matching():
    gold_rows = [
        {"description": "Item A", "taxable_value": 100.0},
        {"description": "Item B", "taxable_value": 200.0},
    ]
    pred_rows = [
        {"description": "Item B", "taxable_value": 200.0},
        {"description": "Item A", "taxable_value": 100.0},
    ]
    res = compute_hungarian_row_matching(gold_rows, pred_rows)
    assert res["item_f1"] == 1.0
    assert res["item_precision"] == 1.0
