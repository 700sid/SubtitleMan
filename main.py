import concurrent.futures
import json
import PySimpleGUI as sg
import os
import logging
import re
import enchant
import shutil
import requests
import src.ExcludedWord as EW


def update_word_dict(file):
    size = len(word_to_write)
    i = 0
    if values['-DICT MODE-'] == 'Online Dictionary (Required Internet)':
        def update_word(word):  # getting meaning from api
            nonlocal session
            response = EW.get_meaning_dictionary_api(word, session)
            word_to_write[word] = response  # writing to dictionary

        session = requests.Session()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            results = executor.map(update_word, word_to_write.keys())
            # getting result from api using threads and session
            for result in results:
                try:
                    result
                except Exception as e:
                    logging.error(f'{e} in Thread update word dict {result}')
                # Changing word with word and meaning

                if not sg.OneLineProgressMeter('Downloading Meaning', i, size, grab_anywhere=True):
                    # A progress meter for show progress and also have power to cancel progress
                    sg.Popup('Operation Canceled by User')
                    return
                i += 1
            sg.OneLineProgressMeter('Download Meaning', i, size, grab_anywhere=True)  # Progress meter's anomaly
        session.close()

        with open(f'{filename}-summary.txt', mode='w', encoding='utf-8-sig') as f:
            for word in word_to_write.values():
                try:
                    for line in EW.decorated_api_result(word, True):
                        f.write(line + '\n')
                except Exception as e:
                    logging.error(f'{e} while writing summary in online dict')
                f.write('\n\n\n')
            sg.Popup('Summary File Write Successful', auto_close=True, auto_close_duration=1)

        with open(f'{filename}.subtitle-man.srt', mode='w', encoding='utf-8-sig') as f:
            for line in file.split('\n'):
                words = re.findall(r'[A-Za-z]+', line)
                for word in words:
                    if word in word_to_write.keys():
                        for temp in word_to_write[word]:
                            # searching for definition in json response if any
                            try:
                                meaning = temp['meanings'][0]['definitions'][0]['definition']
                                break
                            except Exception as e:
                                logging.error(f'{e} in Thread update word dict {result}')

                        line = line.replace(word, f"{word}(: {meaning})")
                f.write(line + '\n')
            sg.Popup('Subtitle File Write Successful')

    elif values['-DICT MODE-'] == 'Inbuilt Dictionary (Not recommended)':
        for word in word_to_write:
            if not sg.OneLineProgressMeter('Getting Meanings', i, size, grab_anywhere=True):
                # A progress meter for show progress and also have power to cancel progress
                sg.Popup('Operation Canceled by User')
                return
            i += 1
            meaning = EW.get_meaning(word)  # Getting mean
            if meaning != 'Nan':
                meaning = meaning.split(';')
                word_to_write[word] = meaning  # writing to dictionary

        sg.OneLineProgressMeter('Getting Meanings', i, size, grab_anywhere=True)  # fun's anomaly

        with open(f'{filename}-summary.txt', mode='w', encoding='utf-8-sig') as f:
            for word in word_to_write:
                        if word_to_write[word] is not None:
                            f.write(f'{word}:\n')
                            for line in word_to_write[word]:
                                f.write(f'    {line}\n')
                            f.write('\n\n\n')

            sg.Popup('Summary File Write Successful', auto_close=True, auto_close_duration=1)

        with open(f'{filename}.subtitle-man.srt', mode='w', encoding='utf-8-sig') as f:
            for line in file.split('\n'):
                words = re.findall('[A-Za-z]+', line)
                for word in words:
                    if word in word_to_write.keys():
                        if word_to_write[word]:
                            line = line.replace(word, f'{word}(: {word_to_write[word][0]})')
                f.write(line + '\n')
            sg.Popup('Subtitle File Write Successful')


def get_user_permission():
    # TODO: Show user the word list with checkbox to decide
    pass


