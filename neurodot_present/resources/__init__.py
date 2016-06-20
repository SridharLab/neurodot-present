import os
module_path = os.path.dirname(__file__)

def load_wordlist():
    fp = os.path.sep.join((module_path, "word_list.txt"))
    wf = open(fp,'r')
    return wf
    
def get_fontpath(font_type):
    fp = os.path.sep.join((module_path, font_type))
    return fp
