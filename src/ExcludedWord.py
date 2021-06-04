import logging
import sqlite3
import os
import pathlib
import shutil
import PyDictionary


# default var
path_of_this_file = pathlib.Path(__file__).parent
conn_dict = sqlite3.connect(f'{path_of_this_file}/dictionary.db')
conn_common_word = sqlite3.connect(f'{path_of_this_file}/ExcludedWords.db')
dictionary = PyDictionary.PyDictionary()


# start afresh
def reset_common_word():
    os.remove(f'{path_of_this_file}/ExcludedWords.db')
    shutil.copy(f'{path_of_this_file}/archive/Excluded_Word.db', f'{path_of_this_file}/ExcludedWords.db')


# Return common words
def get_common_word():
    conn = sqlite3.connect(f'{path_of_this_file}/ExcludedWords.db')
    cursor = conn.cursor()
    words_sql = cursor.execute('select * from words')

    return [word[0] for word in words_sql.fetchall()]


# get definition
def get_meaning(word, next_iter=True, second_chance=True):
    cursor = conn_dict.cursor()
    meaning = cursor.execute(f'select definition from words where word="{word.title()}"')
    meanings = set()
    for i in meaning.fetchall():
        i = i[0]
        if next_iter and len(i.split()) == 2 and i.split()[0].lower() == 'of':
            niter = set(get_meaning(i.split()[1], False).split(';'))
            meanings = meanings | niter
        else:
            i = i.split(';')
            meanings.add(i[0])
    ans = '; '.join(list(meanings)[:3]) or 'Nan'
    if ans == 'Nan' and second_chance:
        ans = second_try_get_meaning(word)
    return ans or 'Nan'


# trying by changing meaning
def second_try_get_meaning(word):
    if word.endswith('ing'):
        return get_meaning(word[:-3], second_chance=False)
    elif word.endswith('s'):
        return get_meaning(word[:-1], second_chance=False)
    elif word.endswith('es'):
        return get_meaning(word[:-2], second_chance=False)
    elif word.endswith('r'):
        return get_meaning(word[:-1], second_chance=False)
    elif word.endswith('ly'):
        return get_meaning(word[:-2], second_chance=False)
    elif word.endswith('ed'):
        return get_meaning(word[:-2], second_chance=False)
    else:
        return 'Nan'


# get definition from PyDictionary slow but effective
def get_meaning_pydict(word):
    return list(dictionary.meaning(word).values())[0][:1]


# insert word
def update_dictionary(word, meaning):
    try:
        val = conn_dict.execute(f'select definition from words where definition="{meaning}"').fetchall()
        if not val:
            conn_dict.execute(f'insert into words values(?, ?)', (word.title(), meaning))
            conn_dict.commit()
        else:
            print("Already there")
    except Exception as ex:
        logging.error(f'{ex} in update_dictionary')


# add word in exclude
def add_to_exclude(word):
    try:
        a = conn_common_word.execute(f'select * from words where word="{word.lower()}"').fetchall()
        if not a:
            conn_common_word.execute(f'insert into words values ("{word.lower()}")')
            conn_common_word.commit()
        else:
            print(f'{word} already in there')
            logging.info(f'{word} already in there :- in fun add_to_search')
    except Exception as ex:
        logging.error(f'{ex} in add_to_search')


# remove from exclude for showing in file
def remove_from_exclude(word):
    try:
        conn_common_word.execute(f'delete from words where word="{word.lower()}"')
        conn_common_word.commit()
    except Exception as ex:
        logging.error(f'{ex} in remove from dict')


if __name__ == '__main__':
    pass
    # reset_common_word()
    # Zythum A kind of ancient malt beverage; a liquor made from malt\n and wheat.
    # update_dictionary('chocolates', 'of chocolate')
    print(get_meaning('eat'))
