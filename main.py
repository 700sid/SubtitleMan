import PySimpleGUI as sg
import os
import logging
import re
import enchant
import shutil
from src.ExcludedWord import *


# TODO: stable http connection to not connect every time and use multi threading or subprocesses
# TODO: in sort speed up

def update_line(line, session):
    new_line = []
    words = re.findall('([A-Za-z]*|[^A-Za-z])', line)  # Splitting words and non words
    for word in words:
        if word.isalpha():  # checking for word
            if lang.check(word) and word.lower() not in common_words:
                # Checking if english word not a common word
                # TODO: create summary file
                try:
                    if word in word_written.keys():
                        if values['-DICT MODE-'] == 'Online Dictionary (slow but effective)':
                            meaning = word_written[word][0]['meanings'][0]['definitions'][0]['definition']
                        elif values['-DICT MODE-'] == 'Inbuilt dictionary (Fast but less effective)':
                            meaning = min(word_written[word].split(';'))
                    elif values['-DICT MODE-'] == 'Online Dictionary (slow but effective)':
                        # get word from online dictionary
                        meaning = get_meaning_dictionary_api(word, session)
                        word_written[word] = meaning
                        meaning = meaning[0]['meanings'][0]['definitions'][0]['definition']
                    elif values['-DICT MODE-'] == 'Inbuilt dictionary (Fast but less effective)':
                        # get word from the local database comparatively faster
                        meaning = get_meaning(word)
                        word_written[word] = meaning
                        meaning = min(meaning.split(';'))
                    if meaning:
                        # TODO: select legitimate meaning and add to dict
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
        no_word = r'^[^A-Za-z]*$'  # checking if line contains words or not
        with requests.Session() as session:  # making a session for gaining online speed
            for line in file:
                if re.match(no_word, line):
                    # if no words in line we append as it is
                    new_srt.append(line)
                else:
                    # if words update line and append new line
                    new_line = update_line(line, session)
                    new_srt.append(new_line)
                if not sg.OneLineProgressMeter('Making', i, size, no_titlebar=True, grab_anywhere=True):
                    # A progress meter for show progress and also have power to cancel progress
                    sg.Popup('Operation Canceled by User')
                    break
                i += 1
            else:  # if for run flawlessly then else occur
                # additional meter statement for overcoming a error of returning false in last iteration
                sg.OneLineProgressMeter('Making', i, size, no_titlebar=True, grab_anywhere=True)
                sg.Popup('File write completed \nSaved on same Location')
                return new_srt
        return False
    except Exception as er:
        logging.error(f'{er} in file_maker')


def file_reader(filename_local):
    # create a temp file for safety, not working in original file
    try:
        if os.path.isfile('src/temp.srt'):
            os.remove('src/temp.srt')
        if filename_local.lower().endswith(('.mkv', '.mp4', '.avi', '.vob', '.mov')):
            # using ffmpeg for extract srt file from video file
            os.system(f'ffmpeg -i "{filename_local}" "src/temp.srt"')
        elif filename_local.lower().endswith(('.srt', '.sub', '.vtt', 'txt', 'sbv', 'ttml')):
            shutil.copy(filename_local, 'src/temp.srt')
        # returning file location with list of lines in file
        return filename_local, [line.strip() for line in open(f'src/temp.srt', 'r', encoding='utf')]
    except Exception as er:
        logging.error(f'{er} in fun file_reader()')
        sg.PopupError('cann\'t open file')
        return None, None


# Default Variable
file = None
lang = enchant.Dict("en_US")
common_words = get_common_word()  # List of common words
sg.theme('DarkGrey14')
logging.basicConfig(filename="src/info.log", level=logging.NOTSET,
                    format='%(levelname)s - %(asctime)s - %(name)s - %(message)s ')
word_written = dict()

