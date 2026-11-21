# DocuMind Extraction Benchmark Report: `stub`

- **Run ID**: `eval_stub_20261121_122550`
- **Timestamp**: 2026-11-21T12:25:50.965208
- **Sample Count**: 4
- **Average Latency**: 0.0 ms/page

## Headline Metrics

| Metric | Score |
|---|---|
| **Micro Precision** | 47.83% |
| **Micro Recall** | 73.33% |
| **Micro F1** | **57.89%** |
| **Macro F1** | 55.56% |

## Per-Field Breakdown

| Field Path | Precision | Recall | F1 Score | TP | FP | FN |
|---|---|---|---|---|---|---|
| `account_holder` | 1.000 | 1.000 | 1.000 | 1 | 0 | 0 |
| `account_number_last4` | 1.000 | 1.000 | 1.000 | 1 | 0 | 0 |
| `bank_name` | 1.000 | 1.000 | 1.000 | 1 | 0 | 0 |
| `buyer.gstin` | 0.000 | 0.000 | 0.000 | 0 | 2 | 0 |
| `buyer.name` | 0.000 | 0.000 | 0.000 | 0 | 2 | 0 |
| `buyer.state_code` | 0.000 | 0.000 | 0.000 | 0 | 2 | 0 |
| `cgst` | 0.500 | 0.500 | 0.500 | 1 | 1 | 1 |
| `closing_balance` | 1.000 | 1.000 | 1.000 | 1 | 0 | 0 |
| `currency` | 0.000 | 0.000 | 0.000 | 0 | 2 | 0 |
| `date` | 1.000 | 1.000 | 1.000 | 1 | 0 | 0 |
| `doc_type` | 1.000 | 1.000 | 1.000 | 4 | 0 | 0 |
| `grand_total` | 0.500 | 0.500 | 0.500 | 1 | 1 | 1 |
| `igst` | 0.000 | 0.000 | 0.000 | 0 | 2 | 0 |
| `invoice_date` | 0.500 | 0.500 | 0.500 | 1 | 1 | 1 |
| `invoice_number` | 0.500 | 0.500 | 0.500 | 1 | 1 | 1 |
| `opening_balance` | 1.000 | 1.000 | 1.000 | 1 | 0 | 0 |
| `place_of_supply` | 0.000 | 0.000 | 0.000 | 0 | 2 | 0 |
| `sgst` | 0.500 | 0.500 | 0.500 | 1 | 1 | 1 |
| `subtotal` | 1.000 | 1.000 | 1.000 | 1 | 0 | 0 |
| `supplier.gstin` | 0.500 | 0.500 | 0.500 | 1 | 1 | 1 |
| `supplier.name` | 0.500 | 0.500 | 0.500 | 1 | 1 | 1 |
| `supplier.pan` | 0.000 | 0.000 | 0.000 | 0 | 2 | 0 |
| `supplier.state_code` | 0.000 | 0.000 | 0.000 | 0 | 2 | 0 |
| `tax` | 1.000 | 1.000 | 1.000 | 1 | 0 | 0 |
| `taxable_total` | 0.500 | 0.500 | 0.500 | 1 | 1 | 1 |
| `total` | 1.000 | 1.000 | 1.000 | 1 | 0 | 0 |
| `vendor_name` | 1.000 | 1.000 | 1.000 | 1 | 0 | 0 |
