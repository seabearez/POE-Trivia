from ahk import AHK
import io
import pandas as pd
import random
import re
import time

def main():
    # game file to get trivia answers from users
    # TODO unhash file below and replace gamefilepath with it
    gamefilepath = r"C:\Program Files (x86)\Grinding Gear Games\Path of Exile\logs\Client.txt"
    #gamefilepath = "test.txt"
    triviafilepath = "Test Questions.csv"
    ladderfilepath = "Ladder.csv"
    ahk = AHK(executable_path=r'C:\Program Files\AutoHotkey\v2\AutoHotkey64.exe')

    # number of questions to run before stopping
    questionNumber = 2

    # delay between each option
    multipleChoiceDelay = 0.5
    count = 0
    # bonuses for being the first person with a correct answer
    global first
    first = True
    firstBonus = 0.5
    # time given for people to provide an answer before correct answer given
    answerTime = 30
    timer = 0
    timeBetweenQuestions = 10
    # can change to # for global chat / other prefixes to identify chat lines and get username position
    testText = "<~MINE~>"
    # can change where the bot will output text between global / guild chat
    global prefix
    prefix = "#"
    global channel
    channel = "8502"

    # functions for people to interact
    viewRankingSession = "!score"
    viewRankingAlltime = "!alltime"
    viewCommands = "!commands"
    commands = [viewRankingSession, viewRankingAlltime, viewCommands]

    # trivia file loading in
    trivia = pd.read_csv(triviafilepath)
    ladder = pd.read_csv(ladderfilepath)
    rowCount = len(trivia.index)

    # load game & login
    loadout()
    time.sleep(30)

    # read entire txt file to track new additions
    with io.open(gamefilepath, mode='r', buffering=-1, encoding=None, errors='replace', newline=None, closefd=True) as logpath:
        while True:
            logline = logpath.readline()
            if not logline:
                break
            lastline = logline

    for i in range(questionNumber):
        # check if any unused questions remain. if not, reset all questions
        if countUnusedQuestions(trivia) < 1:
            resetQuestionsUsed(trivia)
        
        # cycle through index until a question that hasn't been asked recently is found
        index = random.randrange(0, rowCount, 1)
        while trivia.at[index, "Used?"] == 1:
            index = random.randrange(0, rowCount, 1)
        trivia.at[index, "Used?"] = 1
        count = count + 1

        # format and deliver question / multiple choices
        question(trivia, index, multipleChoiceDelay, count, ahk)
        timer = answerTime
        # remove all non-alphahumeric values using RE and get value at header/column location
        answerLetter = re.sub(r'[^a-zA-Z0-9]', '', trivia.at[index, "Correct Letter"].lower())
        answer = re.sub(r'[^a-zA-Z0-9]', '', trivia.at[index, "Correct Answer"].lower())

        # check changes to text file to see 
        while timer > 0:
            # instantiate intial log file to check for new lines to detect potential answers
            with io.open(gamefilepath, mode='r', buffering=-1, encoding=None, errors='replace', newline=None, closefd=True) as logpath:
                lines = logpath.readlines()

            # logic to isolate new lines added to log
            if lines[-1] != lastline:
                lastline = lines[-1]
                # if relevant line of text, check if updateable
                if testText in lines[-1]:
                    user, userAnswer = relevantInfo(lines[-1], testText)
                    if viewRankingSession in lines[-1]:
                        displayRanking(ladder, user, "Session", ahk)
                    if viewRankingAlltime in lines[-1]:
                        displayRanking(ladder, user, "All-time", ahk)
                    if viewCommands in lines[-1]:
                        showCommands(commands, ahk)
                    # RE to turn string into lower case alphanumerals
                    userAnswer = re.sub(r'[^a-zA-Z0-9]', '', userAnswer.lower())
                    ladder = updateLadder(ladder, user, userAnswer, answer, answerLetter, firstBonus)
            time.sleep(0.5)
            timer -= 1
        poeChat("Correct Answer is: " + str(trivia.at[index, "Correct Letter"]) + " / " + str(trivia.at[index, "Correct Answer"]), ahk)
        resetAlreadyAnswered(ladder)
        first = True
        time.sleep(timeBetweenQuestions)
    updateFile(ladder, ladderfilepath)
    updateFile(trivia, triviafilepath)


def question(trivia, index, delay, count, ahk):
    # text output note potential 255 charater limit causing issues
    poeChat(str(count) + ") " + str(trivia.at[index, "Category"]) + ": " + str(trivia.at[index, "Question"]), ahk)
    time.sleep(delay)
    poeChat("A: " + str(trivia.at[index, "A)"]), ahk)
    time.sleep(delay)
    poeChat("B: " + str(trivia.at[index, "B)"]), ahk)
    time.sleep(delay)
    poeChat("C: " + str(trivia.at[index, "C)"]), ahk)
    time.sleep(delay)
    poeChat("D: " + str(trivia.at[index, "D)"]), ahk)
    time.sleep(delay)
    poeChat("E: " + str(trivia.at[index, "E)"]), ahk)
    time.sleep(delay)
    poeChat("F: " + str(trivia.at[index, "F)"]), ahk)


