import json


with open('video_details.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    movies = []
    for movie in data:
        tmp = movie.get('description', 'N/A')
        try:
            name , des = tmp.split('電影線上看，')[0], tmp.split('電影線上看，')[1]
        except:
            print(tmp)
            continue


        movie['name'] = name
        if '。friday影音新上架' in des:
            des = des.split('。friday影音新上架')[0]
        movie['description'] = des
        movies.append(movie)
        # print(movies)
    with open('video_tetails.json', 'w', encoding='utf-8') as f:
        json.dump(movies, f, ensure_ascii=False, indent=4)
        print('done')

