import json
import torch
import os
from huggingface_hub import login
try:
    from sklearn.model_selection import train_test_split
except ImportError:
    raise ImportError(
        "請先安裝 scikit-learn: pip install scikit-learn"
    )
from torch.utils.data import Dataset, DataLoader
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    BitsAndBytesConfig
)
from huggingface_hub import snapshot_download
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

def check_cuda():
    """檢查 CUDA 是否可用"""
    if not torch.cuda.is_available():
        print("警告: CUDA 不可用，將使用 CPU 進行訓練")
        return False
    print(f"使用 CUDA 設備: {torch.cuda.get_device_name(0)}")
    return True

class VideoDataset(Dataset):
    def __init__(self, data, tokenizer, max_length=512):
        self.data = data
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        video = self.data[idx]
        
        # 構建輸入文本
        input_text = f"""<s>[INST] 請根據以下影片資訊生成推薦理由：

標題：{video.get('title', '')}
演員：{', '.join(video.get('models', [])) if video.get('models') else '未知'}
標籤：{', '.join(video.get('tags', [])) if video.get('tags') else '無標籤'}
觀看次數：{video.get('views', '0')}
評分：{video.get('rating', '0')} [/INST]

這部影片非常推薦！以下是具體原因：
{video.get('recommendation', '')} </s>"""

        # 對文本進行編碼
        encoding = self.tokenizer(
            input_text,
            max_length=self.max_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt"
        )

        return {
            "input_ids": encoding["input_ids"].squeeze(),
            "attention_mask": encoding["attention_mask"].squeeze(),
            "labels": encoding["input_ids"].squeeze()
        }

def download_model():
    """下載 Mistral 模型"""
    print("正在下載 Mistral 模型...")
    model_path = snapshot_download(
        repo_id="mistralai/Mistral-7B-v0.1",
        local_dir="./mistral-7b-v0.1",
        ignore_patterns=["*.md", "*.txt"]
    )
    return model_path

def init_model():
    model_path = "./mistral-7b-v0.1"
    if not os.path.exists(model_path) or not any(
        os.path.exists(os.path.join(model_path, f))
        for f in ["pytorch_model.bin", "model.safetensors"]
    ):
        model_path = download_model()
    
    print(f"使用模型路徑: {model_path}")
    
    # 初始化模型配置 - 優化 CUDA 設定
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
    )
    
    # 載入模型 - 設定 CUDA 參數
    print("載入模型中...")
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        quantization_config=bnb_config,
        device_map="cuda:0" if torch.cuda.is_available() else "auto",
        trust_remote_code=True,
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
    )
    
    print("載入 tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    
    return model, tokenizer

def train_model(training_data):
    """訓練模型"""
    # 檢查 CUDA
    use_cuda = check_cuda()
    
    # 分割訓練集和驗證集
    train_data, val_data = train_test_split(training_data, test_size=0.1, random_state=42)
    
    print("初始化 Ollama Mistral 模型...")
    model, tokenizer = init_model()
    tokenizer.pad_token = tokenizer.eos_token
    
    # 準備模型進行訓練
    model = prepare_model_for_kbit_training(model)
    
    # 配置 LoRA 參數 - 針對 Mistral 模型調整
    peft_config = LoraConfig(
        r=4,  # 降低 rank
        lora_alpha=8,
        lora_dropout=0.1,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=[
            "q_proj",
            "v_proj",
        ]
    )
    
    model = get_peft_model(model, peft_config)
    
    # 創建數據集
    train_dataset = VideoDataset(train_data, tokenizer)
    val_dataset = VideoDataset(val_data, tokenizer)
    
    # 訓練參數 - 優化 CUDA 設定
    training_args = TrainingArguments(
        output_dir="video_recommender_model",
        num_train_epochs=1,
        per_device_train_batch_size=2 if use_cuda else 1,  # CUDA 可用時增加批次大小
        gradient_accumulation_steps=8 if use_cuda else 16,  # CUDA 可用時減少梯度累積步數
        learning_rate=2e-4 if use_cuda else 1e-4,
        weight_decay=0.05,
        max_grad_norm=0.3,
        warmup_ratio=0.03,
        evaluation_strategy="steps",
        eval_steps=50 if use_cuda else 100,
        save_strategy="steps",
        save_steps=50 if use_cuda else 100,
        save_total_limit=2,
        logging_steps=10,
        report_to="none",
        fp16=use_cuda,  # 只在 CUDA 可用時使用 fp16
        optim="adamw_torch",
        gradient_checkpointing=True,
        log_level="info",
        no_cuda=not use_cuda  # 控制是否使用 CUDA
    )
    
    # 訓練器
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        tokenizer=tokenizer,
    )
    
    print("開始訓練...")
    trainer.train()
    
    print("保存模型...")
    trainer.save_model("video_recommender_model/final")
    
    return model, tokenizer

def setup_huggingface():
    """設定 Hugging Face 認證"""
    token = os.getenv("HUGGINGFACE_TOKEN")
    if not token:
        # 如果環境變數中沒有 token，提示用戶輸入
        token = input("請輸入你的 Hugging Face token: ")
    login(token)  # 登入 Hugging Face

if __name__ == "__main__":
    # 設定 Hugging Face 認證
    setup_huggingface()
    
    # 設定 CUDA 設備
    torch.cuda.set_device(0) if torch.cuda.is_available() else None
    
    # 從 JSON 文件加載訓練數據
    with open("video_details.json", "r", encoding="utf-8") as f:
        training_data = json.load(f)
    
    # 訓練模型
    model, tokenizer = train_model(training_data)
