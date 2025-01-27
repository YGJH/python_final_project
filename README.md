CosyVoice 感覺這個聲音比較好，但是會生很久
然後預設是電影模式，有聊天模式跟av模式

# Install
```
conda create -n movie_recommender python==3.10
conda activate movie_recommender
pip install cython
conda install -c conda-forge pynini
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```
如果有錯可以自己去看cosyVoice的說明
然後pynini可能有指定版本，但我忘了
然後第一次要下載模型到pretrained_models，但如果下載爛掉就改版本號
```
pip install modelscope==1.17.0 -i https://pypi.tuna.tsinghua.edu.cn/simple
```
有問題請去把你的食指放進你的屁眼