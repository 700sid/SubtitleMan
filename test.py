from nltk.corpus import wordnet
import time
from PyDictionary import PyDictionary
import enchant


word = 'misogyny'

lang = enchant.Dict("en_US")
print(lang.check(word))

dictionary = PyDictionary()
print(dictionary.meaning(word))

meaning = wordnet.synsets(word)
a = [i.lemma_names() for i in meaning][0]
a = [i for i in a if i != word]
print(a)


meaning = wordnet.synsets(word)
a = [i.lemma_names() for i in meaning][0]
a = [i for i in a if i != word]
a = ', '.join(a[:3])
if a:
    new_word = f'{word}(: {a})'
else:
    new_word = word
print(new_word)
print(bool(new_word))

