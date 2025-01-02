import json
import os
import pathlib
# 設定目錄路徑
data_dir = 'divided_data'
output_file = 'video_details.json'
# 用於存儲所有數據的列表
combined_data = []
# 遍歷目錄中的所有JSON檔案
for json_file in os.listdir(data_dir):
    if json_file.endswith('.json'):
        try:
            with open(os.path.join(data_dir, json_file), 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 如果讀取的是列表，則延伸；如果是字典，則添加
                if isinstance(data, list):
                    combined_data.extend(data)
                else:
                    combined_data.append(data)
            print(f"處理檔案 {json_file} 已完成")
        except Exception as e:
            print(f"處理檔案 {json_file} 時發生錯誤: {str(e)}")
# 將合併的數據寫入新檔案
try:
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(combined_data, f, ensure_ascii=False, indent=2)
    print(f"已成功將所有JSON檔案合併至 {output_file}")
except Exception as e:
    print(f"寫入檔案時發生錯誤: {str(e)}")