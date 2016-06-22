# -*- coding: utf-8 -*-
import pygame, sys, os
import random
from neurodot_present.present_lib import Screen, FixationCross, TextDisplay, UserEscape, bell, run_start_sequence, run_stop_sequence
import neurodot_present.resources

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

    arial_heightScaleFactor = 1.0487012987  # the height of ArialHebrew characters differ from Arial chars by this factor
    num_blocks    = 24    # num_blocks * wordsPerBlock should not exceed 512
    wordsPerBlock = 8     # words displayed (both latin and hebrew) per block

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
    words_displayed = open(fn, "w")
    FC = FixationCross(color = "black")
    restScreen = Screen(color = "white", fixation_cross = FC)
    blankScreen = Screen(color = "white")
    latin_text = TextDisplay(vsync_value = 1,
                             font_type = "Arial.ttf",
                             font_size = 288,
                             screen_bgColor = "white"
                             )
    hebrew_text = TextDisplay(vsync_value = 2,
                              font_type = "ArialHebrew.ttf",
                              font_size = int(288 * arial_heightScaleFactor),
                              screen_bgColor = "white"
                              )

    # get and randomize a list of latin words from the word_list.txt file
    word_list = []
    with neurodot_present.resources.load_wordlist() as list_file:
        for line in list_file.readlines():
            word_list.append(line.rstrip().upper())
    random.shuffle(word_list)

    # get list of dictionaries for latin/hebrew words and randomize
    stim_list = []
    for word in word_list[0:num_blocks*wordsPerBlock/2 + 1]:
        latin = {'word': word, 'lang_id': 1}
        hebrew = {'word': code_hebrew(word), 'lang_id': 2}
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

                #display latin or hebrew text
                if stim['lang_id'] == 1:
                    words_displayed.write(stim['word'].encode("utf8") + "\n")
                    latin_text.run(text_content = stim['word'], duration = 1)
                elif stim['lang_id'] == 2:
                    words_displayed.write(stim['word'].encode("utf8") + "\n")
                    hebrew_text.run(text_content = stim['word'], duration = 1)

                # display blank screen
                blankScreen.run(duration = 1, vsync_value = 0)

            if block < num_blocks-1:

                # add an empty line to text file to signify between trials
                words_displayed.write("\n")

                #rest period
                bell()
                restScreen.run(duration = 4, vsync_value = 0)
                bell()
                restScreen.run(duration = random.uniform(1,3), vsync_value = 0)

            block += 1
        
    except UserEscape as exc:
        print exc
    except:
        print "Unexpected error:"
        raise
    finally:
        # stop sequence
        run_stop_sequence()
    
    pygame.quit()
    sys.exit()

if __name__ == '__main__': main()

