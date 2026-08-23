# Gemma QLoRA Hindi Vocabulary-Constrained Fine-Tuning

This repository contains the complete codebase to fine-tune a small Google Gemma model (`google/gemma-2-2b-it`) using **QLoRA** on a remote GPU instance (like RunPod). 

The goal of this fine-tuning is to build a model that converses in Hindi using **only a specific set of 300 simple Hindi words**. We implement a hybrid engineering approach:
1. **Supervised Fine-Tuning (SFT)**: Trains the model on a conversational dataset structured entirely using the 300 words. This teaches the model the grammar and conversational style.
2. **Logits Masking (At Inference)**: Uses a custom `LogitsProcessor` in FastAPI that mathematically restricts model output to only those 300 words, punctuation, and control tokens. This guarantees **100% compliance** with the vocabulary limit.

---

## File Structure

- `generate_dataset.py`: Python script to programmatically compile 300 words, generate verified conversation turns, and output files.
- `dataset.jsonl`: The output training dataset of 516 verified Hindi dialogue pairs.
- `hindi_vocab.json`: The reference JSON list of the 300 simple Hindi words.
- `train.py`: The QLoRA training script.
- `app.py`: FastAPI server that loads the model + adapter and serves the `/chat` endpoint with logits constraint.
- `requirements.txt`: Python package dependencies.

---

## RunPod GPU Setup Guide

### 1. Rent a GPU
1. Sign up on [RunPod.io](https://www.runpod.io/) and add billing credit (e.g. $5).
2. Go to the **Secure Cloud** or **Community Cloud**.
3. Choose a GPU instance with **at least 24 GB of VRAM**. Recommended:
   - **NVIDIA L4** (approx. $0.30 - $0.35 / hr)
   - **NVIDIA RTX 4090 / RTX 3090** (approx. $0.22 - $0.40 / hr)
4. Click **Deploy**. Under **Templates**, select the **RunPod PyTorch** template (includes PyTorch, CUDA, and Jupyter Lab).
5. Open the **Web Terminal** or connect via **SSH** / **Jupyter Lab**.

### 2. Prepare Code and Dependencies
Once connected to your RunPod instance, clone your files or upload them to a workspace folder (e.g. `/workspace/FineTuning`). Then run:

```bash
# Navigate to project folder
cd /workspace/FineTuning

# Install required python packages
pip install -r requirements.txt
```

### 3. Set Up Hugging Face Access
Gemma is a gated model. You must accept the license terms on the Hugging Face page for [google/gemma-2-2b-it](https://huggingface.co/google/gemma-2-2b-it) using your Hugging Face account.

Once accepted, get a User Access Token from HF settings and export it in your RunPod terminal:
```bash
export HF_TOKEN="your_hugging_face_token_here"
```

---

## Run Fine-Tuning

### 1. Generate / Verify the Dataset
If you make changes to the words or templates, run:
```bash
python generate_dataset.py
```
This generates:
- `dataset.jsonl` (training examples)
- `hindi_vocab.json` (vocab of exactly 300 words)

### 2. Start QLoRA Fine-Tuning
Run the training script on the GPU:
```bash
python train.py --epochs 3 --batch_size 4 --lr 2e-4
```
**What happens under the hood?**
- Loads the model `google/gemma-2-2b-it` in 4-bit precision.
- Configures LoRA adapters targeting all model linear projection layers.
- Prepares training data by wrapping dialogues in Gemma's chat template.
- Runs supervised fine-tuning (SFT) using `SFTTrainer`.
- Saves adapter weights to `./gemma-2b-hindi-lora/`.

---

## Start the API Server

Launch the FastAPI endpoint that hosts the fine-tuned model and implements the **Logits Masking Guardrail**:

```bash
python app.py
```
The server will start on port `8000`. It loads the base model in 4-bit, loads the LoRA adapter, tokenizes the allowed 300 words (including special control tokens like `<start_of_turn>`, `<end_of_turn>`), and builds the custom `LogitsProcessor`.

---

## How to Test the API

Open another terminal on your machine or inside the pod and execute a `curl` request:

```bash
curl -X POST "http://localhost:8000/chat" \
     -H "Content-Type: application/json" \
     -d '{
       "messages": [
         {"role": "user", "content": "नमस्ते, आप कैसे हैं?"}
       ],
       "temperature": 0.1,
       "max_tokens": 64
     }'
```

### Sample Response
```json
{
  "response": "मैं ठीक हूँ। आप कैसे हैं?",
  "vocabulary_check": "PASS"
}
```

*Note: The `vocabulary_check` field will print `PASS` if all generated words belong to the 300-word vocabulary, and will identify any invalid word if generated.*
