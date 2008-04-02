''' Guess the language of text.

    Based on guesslanguage.cpp by Jacob R Rideout for KDE
    http://websvn.kde.org/branches/work/sonnet-refactoring/common/nlp/guesslanguage.cpp?view=markup
    which itself is based on Language::Guess by Maciej Ceglowski
    http://languid.cantbedone.org/

    Copyright (c) 2008, Kent S Johnson

    C++ version is Copyright (c) 2006 Jacob R Rideout <kde@jacobrideout.net>
    Perl version is (c) 2004-6 Maciej Ceglowski
    
    This library is free software; you can redistribute it and/or
    modify it under the terms of the GNU Lesser General Public
    License as published by the Free Software Foundation; either
    version 2.1 of the License, or (at your option) any later version.

    This library is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
    Lesser General Public License for more details.

    You should have received a copy of the GNU Lesser General Public
    License along with this library; if not, write to the Free Software
    Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
    
    Note: Language::Guess is GPL-licensed. KDE developers received permission
    from the author to distribute their port under LGPL:
    http://lists.kde.org/?l=kde-sonnet&m=116910092228811&w=2
    
'''

import codecs, os, re, sys, unicodedata
from collections import defaultdict
from pprint import pprint
from blocks import unicodeBlock


MIN_LENGTH = 20

BASIC_LATIN = "en ceb ha so tlh id haw la sw eu nr nso zu xh ss st tn ts".split()
EXTENDED_LATIN = "cs af pl hr ro sk sl tr hu az et sq ca es fr de nl it da is nb sv fi lv pt ve lt tl cy".split()
ALL_LATIN = BASIC_LATIN + EXTENDED_LATIN
CYRILLIC = "ru uk kk uz mn sr mk bg ky".split()
ARABIC = "ar fa ps ur".split()
DEVANAGARI = "hi ne".split()

# NOTE mn appears twice, once for mongolian script and once for CYRILLIC
SINGLETONS = [
    ('Armenian', 'hy'),
    ('Hebrew', 'he'),
    ('Bengali', 'bn'),
    ('Gurmukhi', 'pa'),
    ('Greek', 'el'),
    ('Gujarati', 'gu'),
    ('Oriya', 'or'),
    ('Tamil', 'ta'),
    ('Telugu', 'te'),
    ('Kannada', 'kn'),
    ('Malayalam', 'ml'),
    ('Sinhala', 'si'),
    ('Thai', 'th'),
    ('Lao', 'lo'),
    ('Tibetan', 'bo'),
    ('Burmese', 'my'),
    ('Georgian', 'ka'),
    ('Mongolian', 'mn-Mong'),
    ('Khmer', 'km'),
]

PT = "pt_BR pt_PT".split()

UNKNOWN = 'No match'

models = {}

def _load_models():
    modelsDir = os.path.join(os.path.dirname(__file__), 'trigrams')
    modelsList = os.listdir(modelsDir)
    
    lineRe = re.compile(r"(.{3})\s+(.*)")
    for modelFile in modelsList:
        modelPath = os.path.join(modelsDir, modelFile)
        f = codecs.open(modelPath, 'r', 'utf-8')
        model = {}  # QHash<QString,int> model
        for line in f:
            m = lineRe.search(line)
            if m:
                model[m.group(1)] = int(m.group(2))
                
        models[modelFile] = model


_load_models()

def guessLanguage(text):
    if not text:
        return UNKNOWN
    
    if isinstance(text, str):
        text = unicode(text, 'utf-8')
    
    text = normalize(text)
    
    return _identify(text, find_runs(text))


def find_runs(text):
    ''' Count the number of characters in each character block '''
    run_types = defaultdict(int)

    totalCount = 0

    for c in text:
        if c.isalpha():
            block = unicodeBlock(c)
            run_types[block] += 1
            totalCount += 1

