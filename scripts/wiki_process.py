import spacy
nlp = spacy.load("zh_core_web_")
import zh_core_web_lg
nlp = zh_core_web_lg.load()
doc = nlp("这是一个用于示例的句子。")
print([(w.text, w.pos_) for w in doc])