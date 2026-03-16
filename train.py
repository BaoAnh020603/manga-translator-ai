import os
import pandas as pd
import torch
from datasets import Dataset
from transformers import (
    AutoModelForSeq2SeqLM, 
    AutoTokenizer, 
    Seq2SeqTrainingArguments, 
    Seq2SeqTrainer,
    DataCollatorForSeq2Seq
)

print("============ TRỢ LÝ HUẤN LUYỆN AI MANGATRANSLATOR ============")
print("Đang nạp dữ liệu từ thư mục 'dataset/manga_vocab.csv'...")

try:
    df = pd.read_csv("dataset/manga_vocab.csv")
    if "English" not in df.columns or "Vietnamese" not in df.columns:
        raise ValueError("File CSV của bạn phải có 2 cột tên là: 'English' và 'Vietnamese'")
        
    print(f"Đã tìm thấy {len(df)} câu dữ liệu của bạn để dạy cho AI!")
except Exception as e:
    print(f"Lỗi đọc file dữ liệu: {e}")
    exit(1)

# Chuyển đổi Pandas sang bộ Dataset chuẩn của HuggingFace
dataset = Dataset.from_pandas(df)

# Khởi tạo mô hình dịch thuật Gốc (Base Model)
model_checkpoint = "Helsinki-NLP/opus-mt-en-vi"
print(f"Đang tải não bộ gốc '{model_checkpoint}' để chuẩn bị nâng cấp...")

tokenizer = AutoTokenizer.from_pretrained(model_checkpoint)
model = AutoModelForSeq2SeqLM.from_pretrained(model_checkpoint)

max_input_length = 64
max_target_length = 64

def preprocess_function(examples):
    # Đọc cột Tiếng Anh
    inputs = [ex for ex in examples["English"]]
    # Đọc cột Tiếng Việt
    targets = [ex for ex in examples["Vietnamese"]]
    
    # Mã hóa (Mã hóa văn bản thành mảng các con số ma trận cho AI hiểu)
    model_inputs = tokenizer(inputs, max_length=max_input_length, truncation=True)
    
    # Mã hóa nhãn (Câu trả lời mẫu)
    labels = tokenizer(targets, max_length=max_target_length, truncation=True)
    model_inputs["labels"] = labels["input_ids"]
    return model_inputs

print("Đang mã hóa dữ liệu văn bản sang số học ma trận...")
tokenized_datasets = dataset.map(preprocess_function, batched=True)

# Chia tỉ lệ: Lấy 1 phần nhỏ làm bài kiểm tra (evaluation), còn lại lấy hết làm bài giảng (train)
# Do dữ liệu ví dụ đang rất nhỏ nên cứ để 10% test. Sau này file của bạn có hàng ngàn câu thì 10% sẽ nhiều hơn.
split_dataset = tokenized_datasets.train_test_split(test_size=0.1)

# Setup DataCollator: Tự động gom câu ngắn câu dài cho bằng nhau
data_collator = DataCollatorForSeq2Seq(tokenizer, model=model)

# CẤU HÌNH HUẤN LUYỆN DÀNH CHO CPU YẾU (LOW-END PC)
print("Đang thiết lập thông số siêu tiết kiệm RAM...")

batch_size = 2 # Chậm mà chắc: Nhét 2 câu vào não 1 lần để không tràn RAM 8GB.
output_dir = "models/my_custom_ai"

args = Seq2SeqTrainingArguments(
    output_dir=output_dir,
    evaluation_strategy="epoch", # Cuối mỗi bài giảng nghỉ ngơi 1 xíu làm kiểm tra
    learning_rate=2e-5,          # Độ ngu học (2e-5 là chậm tiêu tốn thời gian nhưng học rất kĩ)
    per_device_train_batch_size=batch_size, 
    per_device_eval_batch_size=batch_size,
    weight_decay=0.01,           # Tránh tình trạng AI bị học vẹt
    save_total_limit=1,          # Chỉ lưu đúng 1 não cuối cùng xuất sắc nhất để nhẹ ổ cứng
    num_train_epochs=3,          # Cho AI đọc đi đọc lại quyển sách 3 lần. (Sau này muốn xịn bạn điền lên 10-20 lần)
    predict_with_generate=True,
    use_cpu=True,                # ÉP CHẠY BẰNG CPU vì máy không có Card rời NVIDIA.
    dataloader_pin_memory=False, # Tránh cảnh báo lỗi vặt.
    log_level="error"            # Bớt spam log thừa mứa
)

trainer = Seq2SeqTrainer(
    model=model,
    args=args,
    train_dataset=split_dataset["train"],
    eval_dataset=split_dataset["test"],
    data_collator=data_collator,
    tokenizer=tokenizer,
)

print("")
print("=================== BẮT ĐẦU QUÁ TRÌNH HUẤN LUYỆN ===================")
print("Cảnh báo: Tốc độ sẽ bị phụ thuộc vào CPU. Máy sẽ quạt kêu hơi to. Đừng lo lắng!")
trainer.train()

print("")
print("=================== XUẤT XƯỞNG MÔ HÌNH ===================")
print(f"Đang lưu 'Não Bộ Độc Quyền' của bạn vào thư mục: {output_dir}")
trainer.save_model(output_dir)
print("Hoàn tất! Giờ bạn có thể khởi động lại server.py. Máy sẽ tự động lấy Não này ra xài (My Custom AI) thay vì con cũ!")
