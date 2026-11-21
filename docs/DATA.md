# Data Strategy & Dataset Governance

This document describes the data sources, synthetic generation process, dataset splitting strategy, and privacy safeguards for DocuMind.

---

## 1. Supported Document Types

| Document Type | Key | Primary Source | Validation Constraints |
|---|---|---|---|
| **GST Tax Invoice** | `gst_invoice` | Synthetic Generator (`datagen/`) + Hand-labeled test set | Base-36 GSTIN checksum, CGST+SGST=IGST state consistency, line math |
| **Bank Statement** | `bank_statement` | Synthetic Generator (`datagen/`) + Hand-labeled test set | Running balance continuity, period opening/closing balance reconciliation |
| **Retail Receipt** | `receipt` | Public Datasets (SROIE, CORD) + Synthetic | Subtotal + tax == total, vendor presence |

---

## 2. Synthetic Generator Architecture (`datagen/`)

To protect privacy and avoid leaking sensitive customer PII, training datasets are synthetically generated:
- **Reproducibility**: Parameterized with fixed seeds and emitted with ground-truth JSON labels.
- **Indian Localization**: Utilizes `Faker('en_IN')` for realistic vendor names, addresses, and PIN codes.
- **Valid Financial Identifiers**:
  - Valid Indian GSTINs generated with mathematically compliant Base-36 check digits.
  - Realistic PAN numbers, HSN/SAC codes (textiles, electronics, FMCG, logistics).
  - Indian currency grouping (`1,23,456.50`) and realistic transaction narration lines (`UPI`, `NEFT`, `IMPS`, `ATM`).
- **Layout Diversity**: 6 Jinja2 HTML invoice templates and 4 bank statement templates compiled via WeasyPrint to PDF and rendered to PNG at 200 DPI.
- **Visual Degradation**: Mild to harsh OpenCV/Albumentations augmentations (perspective warp, gaussian noise, blur, shadows).

---

## 3. Dataset Splitting Strategy (Zero Layout Leakage)

Splitting randomly on synthetic documents causes models to memorize visual coordinates rather than learning spatial relations. DocuMind splits **by layout template**:

- **`train`**: Templates T1, T2, T3, T4 (Seed Set A).
- **`val`**: Templates T1, T2, T3, T4 (Seed Set B).
- **`test_seen`**: Templates T1, T2, T3, T4 (Seed Set C).
- **`test_unseen`**: Templates T5 and T6 (Layouts never seen during training).
- **`test_real`**: 100+ real documents with hand-verified labels.

---

## 4. Privacy & Compliance

- **Zero Real PII Committed**: Real corporate documents and customer identifiers are never checked into git.
- **Masking**: Bank account numbers are masked to last 4 digits (`account_number_last4`).
- **Logs**: JSON structlog processor masks account and tax numbers before stdout.