#    pprint.pprint(run_types)
    
    # return run types that used for 40% or more of the string
    # always return basic latin if found more than 15%.
    relevant_runs = []
    for key, value in run_types.items():
        pct = (value*100) / totalCount
        if pct >=40:
            relevant_runs.append(key)
        elif key == "Basic Latin" and ( pct >=15 ):
            relevant_runs.append(key)

    return relevant_runs


def _identify(sample, scripts):
    if len(sample) < 3:
        return UNKNOWN

    if "Hangul Syllables" in scripts or "Hangul Jamo" in scripts \
            or "Hangul Compatibility Jamo" in scripts or "Hangul" in scripts:
        return "ko"

    if "Greek and Coptic" in scripts:
        return "el"

    if "Katakana" in scripts or "Hiragana" in scripts or "Katakana Phonetic Extensions" in scripts:
        return "ja"

    if "CJK Unified Ideographs" in scripts or "Bopomofo" in scripts \
            or "Bopomofo Extended" in scripts or "KangXi Radicals" in scripts:

# This is in both Ceglowski and Rideout
# I can't imagine why...
#            or "Arabic Presentation Forms-A" in scripts
        return "zh"

    if "Cyrillic" in scripts:
        return check( sample, CYRILLIC )

    if "Arabic" in scripts or "Arabic Presentation Forms-A" in scripts or "Arabic Presentation Forms-B" in scripts:
        return check( sample, ARABIC )

    if "Devanagari" in scripts:
        return check( sample, DEVANAGARI )


    # Try languages with unique scripts
    for blockName, langName in SINGLETONS:
        if blockName in scripts:
            return langName

    if "Latin Extended Additional" in scripts:
        return "vi"

    if "Extended Latin" in scripts:
        latinLang = check( sample, EXTENDED_LATIN )
        if latinLang == "pt":
            return check(sample, PT)
        else:
            return latinLang
            
    if "Basic Latin" in scripts:
        return check( sample, ALL_LATIN )

    return UNKNOWN


def check(sample, langs):
    if len(sample) < MIN_LENGTH:
        return UNKNOWN

    scores = []
    model = createOrderedModel(sample)  # QMap<int,QString>

    for key in langs:
        lkey = key.lower()

        if lkey in models:
            scores.append( (distance(model, models[lkey]), key) )

    if not scores:
        return UNKNOWN

    # we want the lowest score, less distance = greater chance of match
#    pprint(sorted(scores))
    return min(scores)[1]


def createOrderedModel(content):
    ''' Create a list of trigrams in content sorted by frequency '''
    trigrams = defaultdict(int) # QHash<QString,int> 
    content = content.lower()
    
    for i in xrange(0, len(content)-2):
        trigrams[content[i:i+3]]+=1

    return sorted(trigrams.keys(), key=lambda k: (-trigrams[k], k))


spRe = re.compile(r"\s\s", re.UNICODE)
MAXGRAMS = 300

def distance(model, knownModel):
    dist = 0

    for i, value in enumerate(model[:MAXGRAMS]):
        if not spRe.search(value):
            if value in knownModel:
                dist += abs(i - knownModel[value])
            else:
                dist += MAXGRAMS

    return dist


def _makeNonAlphaRe():
    nonAlpha = [u'[^']
    for i in range(sys.maxunicode):
      c = unichr(i)
      if c.isalpha(): nonAlpha.append(c)
    nonAlpha.append(u']')
    nonAlpha = u"".join(nonAlpha)
    return re.compile(nonAlpha)


nonAlphaRe = _makeNonAlphaRe()
spaceRe = re.compile('\s+', re.UNICODE)
    
def normalize(u):
    ''' Convert to normalized unicode.
        Remove non-alpha chars and compress runs of spaces.
    '''
    u = unicodedata.normalize('NFC', u)
    u = nonAlphaRe.sub(' ', u)
    u = spaceRe.sub(' ', u)
    return u