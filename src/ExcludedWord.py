import logging
import sqlite3
import os
import pathlib
import shutil


# default var
path_of_this_file = pathlib.Path(__file__).parent
conn_dict = sqlite3.connect(f'{path_of_this_file}/dictionary.db')
conn_common_word = sqlite3.connect(f'{path_of_this_file}/ExcludedWords.db')


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
def get_meaning(word):
    cursor = conn_dict.cursor()
    meaning = cursor.execute(f'select definition from words where word="{word.title()}"')
    meanings = []
    for i in meaning.fetchall():
        i = i[0]
        if len(i.split()) == 2 and i.split()[0].lower() == 'of':
            meanings.append(get_meaning(i.split()[1]))
        else:
            i = i.split(';')
            meanings.append(i[0])
    ans = '; '.join(meanings[:3])

    return ans or 'Not in Dictionary, Please add'


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
        conn_common_word.execute(f'delete from words where word="{word.lower}"')
        conn_common_word.commit()
    except Exception as ex:
        logging.error(f'{ex} in remove from dict')


if __name__ == '__main__':
    pass
    # reset_common_word()
    # Zythum A kind of ancient malt beverage; a liquor made from malt\n and wheat.
    # update_dictionary('chocolates', 'of chocolate')
    print(get_meaning('chocolate'))
