"""
    Hangman in Python
    -------------------
    https://github.com/J0w03L/py-hangman
    https://j0w03l.me
    -------------------
"""

import requests
import time
import urllib
import logging

# Endpoints
WORD_RAND_API = "https://random-word-api.herokuapp.com/word"
WORD_DEF_API  = "https://api.dictionaryapi.dev/api/v2/entries/en/{word}"

# Game Config
DEBUG           = False
MAX_GUESSES     = 10
API_DELAY       = 2
API_MAX_ERRORS  = 3
ALLOWED_LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

# Debug Logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG if DEBUG else logging.ERROR)

def main():
    while True:
        playHangman()

        playAgain = True

        while True:
            doPlayAgain = str.upper(input("Do you want to play again? (Y/N): "))

            if doPlayAgain not in "YN" or len(doPlayAgain) != 1:
                print("Please type Y or N.")
                continue

            if doPlayAgain == "N": playAgain = False
            
            break

        if not playAgain: break

def playHangman():
    randWord            = pickWord()
    guesses             = []
    wordGuesses         = []
    incorrectGuesses    = 0
    winner              = False
    playing             = True

    while True:
        stage                       = incorrectGuesses
        hangmanArt                  = getHangmanArt(stage)
        wordPreview, wordGuessed    = getWordPreview(randWord, guesses)
        guess                       = None
        guessType                   = None

        print(f"\n------\n{hangmanArt}{wordPreview}\n")
        print(f"Available Letters: {' '.join([letter for letter in ALLOWED_LETTERS if letter not in guesses])}")

        if wordGuessed:
            winner = True
            break

        if stage >= MAX_GUESSES: break

        while True:
            guess = str.upper(input("Make a guess: "))

            if len(guess) == 0:
                # Nothing was entered, try again.
                continue

            if len(guess) == 1:
                # User is guessing a letter.

                if guess in guesses:
                    print("You have already guessed this letter!")
                    continue

                if guess not in ALLOWED_LETTERS:
                    print("This is not a valid letter!")
                    continue

                guessType = "letter"
                break

            # User is guessing the word.
            if guess in wordGuesses:
                print("You have already guessed this word!")
                continue

            guessType = "word"
            break
        
        match guessType:
            case "letter":
                guesses.append(guess)

                if guess not in str.upper(randWord["word"]):
                    incorrectGuesses += 1
                    print("This guess was incorrect!")
                    continue
                
                print("This guess was correct!")
                continue
            case "word":
                if guess != str.upper(randWord["word"]):
                    incorrectGuesses += 1
                    wordGuesses.append(guess)
                    print("This guess was incorrect!")
                    continue

                print("This guess was correct!")
                winner = True
                break

        
    print("\nCongratulations; you have guessed the word!\n" if winner else "\nOh no! Better luck next time!\n")
    printWordInfo(randWord)

def pickWord() -> dict:
    foundWordWithDef    = False
    firstAPIAttempt     = True
    apiErrorCount       = 0
    apiErrorCodes       = []
    randWord            = {"word": None, "meanings": None}

    print("Picking a word; please wait...")

    while not foundWordWithDef:
        # If we've encountered too many API errors, bail out.
        if apiErrorCount >= API_MAX_ERRORS:
            logging.debug("Too many API errors; bailing out!")
            break

        # If this is not our first attempt at getting a word from the APIs, wait before making an attempt so we can't hit any ratelimits.
        if not firstAPIAttempt:
            logging.debug(f"Sleeping for {API_DELAY} seconds between API request cycles...")
            time.sleep(API_DELAY)

        firstAPIAttempt = False

        # Get a random word from the random word API.
        logging.debug("Attempting to get a word from the random word API...")
        wordRandRequestHeaders = {"User-Agent": "py-hangman"}
        wordRandRequest = requests.get(WORD_RAND_API, headers = wordRandRequestHeaders)
        
        # Check the status code of the API response to ensure everything went smoothly.
        if wordRandRequest.status_code != 200:
            # Try again.
            logging.debug(f"Random word API returned non-200 status code ({wordRandRequest.status_code})!")
            apiErrorCodes[apiErrorCount] = wordRandRequest.status_code
            apiErrorCount += 1
            continue

        # Parse the response JSON
        wordRandResponse    = wordRandRequest.json()
        randWord["word"]    = wordRandResponse[0]
        logging.debug(f"Current random word candidate: \"{randWord['word']}\"")

        # If we get here, we successfully got a random word from the API.
        # But we need to check if our definition API has a definition for the word.
        logging.debug("Attempting to get a definition for our word from the definition API...")
        wordDefRequest = requests.get(WORD_DEF_API.format(word = urllib.parse.quote(randWord["word"])))

        # Check the status code just like we did with the last request.
        if wordDefRequest.status_code != 200:
            # Try again.
            logging.debug(f"Word definition API returned non-200 status code ({wordDefRequest.status_code})!")

            # Don't track 404 codes as these are just missing words.
            if wordDefRequest.status_code != 404:
                apiErrorCodes.append(wordRandRequest.status_code)
                apiErrorCount += 1
            
            continue
        
        # Parse the response JSON
        logging.debug(wordDefRequest.json())
        wordDefResponse         = wordDefRequest.json()[0]
        randWord["meanings"]    = wordDefResponse["meanings"]

        logging.debug(f"Found the word \"{randWord['word']}\"!")
        foundWordWithDef = True
    
    if not foundWordWithDef:
        # We were unable to get a word from the APIs due to encountering too many errors.
        print(
             "Sorry, but we were unable to get a word for you (too many API errors).\nAre you connected to the internet?"
             "\n\n"
            f"Error Codes: {', '.join([str(code) for code in apiErrorCodes])}"
        )
        exit()

    return randWord

