# -*- coding: utf-8 -*-
import pygame, sys
import random
from present_lib import Screen, FixationCross, TextDisplay, UserEscape, bell

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
    pygame.init()
    arial_heightScaleFactor = 1.0487012987  # the height of ArialHebrew characters differ from Arial chars by this factor
    num_trials = 2
    wordsPerTrial = 4  # latin words displayed per trial
    
    # get and randomize a list of 4-letter words from the word_list.txt file
    word_list = []
    with open("resources/word_list.txt") as list_file:
        for line in list_file:
            word_list.append(line.rstrip().upper())
    random.shuffle(word_list)
    
    #instantiate objects
    FC = FixationCross(color = "black")
    words_displayed = open("data/words_displayed.txt", "w")
    notStim = Screen(color = "white", fixation_cross = FC)
    redScreen = Screen(color = "red")
    blankScreen = Screen(color = "white")
    restScreen = Screen(color = "black")
    latin_text = TextDisplay(font_type = "resources/Arial.ttf", font_size = 288, screen_bgColor = "white")
    hebrew_text = TextDisplay(font_type = "resources/ArialHebrew.ttf", font_size = int(288 * arial_heightScaleFactor), screen_bgColor = "white")
    
    try:
        #start sequence  
        restScreen.run(duration = 3, vsync_value = 0)
        bell()
        restScreen.run(duration = 1, vsync_value = 0)  
        restScreen.run(duration = 1, vsync_value = 13)  #begins the start frame
        notStim.run(duration = 1, vsync_value = 0) 
        notStim.run(duration = 1, vsync_value = 5)      #starts the recording
        notStim.run(duration = 1, vsync_value = 0)

        trial = 0
        word_index = 0
        word_counter = 0
        while trial < num_trials:
            while word_counter < wordsPerTrial:
                word_counter += 1
                word_index += 1

                #write words which will be displayed to output file
                words_displayed.write(word_list[word_index] + "\n")
                words_displayed.write(code_hebrew(word_list[word_index]).encode("utf8") + "\n")

                #task
                latin_text.run(text_content = word_list[word_index], duration = 1, vsync_value = 1)
                notStim.run(duration = 1, vsync_value = 0)
                hebrew_text.run(text_content = code_hebrew(word_list[word_index]), duration = 1, vsync_value = 2)
                notStim.run(duration = 1, vsync_value = 0)
            
            word_counter = 0

            if trial < num_trials-1:
                # add an empty line to text file to signify between trials
                words_displayed.write("\n")

                #rest period
                bell()
                restScreen.run(duration = 7, vsync_value = 0)
                bell()
                restScreen.run(duration = 1, vsync_value = 0)
                notStim.run(duration = random.uniform(2,4), vsync_value = 0)

            trial += 1

    except UserEscape:
        print "User stopped the sequence."
    except:
        print "Unexpected error:"
        raise
    finally:
        try:
            #stop sequence
            blankScreen.run(duration = 1, vsync_value = 13,)
            blankScreen.run(duration = 1, vsync_value = 0,)
            redScreen.run(duration = 1, vsync_value = 5, wait_on_user_keypress = True,)
        except UserEscape:
            pass
        except:
            print "Unexpected error:"
            raise
    
    pygame.quit()
    sys.exit()

if __name__ == '__main__': main()

