import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict, List
from documind.extraction.prompts import SYSTEM_EXTRACTION_PROMPT, build_user_prompt


def format_chat_vlm_example(
    image_path: str,
    doc_type: str,
    gold_payload: Dict[str, Any],
) -> Dict[str, Any]:
    """Formats an example into Qwen2-VL chat completion format."""
    # Canonical compact JSON with sorted keys and null-discipline
    assistant_json_str = json.dumps(gold_payload, sort_keys=True, separators=(",", ":"))

    user_prompt = build_user_prompt(doc_type)

    return {
        "messages": [
            {
                "role": "system",
                "content": SYSTEM_EXTRACTION_PROMPT,
            },
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": image_path},
                    {"type": "text", "text": user_prompt},
                ],
            },
            {
                "role": "assistant",
                "content": assistant_json_str,
            },
        ]
    }


def build_split_datasets(manifest_path: str, output_dir: str):
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    splits: Dict[str, List[Dict[str, Any]]] = {
        "train": [],
        "val": [],
        "test_seen": [],
        "test_unseen": [],
    }

    if os.path.exists(manifest_path):
        with open(manifest_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                record = json.loads(line)
                split_name = record.get("split", "train")
                example = format_chat_vlm_example(
                    image_path=record["image_path"],
                    doc_type=record["doc_type"],
                    gold_payload=record["gold"],
                )
                if split_name in splits:
                    splits[split_name].append(example)
    else:
        # Generate starter mock dataset for testing pipeline
        mock_examples = [
            ("data/images/inv_01.png", "gst_invoice", {"doc_type": "gst_invoice", "invoice_number": "INV-01", "grand_total": 1180.0}, "train"),
            ("data/images/inv_02.png", "gst_invoice", {"doc_type": "gst_invoice", "invoice_number": "INV-02", "grand_total": 2360.0}, "train"),
            ("data/images/inv_val.png", "gst_invoice", {"doc_type": "gst_invoice", "invoice_number": "INV-VAL", "grand_total": 5900.0}, "val"),
            ("data/images/inv_test.png", "gst_invoice", {"doc_type": "gst_invoice", "invoice_number": "INV-TEST", "grand_total": 10000.0}, "test_unseen"),
        ]
        for img, dtype, gold, sp in mock_examples:
            splits[sp].append(format_chat_vlm_example(img, dtype, gold))

    for split_name, examples in splits.items():
        split_file = out / f"{split_name}.jsonl"
        with open(split_file, "w", encoding="utf-8") as f:
            for ex in examples:
                f.write(json.dumps(ex) + "\n")
        print(f"Wrote {len(examples)} examples to {split_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build training datasets for Qwen2-VL")
    parser.add_argument("--manifest", default="data/manifest.jsonl")
    parser.add_argument("--output", default="data/training")
    args = parser.parse_args()

    build_split_datasets(args.manifest, args.output)