def printWordInfo(wordData: dict):
    print(f"The word was \"{wordData['word']}\"!\n")
    logging.debug(wordData)

    print("    Definitions:")

    for meaning in wordData["meanings"]:
        for definition in meaning["definitions"]:
            print(f"    {meaning['partOfSpeech']}: {definition['definition']}")
            if "example" in definition: print(f"        Example: {definition['example']}")

def getHangmanArt(stage: int):
    ret = ""

    match stage:
        case 0:
            ret = ("                 \n" * 9)
        case 1:
            ret = ("                 \n" * 8 +
                   "===+=============\n")
        case 2:
            ret = ("                 \n" +
                   "   |             \n" * 7 +
                   "===+=============\n")
        case 3:
            ret = ("   ________      \n" +
                   "   |/            \n" +
                   "   |             \n" * 6 +
                   "===+=============\n")
        case 4:
            ret = ("   ________      \n" +
                   "   |/     |      \n" +
                   "   |      |      \n" +
                   "   |             \n" * 5 +
                   "===+=============\n")
        case 5:
            ret = ("   ________      \n" +
                   "   |/     |      \n" +
                   "   |      |      \n" +
                   "   |      O      \n" +
                   "   |             \n" * 4 +
                   "===+=============\n")
        case 6:
            ret = ("   ________      \n" +
                   "   |/     |      \n" +
                   "   |      |      \n" +
                   "   |      O      \n" +
                   "   |      +      \n" +
                   "   |      |      \n" +
                   "   |             \n" * 2 +
                   "===+=============\n")
        case 7:
            ret = ("   ________      \n" +
                   "   |/     |      \n" +
                   "   |      |      \n" +
                   "   |      O      \n" +
                   "   |     -+      \n" +
                   "   |      |      \n" +
                   "   |             \n" * 2 +
                   "===+=============\n")
        case 8:
            ret = ("   ________      \n" +
                   "   |/     |      \n" +
                   "   |      |      \n" +
                   "   |      O      \n" +
                   "   |     -+-     \n" +
                   "   |      |      \n" +
                   "   |             \n" * 2 +
                   "===+=============\n")
        case 9:
            ret = ("   ________      \n" +
                   "   |/     |      \n" +
                   "   |      |      \n" +
                   "   |      O      \n" +
                   "   |     -+-     \n" +
                   "   |      |      \n" +
                   "   |     /       \n" +
                   "   |             \n" +
                   "===+=============\n")
        case 10:
            ret = ("   ________      \n" +
                   "   |/     |      \n" +
                   "   |      |      \n" +
                   "   |      O      \n" +
                   "   |     -+-     \n" +
                   "   |      |      \n" +
                   "   |     / \     \n" +
                   "   |             \n" +
                   "===+=============\n")
    
    return ret

# Returns a tuple of str and bool.
# The string is the word preview, and the bool is whether or not the word has been fully displayed.
def getWordPreview(wordData: dict, guesses: list) -> tuple[str, bool]:
    word            = wordData["word"]
    wordChars       = list(word)
    fullyDisplayed  = True
    ret = "The word is: "

    for char in wordChars:
        char = str.upper(char)

        # Is it a guessable character? If not, always display it.
        # Otherwise, has the user guessed this character already? If they have, also display it.
        if char in guesses or char not in ALLOWED_LETTERS:
            ret += char
            continue
        
        # Neither were true, display a blank instead.
        ret += "_"
        fullyDisplayed = False
    
    return (ret, fullyDisplayed)

if __name__ == "__main__": main()