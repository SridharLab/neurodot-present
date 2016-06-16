# -*- coding: utf-8 -*-
# 20k common words text file from: https://github.com/first20hours/google-10000-english
import pygame, sys
import random
from present_lib import Screen, FixationCross, TextDisplay, UserEscape

# encodes a latin string in a randomly generated hebrew cypher
def code_hebrew(latin_string):
    latin_alphabet = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    hebrew_alphabet = list(u"\u05D0\u05D1\u05D2\u05D3\u05D4\u05D5\u05D6\u05D7\u05D8\u05D9\u05DA\u05DB\u05DC\u05DD\u05DE\u05DF\u05E1\u05E2\u05E3\u05E4\u05E5\u05E6\u05E7\u05E8\u05E9\u05EA")
    
    random.shuffle(hebrew_alphabet)
    cypher = dict(zip(latin_alphabet, hebrew_alphabet))
    cypher[" "] = " "

    latin_list = list(latin_string)
    coded_string = ""
    i = 0
    for char in latin_list:
        coded_string += cypher[char]
        i += 1

    return coded_string

def main():
    pygame.init()
    TASK_DURATION = 30  #seconds
    num_trials = 2

    # get and randomize a list of 4-letter words in the 20k most used
    word_list = []
    with open("20k.txt") as list_file:
        for line in list_file:
            if len(line.rstrip()) == 4:
                word_list.append(line.rstrip().upper())
    random.shuffle(word_list)

    #instantiate objects
    FC = FixationCross(color = "black")
    SCR = Screen(color = "white", fixation_cross = FC)
    redScreen = Screen(color = "red")
    whiteScreen = Screen(color = "white")
    latin_text = TextDisplay(font_type = "Arial.ttf", font_size = 288)
    hebrew_text = TextDisplay(font_type = "ArialHebrew.ttf", font_size = 288)
    
    try:
        #start sequence  
        SCR.run(duration = 3, vsync_value = 0)  
        SCR.run(duration = 1, vsync_value = 13)  #begins the start frame
        SCR.run(duration = 1, vsync_value = 5)  #starts the recording

        trial = 0
        while trial < num_trials:
            #task
            latin_text.run(text_content = word_list[trial], duration = 4, vsync_value = 1)
            SCR.run(duration = 2 + 4*random.random(), vsync_value = 0)
            hebrew_text.run(text_content = code_hebrew(word_list[trial]), duration = 4, vsync_value = 2)
            SCR.run(duration = 2 + 4*random.random(), vsync_value = 0)

            trial += 1

    except UserEscape:
        print "User stopped the sequence."
    except:
        print "Unexpected error:"
        raise
        
    finally:
        try:
            #stop sequence
            whiteScreen.run(duration = 1, vsync_value = 13,)
            whiteScreen.run(duration = 1, vsync_value = 0,)
            redScreen.run(duration = 1, vsync_value = 5, wait_on_user_keypress = True,)
        except UserEscape:
            pass
        except:
            print "Unexpected error:"
            raise
    
    pygame.quit()
    sys.exit()

if __name__ == '__main__': main()


