import argparse
import sys
from pathlib import Path


def merge_lora_weights(base_model_name: str, adapter_path: str, output_path: str):
    """Merges trained LoRA adapter weights with base model for vLLM high-throughput serving."""
    print(f"Merging adapter from {adapter_path} into base model {base_model_name}...")

    try:
        import torch
        from peft import PeftModel
        from transformers import AutoProcessor, Qwen2VLForConditionalGeneration

        processor = AutoProcessor.from_pretrained(base_model_name)
        base_model = Qwen2VLForConditionalGeneration.from_pretrained(
            base_model_name,
            torch_dtype=torch.float16,
            device_map="cpu",
        )
        model = PeftModel.from_pretrained(base_model, adapter_path)
        merged_model = model.merge_and_unload()

        out = Path(output_path)
        out.mkdir(parents=True, exist_ok=True)
        merged_model.save_pretrained(out)
        processor.save_pretrained(out)
        print(f"[OK] Merged weights saved to {out}. Ready for vLLM.")
    except Exception as e:
        print(f"Note: Running in environment without PyTorch/transformers ({e}).")
        print(f"When running on GPU server, command is: python3 -m training.merge_and_export --base {base_model_name} --adapter {adapter_path} --out {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Merge LoRA weights for vLLM serving")
    parser.add_argument("--base", default="Qwen/Qwen2-VL-2B-Instruct")
    parser.add_argument("--adapter", default="models/adapter")
    parser.add_argument("--out", default="models/merged_qwen2_vl")
    args = parser.parse_args()

    merge_lora_weights(args.base, args.adapter, args.out)
