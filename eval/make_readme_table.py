import json
from pathlib import Path


def generate_results_table(reports_dir: str = "reports") -> str:
    reports_path = Path(reports_dir)
    if not reports_path.exists():
        return "*No benchmark reports generated yet. Run `make eval-extraction`.*"

    # Find the latest metrics.json for each backend
    backend_latest: dict[str, dict] = {}

    for metrics_file in sorted(reports_path.glob("*/metrics.json")):
        try:
            with open(metrics_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                backend = data.get("backend", "unknown")
                backend_latest[backend] = data
        except Exception:
            continue

    if not backend_latest:
        return "*No completed benchmark runs found.*"

    table_lines = [
        "| Model ID | System Description | Micro F1 | Macro F1 | Latency (p50) | Status |",
        "|---|---|---|---|---|---|",
    ]

    backend_labels = {
        "stub": ("STUB", "Test Fixture Baseline (CI)"),
        "regex": ("B0", "OCR + Regex & Heuristics"),
        "ocr_llm": ("B1", "OCR + Groq Llama-3.3 70B"),
        "vlm_prompted": ("V0", "Prompted Qwen2-VL-2B (Zero-Shot)"),
        "vlm_finetuned": ("M1", "Fine-Tuned Qwen2-VL-2B (4-bit QLoRA)"),
    }

    for b_id, (label, desc) in backend_labels.items():
        if b_id in backend_latest:
            m = backend_latest[b_id]
            f1 = f"{m.get('micro_f1', 0.0) * 100:.1f}%"
            macro = f"{m.get('macro_f1', 0.0) * 100:.1f}%"
            lat = f"{m.get('avg_latency_ms', 0):.0f} ms"
            status = "Verified"
        else:
            f1, macro, lat, status = "--", "--", "--", "Pending GPU Run"

        table_lines.append(f"| **{label}** | {desc} | {f1} | {macro} | {lat} | {status} |")

    return "\n".join(table_lines)


if __name__ == "__main__":
    table = generate_results_table()
    print(table)