# layouts
head_layout = [
    [
        sg.Text('Welcome to Subtitle Man', font=('Franklin Gothic Book', 16))
    ],
    [
        sg.Text('Click here to import file')
    ],
    [
        sg.Input('Enter File Location', key='-FILE LOCATION-', size=(40, 1)),
        sg.FileBrowse('Browse')
    ],
    [
        sg.OK(key='-IMPORT-')
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
include_exclude_word_layout = [
    [
        sg.Text('Write this word to file or not')
    ],
    [
        sg.Input(default_text='Enter a word', key='-WORD COMMON-'),
    ],
    [
        sg.Button('Include', key='-INCLUDE-', button_color='green4',
                  tooltip='Definition of this word will be wrote on the file.'),
        sg.Button('Exclude', key='-EXCLUDE-', button_color='firebrick4',
                  tooltip='Definition of this word will not be wrote on the file.')
    ],
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
dictionary_layout = [
    [
        sg.Input(default_text='Enter Word', key='-DICTIONARY SEARCH WORD-')
    ],
    [
        sg.InputOptionMenu(('Inbuilt dictionary (Offline)', 'Online Dictionary'),
                           key='-DICT SEARCH MODE-')
    ],
    [
        sg.Button('Define', key='-DICTIONARY SEARCH-')
    ],
    [
        sg.Text('', visible=False, key='-DICTIONARY MEANING-')
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
        sg.Frame('Exclude/Include Word', layout=include_exclude_word_layout, element_justification='c')
    ],
    [
        sg.Frame('Add to Dictionary', layout=add_to_dictionary_layout, element_justification='c')
    ],
    [
        sg.Frame('Dictionary', layout=dictionary_layout, element_justification='c')
    ]
]

window = sg.Window(title='Subtitle Man', layout=layout, element_justification='c',
                   margins=(10, 10), enable_close_attempted_event=True)

while True:
    event, values = window()
    print(event, values)
    if event == sg.WINDOW_CLOSE_ATTEMPTED_EVENT and sg.popup_yes_no('Do you really want to exit?') == 'Yes':
        break
    if event == '-IMPORT-':
        # Just import file and take his name and list of line as result
        try:
            filename, file = file_reader(values['-FILE LOCATION-'])
        except Exception as t:
            logging.error(t)

    if event == '-MAKE FILE-':
        # make your file in same location if -IMPORT- Successful && A dictionary mode selected
        try:
            if file and values['-DICT MODE-']:
                new_file = file_maker()
                if new_file:
                    with open(f'{filename}_subtitle-man.srt', mode='w', encoding='utf-8-sig') as f:
                        for row in new_file:
                            f.write(row + '\n')
            elif not file:
                sg.PopupError('Please select\n\n> a valid file\nEnsure Pressing OK button in import')
            elif not values['-DICT MODE-']:
                sg.PopupError('Please select\n\n> a dict mode')
        except Exception as ex:
            sg.PopupError(ex)
            logging.error(f'{ex} in -makefile-')

    if event == '-ADD TO DICT-':
        # Add a definition to dictionary
        try:
            update_dictionary(values['-WORD FOR DICT-'], values['-MEANING FOR DICT-'])
        except Exception as ex:
            sg.PopupError(f'{ex} happen')
            logging.error(f'{ex} happen in event \'-ADD TO DICT-\'')

    if event == '-EXCLUDE-':
        # That word will not be written in your file next time
        try:
            add_to_exclude(values['-WORD COMMON-'])
            common_words = get_common_word()
        except Exception as ex:
            logging.error(f'{ex} in event -EXCLUDE-')

    if event == '-INCLUDE-':
        # That word will be written in your file next time
        try:
            remove_from_exclude(values['-WORD COMMON-'])
            common_words = get_common_word()
        except Exception as ex:
            logging.error(f'{ex} in event -INCLUDE-')

    if event == '-DICTIONARY SEARCH-':
        # A normal dictionary for simple usage
        try:
            if values['-DICT SEARCH MODE-'] == 'Inbuilt dictionary (Offline)':
                sg.Print(get_meaning(values['-DICTIONARY SEARCH WORD-']), no_titlebar=True)
            elif values['-DICT SEARCH MODE-'] == 'Online Dictionary':
                for i in decorated_api_result(values['-DICTIONARY SEARCH WORD-']):
                    sg.Print(i, no_titlebar=True, grab_anywhere=True)
            else:
                sg.popup_error('Select a mode')
        except Exception as es:
            logging.error(f'{es} in -DICTIONARY SEARCH-')
            sg.popup_error(f'{es}\n\n"Try righting single word"')

window.close()
