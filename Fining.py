from transformers import AutoTokenizer, AutoModelForCausalLM

tokenizer = AutoTokenizer.from_pretrained("huggingface/llama-3.2")
model = AutoModelForCausalLM.from_pretrained("huggingface/llama-3.2")
