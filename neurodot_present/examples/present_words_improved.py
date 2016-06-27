# -*- coding: utf-8 -*-
import pygame, sys, os
import random
import upsidedown
from neurodot_present.present_lib import Screen, FixationCross, TextDisplay, UserEscape, bell, run_start_sequence, run_stop_sequence
import neurodot_present.resources

STIMULUS_DURATION = 0.5

neurodot_present.present_lib.DEBUG = False

# encodes a latin string in a randomly generated cypher

def cypher_string(latin_string):
    latin_alphabet  = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    cypher_alphabet = latin_alphabet[:]  #NOTE, need to make a separate copy
    random.shuffle(cypher_alphabet)
    cypher_alphabet = list(upsidedown.transform("".join(cypher_alphabet)))
    
    cypher_map = dict(zip(latin_alphabet, cypher_alphabet))
    cypher_map[" "] = " "

    latin_list = list(latin_string.upper())
    coded_string = ""
    i = 0
    for char in latin_list:
        coded_string += cypher_map[char]
        i += 1

    return coded_string

def main():
    num_blocks    = 16    # num_blocks * wordsPerBlock should not exceed 512
    wordsPerBlock = 16     # words displayed (both latin and hebrew) per block

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
    words_displayed = open(fn, "w")
    FC = FixationCross(color = "black")
    restScreen = Screen(color = "white", fixation_cross = FC)
    blankScreen = Screen(color = "white")
    text = TextDisplay(vsync_value = 1,
                             font_type = "DejaVuSansMono.ttf",
                             font_size = 288,
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
        vsync_value = len(word) - 3 #words are 4,5,6 letters long
        latin = {'word': word, 'vsync_value': vsync_value}
        print latin
        cypher = {'word': cypher_string(word), 'vsync_value': vsync_value + 3}
        print cypher
        stim_list.append(latin)
        stim_list.append(cypher)
    random.shuffle(stim_list)
    
    try:
        #start sequence
        run_start_sequence()
        restScreen.run(duration = 2, vsync_value = 0)

        block = 0
        while block < num_blocks:
            for stim in stim_list[block*wordsPerBlock : block*wordsPerBlock + wordsPerBlock]:
                words_displayed.write(stim['word'].encode("utf8") + "\n")
                text.run(text_content = stim['word'],
                         duration = STIMULUS_DURATION,
                         vsync_value = stim['vsync_value']
                         )
                # display blank screen
                blankScreen.run(duration = STIMULUS_DURATION, vsync_value = 0)

            if block < num_blocks-1:

                # add an empty line to text file to signify between trials
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
        # stop sequence
        run_stop_sequence()
    
    pygame.quit()
    sys.exit()

if __name__ == '__main__': main()

