# -*- coding: utf-8 -*-
import pygame, sys, os
import random
from neurodot_present.present_lib import Screen, FixationCross, TextDisplay, UserEscape, bell, run_start_sequence, run_stop_sequence
import neurodot_present.resources

STIMULUS_DURATION = 0.5
SUPRESS_TXT_OUTPUT = True  # supress writing words displayed to text files

# encodes a latin string in a randomly generated hebrew cypher
def code_hebrew(latin_string):
    latin_alphabet = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    hebrew_alphabet = list(
        u"\u05D0\u05D1\u05D2\u05D3\u05D4\u05D5\u05D6\u05D7\u05D8\u05D9\u05DA\u05DB\u05DC\u05DD\u05DE\u05DF\u05E1\u05E2\u05E3\u05E4\u05E5\u05E6\u05E7\u05E8\u05E9\u05EA")

    random.shuffle(hebrew_alphabet)
    cypher = dict(zip(latin_alphabet, hebrew_alphabet))
    cypher[" "] = " "

    latin_list = list(latin_string.upper())
    coded_string = ""
    i = 0
    for char in latin_list:
        coded_string += cypher[char]
        i += 1

    return coded_string

def main():

    num_blocks    = 16    # num_blocks * wordsPerBlock should not exceed 512
    wordsPerBlock = 16     # words displayed (both latin and hebrew) per block
    word_lengths = [4, 5, 6]   # character lengths to select from word_list.txt


    #ensure that video mode is at the maxium FPS
    if sys.platform.startswith("linux"):
        from subprocess import call
        call(["xrandr","-r","144"])

    pygame.init()
    pygame.mouse.set_visible(False)

    #get filepath/name for words displayed text file
    if not os.path.isdir("data"):
        os.mkdir("data")
    num = 0
    while True:
        fn = "data/words_displayed_%02d.txt" % num
        if not os.path.isfile(fn):
            break
        num += 1

    #instantiate some objects
    if not SUPRESS_TXT_OUTPUT:
        words_displayed = open(fn, "w")
    FC = FixationCross(color = "black")
    restScreen = Screen(color = "white", fixation_cross = FC)
    blankScreen = Screen(color = "white")
    text = TextDisplay(font_size = 288,
                             font_type = "FreeMono.ttf",
                             screen_bgColor = "white",
                             )

    # get and randomize a list of latin words from the word_list.txt file
    word_list = []
    with neurodot_present.resources.load_wordlist() as list_file:
        for line in list_file.readlines():
            if len(line.rstrip()) in word_lengths:
                word_list.append(line.rstrip().upper())
    random.shuffle(word_list)

    # get list of dictionaries for latin/hebrew words and randomize
    stim_list = []
    for word in word_list[0:num_blocks*wordsPerBlock/2 + 1]:
        vsync_value = len(word) - 3 #words are 4,5,6 letters long
        latin = {'word': word, 'vsync_value': vsync_value}
        hebrew = {'word': code_hebrew(word), 'vsync_value': vsync_value + 3}
        stim_list.append(latin)
        stim_list.append(hebrew)
    random.shuffle(stim_list)

    try:

        #start sequence
        run_start_sequence()
        restScreen.run(duration = 2, vsync_value = 0)

        block = 0
        while block < num_blocks:
            for stim in stim_list[block*wordsPerBlock : block*wordsPerBlock + wordsPerBlock]:

                if not SUPRESS_TXT_OUTPUT:
                    words_displayed.write(stim['word'].encode("utf8") + "\n")

                text.run(text_content = stim['word'],
                         duration = STIMULUS_DURATION,
                         vsync_value = stim['vsync_value']
                         )
                #print text.textSurface.get_width()

                # display blank screen
                blankScreen.run(duration = STIMULUS_DURATION, vsync_value = 0)

            if block < num_blocks-1:

                # add an empty line to text file to signify between trials
                if not SUPRESS_TXT_OUTPUT:
                    words_displayed.write("\n")

                #rest period
                bell()
                restScreen.run(duration = 3, vsync_value = 0)
                bell()
                restScreen.run(duration = random.uniform(1,3), vsync_value = 0)

            block += 1

    except UserEscape as exc:
        print exc
    except:
        print "Unexpected error:"
        raise
    finally:
        if not SUPRESS_TXT_OUTPUT:
            words_displayed.close()

        # stop sequence
        run_stop_sequence()

    pygame.quit()
    sys.exit()

if __name__ == '__main__': main()

