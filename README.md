Attempts to determine the natural language of a selection of Unicode (utf-8) text.

Based on [guesslanguage.cpp](http://websvn.kde.org/branches/work/sonnet-refactoring/common/nlp/guesslanguage.cpp?view=markup)
by Jacob R Rideout for KDE which itself is based on
Language::Guess <http://languid.cantbedone.org/> by Maciej Ceglowski.

Detects over 60 languages - all languages listed in the trigrams
directory plus Japanese, Chinese, Korean and Greek.

`guess_language` uses heuristics based on the character set and trigrams in a sample text
to detect the language. It works better with longer samples and will be confused if
the sample text includes markup such as HTML tags.

**Note**: I (Kent Johnson) am no longer using or maintaining this code. Phi-Long DO maintains a Python 3 version (with support for lib3to2) at https://bitbucket.org/spirit/guess_language.

Usage
=====

The main entry points all take a single string as input and return a language identifier.
The string must be Unicode or UTF-8 text. The language identifer can be the language name
in English, the two- or three-letter IANA language code, a language ID or a tuple containing
all three codes.

The primary entry points, and the return values, are as follows::

    guessLanguage(txt) - IANA language code
    guessLanguageTag(txt) - IANA language code (same as guessLanguage)
    guessLanguageName(txt) - Language name in English
    guessLanguageId(txt) - language ID
    guessLanguageInfo(txt) - tuple of (IANA code, id, name)