def relevantInfo(line, testText):
    line = line.strip()
    # check if line is relevant chat to evaluate
    if testText not in line:
        return
    
    indexPosition = line.index(testText)
    line = line[indexPosition:]
    
    # adjust for space between guild/user. if non-guild use case remove space
    begOfUser = len(testText) + 1
    endOfUser = line.index(":")
    user = line[begOfUser:endOfUser]
    # adj for colon 
    answer = line[endOfUser + 1:]
    return user, answer


def updateLadder(ladder, user, userAnswer, answer, answerLetter, firstBonus):
    global first
    rowCount = len(ladder.index)
    # assume both answers have already been turned into only alphanum characters
    for index, row in ladder.iterrows():
        if user == row["charName"]:
            if ladder.at[index, "AlreadyAnswered"] == 0:
                if validAnswer(userAnswer, answer, answerLetter):
                    if not first:
                        ladder.at[index, "Session"] += ladder.at[index, "Session"] 
                        ladder.at[index, "All-time"] += ladder.at[index, "All-time"]
                    else:
                        ladder.at[index, "Session"] = ladder.at[index, "Session"] + 1 + firstBonus 
                        ladder.at[index, "All-time"] = ladder.at[index, "All-time"] + 1 + firstBonus
                        first = False
                ladder.at[index, "AlreadyAnswered"] = 1
            # once userfound and info updated, return out
            return ladder
        if index == rowCount - 1:
            if validAnswer(userAnswer, answer, answerLetter):
                if not first:
                    newRow = pd.Series({"charName": user, "Session": 1, "All-time": 1, "AlreadyAnswered": 1, "First": 0})
                else:
                    newRow = pd.Series({"charName": user, "Session": 1 + firstBonus, "All-time": 1 + firstBonus, "AlreadyAnswered": 1, "First": 0})
                    first = False
            else:
                newRow = pd.Series({"charName": user, "Session": 0, "All-time": 0, "AlreadyAnswered": 1, "First": 0})
            ladder = pd.concat([ladder, newRow.to_frame().T], ignore_index=True)
            return ladder


def validAnswer(userAnswer, answer, answerLetter):
    combo = answer + answerLetter
    if "".join(sorted(userAnswer)) == "".join(sorted(answer)):
        return True
    elif "".join(sorted(userAnswer)) == "".join(sorted(answerLetter)):
        return True
    elif "".join(sorted(userAnswer)) == "".join(sorted(combo)):
        return True
    else:
        return False


def updateFile(dataframe, file):
    dataframe.to_csv(file, index=False)


def countUnusedQuestions(dataframe):
    count = 0
    for index, row in dataframe.iterrows():
        if dataframe.at[index, "Used?"] == 0:
            count = count + 1
    return count


def resetQuestionsUsed(dataframe):
    for index, row in dataframe.iterrows():
        dataframe.at[index, "Used?"] = 0 


def resetAlreadyAnswered(dataframe):
    for index, row in dataframe.iterrows():
        dataframe.at[index, "AlreadyAnswered"] = 0


def displayRanking(ladder, user, timeframe, ahk):
    for index, row in ladder.iterrows():
        if user == row["charName"]:
            poeChat("@" + row["charName"] + " " + str(ladder.at[index, timeframe]), ahk)
            return
    poeChat("No score found", ahk)


def showCommands(commands, ahk):
    for command in commands:
        poeChat(str(command), ahk)


def loadout():
    # use v2 for better integration with UAI potentially
    ahk = AHK(executable_path=r'C:\Program Files\AutoHotkey\v2\AutoHotkey64.exe')

    # poe filepath location
    ahk.run_script('Run "C:\\Program Files (x86)\\Grinding Gear Games\\Path of Exile\\PathOfExile.exe"')

    # time for poe app to open
    # TODO add functionality to detect if patch and need to update timing?
    time.sleep(12)

    poe_window = ahk.win_get(title="Path of Exile")
    # log-in credentials for acount
    user = "poetriviabot@proton.me"
    password = "pathofexilechat"

    poe_window.activate()
    # wait for poe window to be activated
    time.sleep(2)

    # enter credentials
    ahk.send_input('{Tab}')
    ahk.send_input(user)
    ahk.send_input('{Tab}')
    time.sleep(1)
    ahk.send_input(password)
    ahk.send_input('{Enter}')

    # wait to load characters
    time.sleep(1)
    ahk.send_input('{Enter}')

    # wait to load into game
    time.sleep(10)
    poeChat("/hideout", ahk)
    poeChat("/global " + channel, ahk)


def poeChat(text, ahk):
    # function that presses enter pre/post msg
    ahk.send_input('{Enter}')
    ahk.send_input(prefix)
    ahk.send_input(text)
    ahk.send_input('{Enter}')


if __name__ == '__main__':
    main()