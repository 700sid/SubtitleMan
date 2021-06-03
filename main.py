import PySimpleGUI as sg
import os
import logging
import re
import enchant
import shutil
from src.ExcludedWord import get_common_word, get_meaning, update_dictionary, add_to_exclude, remove_from_exclude


def update_line(line):
    new_line = []
    words = re.findall('([A-Za-z]*|[^A-Za-z])', line)
    for word in words:
        if word.isalpha():
            if lang.check(word) and word.lower() not in common_words:
                try:
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


def file_reader():
    try:
        if os.path.isfile('src/temp.srt'):
            os.remove('src/temp.srt')
        filename = sg.PopupGetFile('Select the video file')
        if filename.lower().endswith(('.mkv', '.mp4', '.avi', '.vob', '.mov')):
            os.system(f'ffmpeg -i "{filename}" "src/temp.srt"')
        elif filename.lower().endswith(('.srt', '.sub', '.vtt', 'txt', 'sbv', 'ttml')):
            shutil.copy(filename, 'src/temp.srt')
        return filename, [line.strip() for line in open(f'src/temp.srt', 'r', encoding='utf')]
    except Exception as er:
        logging.error(f'{er} in fun file_reader()')
        sg.PopupError('cann\'t open file')
        return None, None


# Default Variable
file = None
lang = enchant.Dict("en_US")
common_words = get_common_word()


layout = [
    [
        sg.Text('Welcome to Subtitle Man')
    ],
    [
        sg.Text('Click here to import file'),
        sg.Button('Import File', key='-IMPORT-')
    ],
    [
        sg.Text('Click here to make subtitle/any text file'),
        sg.Button('Make File', key='-MAKE FILE-')
    ],
    [
        sg.HSeparator()
    ],
    [
        sg.Text('Exclude word from Searching')
    ],
    [
        sg.Input(default_text='Enter a word', key='-WORD FOR EXCLUDE-'),
        sg.Submit(key='-EXCLUDE-')
    ],
    [
        sg.HSeparator()
    ],
    [
        sg.Text('Include word for Searching')
    ],
    [
        sg.Input(default_text='Enter a word', key='-WORD FOR INCLUDE-'),
        sg.Submit(key='-ADD TO SEARCH-')
    ],
    [
        sg.HSeparator()
    ],
    [
        sg.Text('Add in dictionary')
    ],
    [
        sg.Input(default_text='Enter a word', key='-WORD FOR DICT-')
    ],
    [
        sg.Input(default_text='Enter definition', key='-MEANING FOR DICT-')
    ],
    [
        sg.Submit(key='-ADD TO DICT-')
    ]
]

logging.basicConfig(filename="src/info.log", level=logging.NOTSET,
                    format='%(levelname)s - %(asctime)s - %(name)s - %(message)s ')

window = sg.Window(title='Subtitle Man', layout=layout, element_justification='c')

while True:
    event, values = window.read()
    print(event, values)
    if event == sg.WIN_CLOSED:
        break
    if event == '-IMPORT-':
        try:
            filename, file = file_reader()
        except Exception as t:
            logging.error(t)

    if event == '-MAKE FILE-':
        if file:
            new_file = file_maker()
            with open(f'{filename}_subtitle-man.srt', 'w') as f:
                for row in new_file:
                    f.write(row + '\n')

        else:
            sg.PopupError('Please select a valid file')

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
