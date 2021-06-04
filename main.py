import PySimpleGUI as sg
import os
import logging
import re
import enchant
import shutil
from src.ExcludedWord import *


def update_line(line):
    new_line = []
    words = re.findall('([A-Za-z]*|[^A-Za-z])', line)
    for word in words:
        if word.isalpha():
            if lang.check(word) and word.lower() not in common_words:
                try:
                    if values['-DICT MODE-'] == 'Online Dictionary (slow but effective)':
                        meaning = get_meaning_pydict(word)
                    elif values['-DICT MODE-'] == 'Inbuilt dictionary (Fast but less effective)':
                        meaning = get_meaning(word)
                    if meaning:
                        new_word = f'{word}(: {meaning})'
                    else:
                        new_word = word
                except Exception as es:
                    logging.error(f'in word {word} {es}')
                    new_word = word
                new_line.append(new_word)
            else:
                new_line.append(word)
        else:
            new_line.append(word)
    return ''.join(new_line)


def file_maker():
    try:
        new_srt = []
        i = 0
        size = len(file)
        no_word = r'^[^A-Za-z]*$'
        for line in file:
            if re.match(no_word, line):
                new_srt.append(line)
            else:
                new_line = update_line(line)
                new_srt.append(new_line)
            sg.OneLineProgressMeter('Making', i + 1, size)
            i += 1
        return new_srt
    except Exception as er:
        logging.error(f'{er} in file_maker')


def file_reader(filename_local):
    try:
        if os.path.isfile('src/temp.srt'):
            os.remove('src/temp.srt')
        if filename_local.lower().endswith(('.mkv', '.mp4', '.avi', '.vob', '.mov')):
            os.system(f'ffmpeg -i "{filename_local}" "src/temp.srt"')
        elif filename_local.lower().endswith(('.srt', '.sub', '.vtt', 'txt', 'sbv', 'ttml')):
            shutil.copy(filename_local, 'src/temp.srt')
        return filename_local, [line.strip() for line in open(f'src/temp.srt', 'r', encoding='utf')]
    except Exception as er:
        logging.error(f'{er} in fun file_reader()')
        sg.PopupError('cann\'t open file')
        return None, None


# Default Variable
file = None
lang = enchant.Dict("en_US")
common_words = get_common_word()

# layouts
head_layout = [
    [
        sg.Text('Welcome to Subtitle Man')
    ],
    [
        sg.Text('Click here to import file')
    ],
    [
        sg.Text('Enter File Location', key='-FILE LOCATION-')
    ],
    [
        sg.FileBrowse('Import File', key='-IMPORT-', enable_events=True)
    ]
]
make_file_layout = [
    [
        sg.Text('Click here to make subtitle/any text file')
    ],
    [
        sg.InputOptionMenu(('Inbuilt dictionary (Fast but less effective)', 'Online Dictionary (slow but effective)'),
                           key='-DICT MODE-')
    ],
    [
        sg.Button('Make File', key='-MAKE FILE-')
    ]
]
exclude_word_layout = [
    [
        sg.Text('Won\'t write this word to file')
    ],
    [
        sg.Input(default_text='Enter a word', key='-WORD FOR EXCLUDE-', size=(20, 1)),
    ],
    [
        sg.Button('Exclude', key='-EXCLUDE-')
    ]
]
include_word_layout = [
    [
        sg.Text('Will write this word to file')
    ],
    [
        sg.Input(default_text='Enter a word', key='-WORD FOR INCLUDE-', size=(20, 1)),
    ],
    [
        sg.Button('Include', key='-ADD TO SEARCH-')
    ]
]
add_to_dictionary_layout = [
    [
        sg.Text('Add word and definition in dictionary')
    ],
    [
        sg.Input(default_text='Enter a word', key='-WORD FOR DICT-', size=(20, 1))
    ],
    [
        sg.Input(default_text='Enter definition', key='-MEANING FOR DICT-')
    ],
    [
        sg.Button('Add', key='-ADD TO DICT-')
    ]
]

layout = [
    [
        sg.Frame('Hello', layout=head_layout, element_justification='c')
    ],
    [
        sg.Frame('Makefile', layout=make_file_layout, element_justification='c')
    ],
    [
        sg.Frame('Exclude Word', layout=exclude_word_layout, element_justification='c'),
        sg.Frame('Include Word', layout=include_word_layout, element_justification='c')
    ],
    [
        sg.Frame('Add to Dictionary', layout=add_to_dictionary_layout, element_justification='c')
    ]
]

logging.basicConfig(filename="src/info.log", level=logging.NOTSET,
                    format='%(levelname)s - %(asctime)s - %(name)s - %(message)s ')

window = sg.Window(title='Subtitle Man', layout=layout, element_justification='c', margins=(10, 10))

while True:
    event, values = window.read()
    print(event, values)
    if event == sg.WIN_CLOSED:
        break
    if event == '-IMPORT-':
        try:
            filename, file = file_reader(values['-IMPORT-'])
            window['-FILE LOCATION-'].update(filename)
        except Exception as t:
            logging.error(t)

    if event == '-MAKE FILE-':
        if file and values['-DICT MODE-']:
            new_file = file_maker()
            with open(f'{filename}_subtitle-man.srt', mode='w', encoding='utf-8-sig') as f:
                for row in new_file:
                    f.write(row + '\n')

        else:
            sg.PopupError('Please select a valid file or dict mode')

    if event == '-ADD TO DICT-':
        try:
            update_dictionary(values['-WORD FOR DICT-'], values['-MEANING FOR DICT-'])
        except Exception as ex:
            sg.PopupError(f'{ex} happen')
            logging.error(f'{ex} happen in event \'-ADD TO DICT-\'')

    if event == '-EXCLUDE-':
        try:
            add_to_exclude(values['-WORD FOR EXCLUDE-'])
            common_words = get_common_word()
        except Exception as ex:
            logging.error(f'{ex} in event -EXCLUDE-')

    if event == '-ADD TO SEARCH-':
        try:
            remove_from_exclude(values['-WORD FOR INCLUDE-'])
            common_words = get_common_word()
        except Exception as ex:
            logging.error(f'{ex} in event -ADD TO SEARCH-')


window.close()