def get_words_from_file():
    words = re.findall('([A-Za-z]+)', file)  # Getting words from file
    for word in words:
        try:
            if lang.check(word) and word.lower() not in common_words:  # checking for not common valid english word
                word_to_write[word] = None
        except Exception as e:
            logging.error(f'in word {word} {e}')


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
        with open(f'src/temp.srt', 'r', encoding='utf') as f:
            file_data = f.read()
        return filename_local, file_data
    except Exception as er:
        logging.error(f'{er} in fun file_reader()')
        sg.PopupError('cann\'t open file')
        return None, None


def subtitle_login():
    global user_token
    url = "https://api.opensubtitles.com/api/v1/login"

    payload = {'username': values['-USERNAME OPENSUBTITLES-'],
               'password': values['-PASSWORD OPENSUBTITLES-']}
    files = [

    ]
    headers = {
        'Api-key': api_key
    }

    response = requests.request("POST", url, headers=headers, data=payload, files=files)

    if 'message' not in response.json():
        user_token = response.json()['token']
        sg.Popup('Login Successful')
        print(user_token)
    else:
        sg.PopupError(response.json()['message'])


if __name__ == '__main__':
    # Default Variable
    file = None
    lang = enchant.Dict("en_US")
    user_token = None
    list_subtitles = None
    common_words = EW.get_common_word()  # List of common words
    sg.theme('DarkGrey14')
    logging.basicConfig(filename="src/info.log", level=logging.NOTSET,
                        format='%(levelname)s - %(asctime)s - %(name)s - %(message)s ')
    word_to_write = dict()

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
            sg.InputOptionMenu(('Inbuilt Dictionary (Not recommended)', 'Online Dictionary (Required Internet)'),
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
            sg.InputOptionMenu(('Inbuilt Dictionary (Not recommended) (Offline)', 'Online Dictionary (Required Internet)'),
                               key='-DICT SEARCH MODE-')
        ],
        [
            sg.Button('Define', key='-DICTIONARY SEARCH-')
        ],
        [
            sg.Text('', visible=False, key='-DICTIONARY MEANING-')
        ]
    ]

    layout_left = [
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

    api_key_layout = [
        [
            sg.In('Enter OpenSubtitles API key', key='-OPEN API KEY-')
        ],
        [
            sg.Button('ADD API KEY', key='-ADD API KEY-')
        ],
        [
            sg.Text('https://www.opensubtitles.com/consumers'),
        ]
    ]

    login = [
        [
            sg.Text('Login id :', size=(8, 1)),
            sg.In('', key='-USERNAME OPENSUBTITLES-', size=(30, 1)),
        ],
        [
            sg.Text('Password:', size=(8, 1)),
            sg.In('', key='-PASSWORD OPENSUBTITLES-', size=(30, 1), password_char='*')
        ],
        [
            sg.Button('Login', key='-LOGIN OPENSUBTITLES-')
        ]
    ]

    layout_right = [
        [
            sg.Text('Download Subtitle')
        ],
        [
            sg.Frame('Login', layout=login)
        ],
        [
            sg.In('Enter Subtitle\'s name', key='-SUBTITLE NAME-')
        ],
        [
            sg.Button('Search', key='-SUBTITLE SEARCH-')
        ],
        [
            sg.Listbox(key='-SUBTITLE LIST-', values=[], size=(40, 10))
        ],
        [
            sg.Button('Download', key='-DOWNLOAD SUBTITLE-')
        ],

    ]

    with open('key.txt', mode='r') as f:
        api_key = f.read()
        if not api_key:
            layout_right.extend(api_key_layout)

    layout = [
        [
            sg.Column(layout_left),
            sg.VSeparator(),
            sg.Column(layout_right)
         ]
    ]

    window = sg.Window(title='Subtitle Man', layout=layout, element_justification='c',
                       margins=(10, 10), enable_close_attempted_event=True)

    while True:
        event, values = window()
        print(event, values)
        if event == sg.WINDOW_CLOSE_ATTEMPTED_EVENT and sg.popup_yes_no('Do you really want to exit?') == 'Yes':
            if user_token:
                url = "https://api.opensubtitles.com/api/v1/logout"

                payload = {}
                headers = {
                    'Authorization': user_token,
                    'Api-key': api_key
                }

                response = requests.request("DELETE", url, headers=headers, data=payload)
                print(response.text)
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
                    get_words_from_file()
                    get_user_permission()
                    update_word_dict(file)
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
                EW.update_dictionary(values['-WORD FOR DICT-'], values['-MEANING FOR DICT-'])
            except Exception as ex:
                sg.PopupError(f'{ex} happen')
                logging.error(f'{ex} happen in event \'-ADD TO DICT-\'')

        if event == '-EXCLUDE-':
            # That word will not be written in your file next time
            try:
                EW.add_to_exclude(values['-WORD COMMON-'])
                common_words.append(values['-WORD COMMON-'])
            except Exception as ex:
                logging.error(f'{ex} in event -EXCLUDE-')

        if event == '-INCLUDE-':
            # That word will be written in your file next time
            try:
                EW.remove_from_exclude(values['-WORD COMMON-'])
                common_words.remove(values['-WORD COMMON-'])
            except Exception as ex:
                logging.error(f'{ex} in event -INCLUDE-')

        if event == '-DICTIONARY SEARCH-':
            # A normal dictionary for simple usage
            try:
                if values['-DICT SEARCH MODE-'] == 'Inbuilt Dictionary (Not recommended) (Offline)':
                    sg.Print(EW.get_meaning(values['-DICTIONARY SEARCH WORD-']), no_titlebar=True)
                elif values['-DICT SEARCH MODE-'] == 'Online Dictionary (Required Internet)':
                    for i in EW.decorated_api_result(values['-DICTIONARY SEARCH WORD-']):
                        sg.Print(i, no_titlebar=True, grab_anywhere=True)
                else:
                    sg.popup_error('Select a mode')
            except Exception as es:
                logging.error(f'{es} in -DICTIONARY SEARCH-')
                sg.popup_error(f'{es}\n\n"Try righting single word"')

        if event == '-LOGIN OPENSUBTITLES-':
            try:
                subtitle_login()
            except Exception as ex:
                logging.error(f'{ex} in -LOGIN OPENSUBTITLES-')

        if event == '-SUBTITLE SEARCH-':
            url = f"https://api.opensubtitles.com/api/v1/subtitles?query={values['-SUBTITLE NAME-']}&languages=en"

            payload = {}
            headers = {
                'Api-key': api_key
            }

            response = requests.request("GET", url, headers=headers, data=payload)

            list_subtitles = {value["attributes"]["release"]: value['id'] for value in response.json()['data']}
            window['-SUBTITLE LIST-'].update(list_subtitles.keys())

        if event == '-DOWNLOAD SUBTITLE-':
            try:
                print(values['-SUBTITLE LIST-'])
                url = "https://api.opensubtitles.com/api/v1/download"

                payload = json.dumps({
                    "file_id": list_subtitles[values['-SUBTITLE LIST-'][0]],
                    "file_name": values['-SUBTITLE LIST-'][0],
                    # "strip_html": True,
                    # "cleanup_links": True,
                    # "remove_adds": True,
                    # "in_fps": 0,
                    # "out_fps": 0,
                    # "timeshift": 0
                })
                headers = {
                    'Authorization': user_token,
                    'Content-Type': 'application/json',
                    'Api-key': api_key
                }

                response = requests.request("POST", url, headers=headers, data=payload)
                response = response.json()
                print(response)

                downloaded_subtitle_file = requests.request('GET', url=response['link']).text
                print(downloaded_subtitle_file)
                download_location = sg.popup_get_folder('Select Folder')
                with open(f"{download_location}/{values['-SUBTITLE LIST-'][0]}.srt", mode='w',
                          encoding='utf-8-sig') as f:
                    f.write(downloaded_subtitle_file)
                sg.Popup('File Download Successful')
            except Exception as es:
                sg.PopupError(es)

        if event == '-ADD API KEY-':
            try:
                with open('key.txt', 'w') as api_file:
                    api_file.write(values['-OPEN API KEY-'])
                    sg.Popup('Key write Successful')
                api_key = values['-OPEN API KEY-']
            except Exception as es:
                login.error(f'{es} in -ADD API KEY-')

    window.close()
