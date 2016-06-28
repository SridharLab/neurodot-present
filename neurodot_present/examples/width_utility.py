"""
Ed Eskew

This utility is designed to find a range of widths in pixels that will be displayed during the words paradigm
presentation, with the consideration that the width of hebrew words displayed depends on the (random) latin to hebrew
cipher.
"""
import collections
from neurodot_present.present_lib import TextDisplay
import neurodot_present.resources

neurodot_present.present_lib.DEBUG = True
min_word_characters = 4  # characters in shortest word found in word_list.txt
max_word_characters = 6  # characters in longest word found in word_list.txt
font_size = 288
#latinText = TextDisplay(font_type="Arial.ttf")
#hebrewText = TextDisplay(font_type="ArialHebrew.ttf")
latinText = TextDisplay(font_type="Everson Mono Bold.ttf")
hebrewText = TextDisplay(font_type="Everson Mono Bold.ttf")
#arial_heightScaleFactor = 1.333333333
hebrew_alphabet = list(
    u"\u05D0\u05D1\u05D2\u05D3\u05D4\u05D5\u05D6\u05D7\u05D8\u05D9\u05DA\u05DB\u05DC\u05DD\u05DE\u05DF\u05E1\u05E2\u05E3\u05E4\u05E5\u05E6\u05E7\u05E8\u05E9\u05EA")


def getLatinWidth(str):
    return latinText.render_surface(text_content=str, font_size=font_size).get_width()


def getHebWidth(str):
    #return hebrewText.render_surface(text_content=str, font_size=int(font_size * arial_heightScaleFactor)).get_width()
    return hebrewText.render_surface(text_content=str, font_size=font_size).get_width()

# get list of words from text file
word_list = []
with neurodot_present.resources.load_wordlist() as list_file:
    for line in list_file.readlines():
        word_list.append(line.rstrip().upper())

# get character frequency tuple list of four letter words
fourLetterCounterList = []
for word in word_list:
    if len(word) == min_word_characters:
        charFreqList = collections.Counter(word).most_common()
        fourLetterCounterList.append(charFreqList)

# get character frequency tuple list of six letter words
sixLetterCounterList = []
for word in word_list:
    if len(word) == max_word_characters:
        charFreqList = collections.Counter(word).most_common()
        sixLetterCounterList.append(charFreqList)

# sort counter lists
for i in range(0, max_word_characters):
    def getKey(el):
        try:
            return el[i][1]
        except IndexError:
            pass
    fourLetterCounterList.sort(key=getKey)
    sixLetterCounterList.sort(key=getKey)

# get character freqency tuple lists for the two four and six letter words
# with most repeated characters
fourLetterWord = fourLetterCounterList[0]
sixLetterWord = sixLetterCounterList[0]

# get lists of repetitions for each character
fourLetterReps = []
for tup in fourLetterWord:
    fourLetterReps.append(tup[1])
sixLetterReps = []
for tup in sixLetterWord:
    sixLetterReps.append(tup[1])

# get companion list of pixel widths of hebrew_alphabet
charWidthList = []
for char in hebrew_alphabet:
    charWidth = getHebWidth(char)
    charWidthList.append(charWidth)

# sort hebrew_alphabet by charWidthList
sortedBigToSmall = sorted(hebrew_alphabet, key=lambda char: charWidthList[
                          hebrew_alphabet.index(char)], reverse=True)
sortedSmallToBig = sorted(hebrew_alphabet, key=lambda char: charWidthList[
                          hebrew_alphabet.index(char)])

# get shortest possible hebrew word
shortestHebWord = ""
for i in range(0, len(fourLetterReps)):
    shortestHebWord += sortedSmallToBig[i] * fourLetterReps[i]

# get longest possible hebrew word
longestHebWord = ""
for i in range(0, len(sixLetterReps)):
    longestHebWord += sortedBigToSmall[i] * sixLetterReps[i]

# get widths of shortest and longest Hebrew words
shortestHebWidth = getHebWidth(shortestHebWord)
longestHebWidth = getHebWidth(longestHebWord)

# get shortest and longest English words and widths
shortestLatinWidth = 1000000000000  # this has to be longer in pixels than every word that could be displayed
longestLatinWidth = 0
for word in word_list:
    width = getLatinWidth(word)
    if width < shortestLatinWidth:
        shortestLatinWidth = width
        shortestLatinWord = word
    if width > longestLatinWidth:
        longestLatinWidth = width
        longestLatinWord = word

# get raw unicode for hebrew characters
shortestHebWord = shortestHebWord.encode('raw_unicode_escape')
longestHebWord = longestHebWord.encode('raw_unicode_escape')

# print results
print ""
print 'Shortest Latin: ','{0:>36} -{1:>5} pixels'.format(shortestLatinWord, shortestLatinWidth)
print 'Shortest Hebrew:', '{0:>36} -{1:>5} pixels'.format(shortestHebWord, shortestHebWidth)
print 'Longest Latin:  ', '{0:>36} -{1:>5} pixels'.format(longestLatinWord, longestLatinWidth)
print 'Longest Hebrew: ', '{0:>36} -{1:>5} pixels'.format(longestHebWord, longestHebWidth)
print ""
