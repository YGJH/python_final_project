import json


# def retrieve_relevant_documents(prompt):
#     # 讀取 video_details.json 文件
#     with open("video_details.json", "r", encoding="utf-8") as f:
#         video_details_list = json.load(f)

#     # 檢索邏輯：根據提示檢索相關的影片
#     relevant_docs = []
#     for video in video_details_list:
#         title = video.get('title', '')
#         description = video.get('description', '')
#         genre = video.get('genre', '')
#         actors = video.get('actors', [])

#         if (prompt in title or
#             prompt in description or
#             prompt in genre or
#                 any(prompt in actor for actor in actors)):
#             relevant_docs.append(video)

#     return relevant_docs

prompt = "我喜歡曾允凡"
with open("video_tetails.json", "r", encoding="utf-8") as f:
    video_details_list = json.load(f)

print(video_details_list[0].get('name'))
print(video_details_list[0].get('description'))
print(video_details_list[0].get('genre'))
# print(video_details_list[0].get('actors'))

# prompt 中是否包含一個子字串，該子字串在 actors 中的任何一個元素中
for actor in video_details_list[0].get('actors'):
    if actor in prompt:
        print(actor)
        break
