import os
import json
import torch
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import uvicorn
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, LogitsProcessor, LogitsProcessorList
from peft import PeftModel

app = FastAPI(title="Gemma Hindi 300-Vocabulary constrained API")

# Global variables for model and processors
model = None
tokenizer = None
constraint_processor = None

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]
    temperature: Optional[float] = 0.1
    max_tokens: Optional[int] = 128

class ChatResponse(BaseModel):
    response: str
    vocabulary_check: str

# Custom LogitsProcessor to restrict token selection to allowed words
class VocabularyConstraintProcessor(LogitsProcessor):
    def __init__(self, allowed_token_ids, vocab_size):
        # Create a mask tensor on CPU first
        self.mask = torch.full((vocab_size,), float('-inf'))
        # Convert set of IDs to list
        allowed_list = list(allowed_token_ids)
        self.mask[allowed_list] = 0.0
        print(f"LogitsProcessor initialized. Allowed tokens: {len(allowed_list)} / Total vocab: {vocab_size}")

    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor) -> torch.FloatTensor:
        # Transfer mask to the same device as scores
        mask_device = self.mask.to(scores.device)
        # Apply mask
        return scores + mask_device

@app.on_event("startup")
def startup_event():
    global model, tokenizer, constraint_processor
    
    # Configuration
    model_id = os.environ.get("BASE_MODEL_ID", "google/gemma-2-2b-it")
    adapter_path = os.environ.get("ADAPTER_PATH", "./gemma-2b-hindi-lora")
    vocab_file = os.environ.get("VOCAB_PATH", "./hindi_vocab.json")
    load_in_4bit = os.environ.get("LOAD_IN_4BIT", "True").lower() == "true"
    
    print(f"Loading tokenizer for {model_id}...")
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    
    print(f"Loading vocabulary from {vocab_file}...")
    if not os.path.exists(vocab_file):
        raise FileNotFoundError(f"Vocabulary file not found at {vocab_file}. Please run generate_dataset.py first.")
    
    with open(vocab_file, "r", encoding="utf-8") as f:
        hindi_vocab = json.load(f)
    
    # 1. Compile list of allowed token IDs
    allowed_token_ids = set()
    
    # Include tokenizer special/control tokens to avoid breaking structure
    allowed_token_ids.update(tokenizer.all_special_ids)
    if tokenizer.pad_token_id is not None:
        allowed_token_ids.add(tokenizer.pad_token_id)
    if tokenizer.eos_token_id is not None:
        allowed_token_ids.add(tokenizer.eos_token_id)
    if tokenizer.bos_token_id is not None:
        allowed_token_ids.add(tokenizer.bos_token_id)
        
    # Standard spacing, newlines, and punctuation tokens
    punctuation = ["।", "?", ",", "!", ".", " ", "\n", "\n\n", " ", "  "]
    for p in punctuation:
        t_ids = tokenizer.encode(p, add_special_tokens=False)
        allowed_token_ids.update(t_ids)
        
    # Gemma specific chat template structural tokens (e.g. <start_of_turn>, <end_of_turn>, model, user)
    # We scan the vocabulary for any tags wrapped in < and >
    for token_str, token_id in tokenizer.get_vocab().items():
        if (token_str.startswith("<") and token_str.endswith(">")) or token_str in ["model", "user"]:
            allowed_token_ids.add(token_id)
            
    # Add token IDs for our 300 words
    for word in hindi_vocab:
        # Check both with and without leading space since tokenizers handle them differently
        for w in [word, " " + word]:
            t_ids = tokenizer.encode(w, add_special_tokens=False)
            allowed_token_ids.update(t_ids)
            
    # Initialize the custom LogitsProcessor
    constraint_processor = VocabularyConstraintProcessor(
        allowed_token_ids=allowed_token_ids,
        vocab_size=len(tokenizer)
    )
    
    # 2. Load the base model
    print(f"Loading base model {model_id}...")
    if load_in_4bit:
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=torch.float16
        )
        base_model = AutoModelForCausalLM.from_pretrained(
            model_id,
            quantization_config=bnb_config,
            device_map="auto",
            torch_dtype=torch.float16
        )
    else:
        base_model = AutoModelForCausalLM.from_pretrained(
            model_id,
            device_map="auto",
            torch_dtype=torch.float16
        )
        
    # 3. Load the LoRA adapter
    if os.path.exists(adapter_path):
        print(f"Applying adapter weights from {adapter_path}...")
        model = PeftModel.from_pretrained(base_model, adapter_path)
        print("Adapter weights loaded successfully.")
    else:
        print(f"Warning: Adapter path {adapter_path} not found. Running base model directly with constraints.")
        model = base_model
        
    model.eval()
    print("API Server Ready.")

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    if model is None or tokenizer is None or constraint_processor is None:
        raise HTTPException(status_code=503, detail="Model is not loaded yet.")
        
    try:
        # 1. Format input messages using Gemma chat template
        messages_dict = [{"role": m.role, "content": m.content} for m in request.messages]
        prompt = tokenizer.apply_chat_template(messages_dict, tokenize=False, add_generation_prompt=True)
        
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        prompt_length = inputs.input_ids.shape[1]
        
        # 2. Generate text with the custom LogitsProcessor
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=request.max_tokens,
                temperature=request.temperature,
                do_sample=request.temperature > 0,
                logits_processor=LogitsProcessorList([constraint_processor]),
                pad_token_id=tokenizer.pad_token_id or tokenizer.eos_token_id
            )
            
        # 3. Decode generated response only (exclude prompt tokens)
        generated_ids = outputs[0][prompt_length:]
        response_text = tokenizer.decode(generated_ids, skip_special_tokens=True).strip()
        
        # 4. Check if the response follows the 300 words rule
        # (This is a safety audit check to display in the API response)
        with open("./hindi_vocab.json", "r", encoding="utf-8") as f:
            hindi_vocab = set(json.load(f))
            
        # Clean response and verify
        cleaned_text = response_text.replace("।", " ").replace("?", " ").replace(",", " ").replace("!", " ")
        response_words = cleaned_text.split()
        invalid_words = [w for w in response_words if w not in hindi_vocab]
        
        vocab_check = "PASS" if len(invalid_words) == 0 else f"FAIL (Invalid words generated: {invalid_words})"
        
        return ChatResponse(
            response=response_text,
            vocabulary_check=vocab_check
        )
        
    except Exception as e:
        print(f"Error during generation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000)
