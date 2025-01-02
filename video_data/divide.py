import json
import os
import math

def divide_json_file():
    # 建立資料夾
    output_dir = "divided_data"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 計算現有檔案數量
    existing_files = [f for f in os.listdir(output_dir) if f.endswith('.json')]
    start_num = len(existing_files)
    
    # 讀取原始 JSON 檔案
    with open("video_details.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # 計算需要分割的檔案數量
    chunk_size = 15
    num_files = math.ceil(len(data) / chunk_size)
    
    # 分割並儲存
    for i in range(num_files):
        start_idx = i * chunk_size
        end_idx = min((i + 1) * chunk_size, len(data))
        chunk_data = data[start_idx:end_idx]
        
        output_file = os.path.join(output_dir, f"video_details_{start_num + i + 1}.json")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(chunk_data, f, ensure_ascii=False, indent=2)
        
        print(f"已創建檔案: {output_file} (包含 {len(chunk_data)} 筆資料)")

if __name__ == "__main__":
    divide_json_file()