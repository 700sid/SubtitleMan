import PySimpleGUI as sg
import logging
import sqlite3
import os
import pathlib
import shutil
import PyDictionary
import requests
import json


# default var
path_of_this_file = pathlib.Path(__file__).parent  # for avoiding location change during called from outside folder
conn_dict = sqlite3.connect(f'{path_of_this_file}/dictionary.db')  # Our offline dictionary
conn_common_word = sqlite3.connect(f'{path_of_this_file}/ExcludedWords.db')  # Most common words dictionary
dictionary = PyDictionary.PyDictionary()  # Offline dictionary


# start afresh reset common word
def reset_common_word():
    os.remove(f'{path_of_this_file}/ExcludedWords.db')
    shutil.copy(f'{path_of_this_file}/archive/Excluded_Word.db', f'{path_of_this_file}/ExcludedWords.db')


# Return common words
def get_common_word():
    cursor = conn_common_word.cursor()
    words_sql = cursor.execute('select * from words')

    return [word[0] for word in words_sql.fetchall()]


# get definition
def get_meaning(word, next_iter=True, second_chance=True):
    if word.lower() == 'word':
        # local dictionary returning everythi
        return ['The spoken sign of a conception or an idea;']

    cursor = conn_dict.cursor()
    meaning = cursor.execute(f'select definition from words_ where word="{word.title()}"')
    meanings = set()
    for i in meaning.fetchall():
        i = i[0]
        if next_iter and len(i.split()) == 2 and i.split()[0].lower() == 'of':
            # In local dictionary some word has meaning like {'Abandoned': 'of Abandon'}
            # So this if block help us in getting meaning of word after "of"
            niter = set(get_meaning(i.split()[1], next_iter=False).split(';'))
            # next_iter=False parameter helps from going in infinite recursion
            meanings = meanings | niter  # Union meaning in set
        else:
            i = i.split(';')
            meanings.add(i[0])
    ans = '; '.join(list(meanings)) or 'Nan'
    if ans == 'Nan' and second_chance:
        # If don't find answer we gave it a second chance by overcoming some flaws of Offline Dictionary
        ans = second_try_get_meaning(word)
    return ans or 'Nan'


# trying by changing meaning
def second_try_get_meaning(word):
    # addressing some flaws of offline dictionary
    # second_chance=False parameter secure us from infinite recursion
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
    # Get Meaning from a online dictionary Supported by Package PyDictionary
    # TODO: That one is too slow try other API
    return list(dictionary.meaning(word).values())[0][0] or 'Nan'


def get_meaning_dictionary_api(word, session=False):
    url = f"https://api.dictionaryapi.dev/api/v2/entries/en_US/{word}"

    payload = {}
    headers = {}
    if session:  # using session for speed( https://stackoverflow.com/questions/34512646/how-to-speed-up-api-requests )
        response = session.request("GET", url, headers=headers, data=payload)
    else:
        response = requests.request("GET", url, headers=headers, data=payload)
    response = json.loads(response.text)
    return response


# decorate json output to be displayed or written in a file
def decorated_api_result(word, response=False):
    if not response:
        response = get_meaning_dictionary_api(word)
    else:
        response = word

    output_list = list()

    for i in response:
        output_list.append(f'Word : {i["word"]}')
        for meanings in i['meanings']:
            output_list.append(' ' * 4 + f'Part of Speech : {meanings["partOfSpeech"]}')
            output_list.append(' ' * 4 + "Definitions")
            for definitions in meanings['definitions']:
                output_list.append(' ' * 8 + f'definition :')
                output_list.append(' ' * 12 + definitions["definition"])
                if 'synonyms' in definitions.keys():
                    output_list.append(' ' * 8 + 'Synonym : ')
                    for synonym in definitions['synonyms']:
                        output_list.append(' ' * 12 + synonym)
                output_list.append(' ' * 8 + f'Examples : {definitions["example"]}')
    return output_list


# insert word
def update_dictionary(word, meaning):
    # Add a word meaning(ie definition) in Dictionary
    # TODO: store new words in another table not in main
    try:
        val = conn_dict.execute(f'select definition from words_ where definition="{meaning}"').fetchall()
        if not val:
            conn_dict.execute(f'insert into words_ values(?, ?)', (word.title(), meaning))
            conn_dict.commit()
            sg.popup_no_border(f'Successfully Write\nword:{word}\nDefinition{meaning}')
        else:
            sg.popup_no_border(f"Word {word} Already there")
    except Exception as ex:
        sg.popup_error(f'{ex} in update_dictionary', no_titlebar=True)
        logging.error(f'{ex} in update_dictionary')


# add word in exclude
def add_to_exclude(word):
    # common word that doesn't need explanation
    try:
        a = conn_common_word.execute(f'select * from words where word="{word.lower()}"').fetchall()
        if not a:
            conn_common_word.execute(f'insert into words values ("{word.lower()}")')
            conn_common_word.commit()
            sg.popup_no_border(f'{word} exclude successful')
        else:
            print(f'{word} already in there')
            sg.popup_no_border(f'{word} already there')
            logging.info(f'{word} already in there :- in fun add_to_search')
    except Exception as ex:
        sg.popup_error(f'{ex} in Exclude')
        logging.error(f'{ex} in add_to_search')


# remove from exclude for showing in file
def remove_from_exclude(word):
    # those words will be written to your file, considered unfamiliar
    try:
        conn_common_word.execute(f'delete from words where word="{word.lower()}"')
        conn_common_word.commit()
        sg.popup_no_border(f'{word} include successful')
    except Exception as ex:
        sg.popup_error(f'{ex} in Include')
        logging.error(f'{ex} in remove from dict')


if __name__ == '__main__':
    pass
    # reset_common_word()
    # Zythum:- A kind of ancient malt beverage; a liquor made from malt\n and wheat.
    # update_dictionary('chocolates', 'of chocolate')
    print(*decorated_api_result('miserable'), sep='\n')  # When table name returning everything
    # a = get_meaning_dictionary_api('money')
    # print(a[0]['meanings'][0]['definitions'][0]['definition'])
