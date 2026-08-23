import os
import torch
import argparse
from datasets import load_dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
    set_seed
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from trl import SFTTrainer, SFTConfig

def print_gpu_utilization():
    """Prints current GPU VRAM utilization."""
    if torch.cuda.is_available():
        allocated = torch.cuda.memory_allocated() / (1024 ** 3)
        reserved = torch.cuda.memory_reserved() / (1024 ** 3)
        print(f"GPU Memory Allocated: {allocated:.2f} GB | Reserved: {reserved:.2f} GB")
    else:
        print("No GPU available.")

def main():
    parser = argparse.ArgumentParser(description="QLoRA Fine-tuning of Gemma 2B for Hindi vocabulary restriction")
    parser.add_argument("--model_id", type=str, default="google/gemma-2-2b-it", help="Hugging Face model ID")
    parser.add_argument("--dataset_path", type=str, default="./dataset.jsonl", help="Path to dataset.jsonl")
    parser.add_argument("--output_dir", type=str, default="./gemma-2b-hindi-lora", help="Output directory for adapter weights")
    parser.add_argument("--epochs", type=int, default=3, help="Number of training epochs")
    parser.add_argument("--batch_size", type=int, default=4, help="Batch size per GPU")
    parser.add_argument("--lr", type=float, default=2e-4, help="Learning rate")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    
    args = parser.parse_args()
    set_seed(args.seed)
    
    print("Starting QLoRA Fine-Tuning Setup...")
    print_gpu_utilization()
    
    # 1. Load Dataset
    print(f"Loading dataset from {args.dataset_path}...")
    dataset = load_dataset("json", data_files=args.dataset_path, split="train")
    print(f"Loaded {len(dataset)} training examples.")
    
    # 2. Tokenizer Setup
    print(f"Loading tokenizer for {args.model_id}...")
    tokenizer = AutoTokenizer.from_pretrained(args.model_id)
    # Gemma tokenizer uses <bos> and <eos>, ensure pad token is set
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right" # Recommended for SFT Trainer to avoid warnings
    
    # 3. Apply Chat Template to Dataset
    def format_prompts(batch):
        formatted = []
        for messages in batch["messages"]:
            # Apply the standard Gemma template to user and assistant messages
            text = tokenizer.apply_chat_template(messages, tokenize=False)
            formatted.append(text)
        return {"text": formatted}
    
    print("Applying chat template formatting to the dataset...")
    dataset = dataset.map(format_prompts, batched=True, remove_columns=["messages"])
    print(f"Sample formatted instruction:\n{dataset[0]['text']}")
    
    # 4. BitsAndBytes Quantization Config
    print("Configuring 4-bit Quantization (NF4)...")
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
    )
    
    # 5. Load Model
    print(f"Loading base model {args.model_id} in 4-bit...")
    model = AutoModelForCausalLM.from_pretrained(
        args.model_id,
        quantization_config=bnb_config,
        device_map="auto", # Automatically distributes layer-by-layer across available GPUs
        torch_dtype=torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16,
    )
    
    # Prepare model for k-bit training (gradients, layer norm casting, etc.)
    model = prepare_model_for_kbit_training(model)
    
    # 6. Configure LoRA (PEFT)
    print("Setting up PEFT/LoRA configuration...")
    # Gemma models benefit from targeting all linear layers
    peft_config = LoraConfig(
        r=16,
        lora_alpha=32,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM"
    )
    
    # 7. SFT Trainer Setup
    print("Initializing SFTTrainer...")
    training_args = SFTConfig(
        output_dir=args.output_dir,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=2,
        optim="paged_adamw_8bit",
        logging_steps=10,
        learning_rate=args.lr,
        fp16=not torch.cuda.is_bf16_supported(),
        bf16=torch.cuda.is_bf16_supported(),
        max_grad_norm=0.3,
        warmup_ratio=0.03,
        lr_scheduler_type="cosine",
        save_strategy="epoch",
        evaluation_strategy="no",
        dataset_text_field="text",
        max_seq_length=512,
        packing=False,
        report_to="none" # Disable logging to WandB/Tensorboard for simple run
    )
    
    trainer = SFTTrainer(
        model=model,
        train_dataset=dataset,
        peft_config=peft_config,
        tokenizer=tokenizer,
        args=training_args
    )
    
    # 8. Run Training
    print("Starting training loop...")
    print_gpu_utilization()
    
    train_result = trainer.train()
    
    print("Training finished!")
    print_gpu_utilization()
    
    # Save adapter weights and tokenizer
    print(f"Saving fine-tuned adapter weights to {args.output_dir}...")
    trainer.model.save_pretrained(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)
    print("Saving completed.")
    
    # Code snippet to merge and save model (optional, commented out as PEFT loading is standard):
    """
    # To merge adapter and base model:
    from peft import PeftModel
    base_model = AutoModelForCausalLM.from_pretrained(
        args.model_id, 
        torch_dtype=torch.float16, 
        device_map="auto"
    )
    model_to_merge = PeftModel.from_pretrained(base_model, args.output_dir)
    merged_model = model_to_merge.merge_and_unload()
    merged_model.save_pretrained("./gemma-2b-hindi-merged")
    """

if __name__ == "__main__":
    main()
