#Name: Vivian Li
#Andrew ID: vdli
#Section: B

import ast
import librosa
import math

from multiprocessing import Process
#https://stackoverflow.com/questions/323972/is-there-any-way-to-kill-a-thread-in-python
import numpy as np
import os
import pyaudio
from pydub import AudioSegment
import random
import time
from tkinter import *

################################################################################
#General Helpers
################################################################################

def almostEqual(d1, d2, difference): #slightly modified from course website
	return (abs(d2 - d1) < difference)

################################################################################
#Audio
################################################################################

#Loading audio from a path
def loadSongLibrosa(path, d = None):
#returns song and sample rate
	return librosa.load(path, duration = d)

def loadSongPydub(path, d = None):
#returns a pydub AudioSegment
	fileType = path.split(".")[-1]
	song = AudioSegment.from_file(path, format = fileType)
	if d != None:
		duration = d * 1000 #convert to milliseconds
		return song[:duration]
	return song

#Beats/Onsets and converting to a beatmap	
def getBeatTimes(song, sr, bpm):
#returns a numpy array of beat times within 10 milliseconds of a note
	song = librosa.effects.percussive(song)
	beatTimes = librosa.beat.beat_track(song, sr,
		units = 'time', start_bpm = bpm, tightness = 10)[1]
	return beatTimes
	
def getOnsetTimes(song, sr):
#returns a numpy array of note times
	song = librosa.effects.harmonic(song)
	onsetTimes = librosa.onset.onset_detect(song, sr,
		units = 'time', hop_length = sr//10)
	return onsetTimes
	
def removeDuplicatesBeatmap(beatmap):
#removes time indexes too close (within 0.1 s) in a list
	i = 0
	while i < len(beatmap) - 1:
		if almostEqual(beatmap[i][0], beatmap[i + 1][0], 0.25):
			beatmap.pop(i + 1)
		else:
			i += 1

def makeBeatmap(beats, difficulty):
	beatmap = []
	beatList = beats.tolist()
	while len(beatList) != 0:
		beatZero = round(beatList.pop(0), 2)

		noteType = random.choice(["up", "down", "left", "right"])
		if difficulty == "easy":
			beatmap.append((beatZero, "beat"))
		else:
			beatmap.append((beatZero, random.choice(['beat', noteType])))
	return beatmap

def makeBeatmapHard(beats, onset):
#merges beat numpy array and onset numpy array into a beatmap
	beatmap = []
	beatList = beats.tolist()
	onsetList = onset.tolist()
	while len(beatList) != 0 and len(onsetList) != 0:
		beatZero = round(beatList.pop(0), 2)
		onsetZero = round(onsetList.pop(0), 2)

		noteType = random.choice(["up", "down", "left", "right"])
		if almostEqual(beatZero, onsetZero, 0.25):
			beatmap.append((beatZero, noteType))
		elif beatZero < onsetZero:
			beatmap.append((beatZero, noteType))
			onsetList.insert(0, onsetZero)
		else:
			beatmap.append((onsetZero, noteType))
			beatList.insert(0, beatZero)
	return beatmap

################################################################################

def playSong(song): #takes an audioSegment
#plays audio through pyaudio
	p = pyaudio.PyAudio()

	stream = p.open(format = p.get_format_from_width(song.sample_width),
					channels = song.channels,
					rate = song.frame_rate,
					output = True)

	stream.write(song.raw_data)

	stream.stop_stream()
	stream.close()

	p.terminate()

################################################################################
#Storage and Retrieval
################################################################################

def saveSongs(): #updates our song-beatmap file with newly added songs
	if "beatmaps.txt" not in os.listdir(os.curdir):
		open("beatmaps.txt", "x")
	f = open("beatmaps.txt", "r")
	songList = set()
	for song in os.listdir("songs"):
		songList.add(song)
	currentBeatmaps = f.readlines()
	currentSongs = dict()
	for beatmap in currentBeatmaps:
		currentSongs[beatmap.split("|")[0] + beatmap.split("|")[1]] = beatmap
	f = open("beatmaps.txt", "w")
	for song in songList:
		for difficulty in ["easy", "medium", "hard"]:
			if song+difficulty in currentSongs:
				f.write(currentSongs[song + difficulty])
			else:
				newBeatmap = getBeatmap(song, difficulty)
				f.write(song + "|" + difficulty + "|" + str(newBeatmap) + "\n")
	f.close()

def getSongs(): #stores songs from beatmaps.txt into a dictionary
	f = open("beatmaps.txt", "r")
	beatmaps = dict()
	beatmapList = f.readlines()
	for beatmap in beatmapList:
		info = beatmap.split("|")
		songName = info[0] + "|" + info[1]
		beatmaps[songName] = ast.literal_eval(info[2].strip())
		#https://stackoverflow.com/questions/8490955/converting-a-string-to-a-list-of-tuples
	return beatmaps

def getBeatmap(song, difficulty):
#get a song's beatmap from its name and the chosen difficulty
	path = "songs" + os.sep + song
	songSeg = loadSongPydub(path)
	song, sr = loadSongLibrosa(path)
	if difficulty == "easy": bpm = 60.0
	elif difficulty == "medium": bpm = 90.0
	else: bpm = 120.0
	beats = getBeatTimes(song, sr, bpm)
	onsets = getOnsetTimes(song, sr)
	if difficulty != "hard":
		beatmap = makeBeatmap(beats, difficulty)
		removeDuplicatesBeatmap(beatmap)
		return beatmap
	beatmap = makeBeatmapHard(beats, onsets)
	removeDuplicatesBeatmap(beatmap)
	return beatmap

def saveHighscores(data): #saves player highscores into a file
	f = open("highscores.txt", "w")
	for song in data.highscores:
		f.write(song + "," + str(data.highscores[song]) + "\n")

def getHighscores(): #gets dictionary of player highscores from file
	if "highscores.txt" not in os.listdir(os.curdir):
		open("highscores.txt", "x")
	f = open("highscores.txt", "r")
	highscores = dict()
	highscoresList = f.readlines()
	for highscore in highscoresList:
		songName = highscore.split(",")[0].strip()
		score = highscore.split(",")[1].strip()
		highscores[songName] = float(score)
	return highscores

def updateHighscore(song, score, data): #updates the highscore dict in data
	if song not in data.highscores:
		data.highscores[song] = score
	else:
		if data.highscores[song] < score:
			data.highscores[song] = score

################################################################################
#Class Helpers
################################################################################

def getDXY(startX, startY, endX, endY, data):
	distanceX = endX - startX
	distanceY = endY - startY
	runsPerSecond = 1500/data.timerDelay
	return (distanceX/runsPerSecond, distanceY/runsPerSecond)

def getDR(startR, endR, data):
	distanceR = endR - startR
	runsPerSecond = 1500/data.timerDelay
	return (distanceR/runsPerSecond)

def isNotValidXY(data, endX, endY, cWidth, cHeight):
	if not (100 < endX < cWidth - 100) or not (100 < endY < cHeight - 100):
		return True
	return False

def getEndXY(data, index):
	endX, endY = data.width//2, data.height//2
	if len(data.currentNotes) > 0:
		prevNote = data.currentNotes[-1]
		prevX, prevY = prevNote.endX, prevNote.endY
		dx = math.cos(index) * random.randint(100, 200)
		dy = math.sin(index) * random.randint(100, 200)
		endX, endY = prevX + dx, prevY + dy
		if isNotValidXY(data, endX, endY, data.width, data.height):
			endX, endY = data.width//2, data.height//2
	return endX, endY

def drawDirection(canvas, cx, cy, r, direction):
	if direction == "up":
		p1, p2, p3 = (cx, cy - r), (cx - r, cy + r), (cx + r, cy + r)
	elif direction == "down":
		p1, p2, p3 = (cx, cy + r), (cx - r, cy - r), (cx + r, cy - r)
	elif direction == "right":
		p1, p2, p3 = (cx - r, cy - r), (cx - r, cy + r), (cx + r, cy)
	elif direction == "left":
		p1, p2, p3 = (cx + r, cy - r), (cx + r, cy + r), (cx - r, cy)

	if direction == 'beat':
		canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill = "dark blue")
	else:
		canvas.create_polygon(p1, p2, p3, fill = "dark blue")

def drawCube(canvas, cx, cy, r, dx, dy, dr, color, stipple):
	front = ((cx - r, cy - r), (cx + r, cy - r),
			(cx + r, cy + r), (cx - r, cy + r))
	nx, ny, nr = cx - 2 * dx, cy - 2 * dy, r - 2 * dr
	back = ((nx - nr, ny - nr), (nx + nr, ny - nr),
			(nx + nr, ny + nr), (nx - nr, ny + nr))
	canvas.create_rectangle(back[0], back[2], fill = color, stipple = stipple)
	for i in range(4):
		canvas.create_polygon(back[i], front[i], front[(i + 1) % 4],
		back[(i + 1) % 4], fill = color, outline = "black", stipple = stipple)
	canvas.create_rectangle(front[0], front[2], fill = color, stipple = stipple)
################################################################################
#Classes
################################################################################

class Note(object):
	def __init__(self, data, index, direction = None):
#notes start in the center of the screen and go to a random position
#their radius increases from 10 to 30
		self.cx = data.width/2
		self.cy = data.height/2
		self.r = 10

		self.endX, self.endY = getEndXY(data, index)
		self.endR = 30

		self.dx, self.dy = getDXY(self.cx, self.cy, self.endX, self.endY, data)
		self.dr = getDR(self.r, self.endR, data)

		self.direction = direction
		self.index = index
		self.color = "light blue"

		self.maxScore = 300
		self.stipples = ["gray12", "gray25", "gray50", "gray75", ""]
		self.stIndex = 0

	def move(self):
		self.cx += self.dx
		self.cy += self.dy
		self.r += self.dr
		rLimit = self.endR - self.dr * (len(self.stipples) - self.stIndex - 2)
		if self.r > rLimit:
			self.stIndex += 1
			if self.stIndex == len(self.stipples):
				self.stIndex = len(self.stipples) - 1

	def checkForLimit(self, data):
		if self.r >= self.endR + 6:
			data.health -= 10
			data.currentNotes.remove(self)
			data.scoreCounts[0] += 1
			data.noteIndex += 1

	def draw(self, canvas, currIndex):
		cx, cy, r = self.cx, self.cy, self.r
		stipple = self.stipples[self.stIndex]
		drawCube(canvas, cx, cy, r, self.dx, self.dy, self.dr, self.color,
				stipple)
		drawDirection(canvas, cx, cy, r//2, self.direction)

	def checkIfSwiped(self, data):
		cx, cy, r = self.cx, self.cy, self.r
		stX, stY = data.pressX, data.pressY
		edX, edY = data.releaseX, data.releaseY
		noteL, noteR, noteU, noteD = cx - r, cx + r, cy - r, cy + r

		if almostEqual(stY + edY, cy*2, r*2):
			if stX <= noteL and edX >= noteR:
				return "right" == self.direction or self.direction == "beat"
			elif stX >= noteR and edX <= noteL:
				return "left" == self.direction or self.direction == "beat"

		if almostEqual(stX + edX, cx*2, r*2):
			if stY <= noteU and edY >= noteD:
				return "down" == self.direction or self.direction == "beat"
			elif stY >= noteD and edY <= noteU:
				return "up" == self.direction or self.direction == "beat"
		return False

	def getScore(self):
		if self.r >= self.endR:
			return 300
		elif self.endR - self.r <= 2:
			return 200
		elif self.endR - self.r <= 5:
			return 100
		else:
			return 0

	def addScore(self, data):
		score = self.getScore()
		data.score += score

		if score == 300:
			data.scoreCounts[3] += 1
		elif score == 200:
			data.scoreCounts[2] += 1
		elif score == 100:
			data.scoreCounts[1] += 1
		else: data.scoreCounts[0] += 1

	def getHealth(self):
		if self.dx == 0 and self.dy == 0:
			return 10
		elif self.endR - self.r <= 2:
			return 5
		elif self.endR - self.r <= 5:
			return 0
		else:
			return -10

	def addHealth(self, data):
		health = self.getHealth()
		data.health += health
		if data.health > 100: data.health = 100

class harmfulNote(Note):
	def __init__(self, data, index, direction = None):
		super().__init__(data, index, direction)
		self.color = "red"

	def getScore(self):
		return -300

	def getHealth(self):
		return -10

	def checkForLimit(self, data):
		if self.r >= self.endR + 6:
			data.score += 300
			data.health += 10
			if data.health > 100: data.health = 100

			data.currentNotes.remove(self)
			data.scoreCounts[3] += 1
			data.noteIndex += 1

class helpfulNote(Note):
	def __init__(self, data, index, direction = None):
		super().__init__(data, index, direction)
		self.color = "green"
		self.maxScore = 600

	def getScore(self):
		return super().getScore() * 2

class songDisplay(object):
	def __init__(self, fileName, songName, difficulty, beatmap, index):
		self.fileName = fileName
		self.songName = songName
		self.difficulty = difficulty
		self.beatmap = beatmap
		self.index = index

	def draw(self, canvas, data):
		x0 = data.width//10
		y0 = data.height * 1/5 + data.height * (self.index)/5
		x1 = data.width//2
		y1 = data.height * 1/5 + data.height * (self.index + 1)/5

		if data.displayIndex == self.index:
			canvas.create_rectangle(x0, y0, x1, y1, fill = "yellow2")
		else:
			canvas.create_rectangle(x0, y0, x1, y1, fill = "light blue")
		canvas.create_text(data.width * 3/10, (y0 + y1)//2,
				text = self.songName + "\t" + self.difficulty.upper(),
				font = "System 16", width = x1 - x0)

	def onClick(self, x, y, data):
		x0 = data.width//10
		y0 = data.height * 1/5 + data.height * (self.index)/5
		x1 = data.width//2
		y1 = data.height * 1/5 + data.height * (self.index + 1)/5

		if x0 < x < x1 and y0 < y < y1:
			if data.displayIndex != self.index:
				data.displayIndex = self.index
			else:
				initGame(data)

################################################################################
#Animation
################################################################################

################################################################################
#Button Helpers
################################################################################

def goBack(data):
	if data.screen == "select":
		data.screen = "title"
	if data.screen == "end":
		data.screen = "select"
def helpToggle(data):
	data.help = not data.help

def titleMenuToggle(data):
	data.titleMenu = not data.titleMenu

def turnPageLeft(data):
	data.currentPage -= 1
	if data.currentPage < 1: data.currentPage = 1
def turnPageRight(data):
	data.currentPage += 1
	if data.currentPage > data.totalPages: data.currentPage = data.totalPages

################################################################################
#Button Inits
################################################################################

def initGenButtons(canvas, data):
	data.backButton = Button(canvas, text = "Back")
	data.backButton.configure(font = "System 15 bold", bg = "pale turquoise",
			activebackground = "light blue", command = lambda: goBack(data))
	#https://stackoverflow.com/questions/3704568/tkinter-button-command-activates-upon-running-program

	data.helpButton = Button(canvas, text = "?")
	data.helpButton.configure(font = "System 15 bold", bg = "pale turquoise",
		activebackground = "light blue", command = lambda: helpToggle(data))
	#https://stackoverflow.com/questions/3704568/tkinter-button-command-activates-upon-running-program

def initTitleButtons(canvas, data):
	data.titleImage = PhotoImage(file="images" + os.sep + "beatsu_title.png")
	data.titleButton = Button(canvas, image = data.titleImage, 
		command = lambda: titleMenuToggle(data))
	#https://stackoverflow.com/questions/3704568/tkinter-button-command-activates-upon-running-program

	data.startButton = Button(canvas, text = "Start")
	data.startButton.configure(font = "System 25 bold", bg = "pale turquoise",
			activebackground = "light blue", command = lambda: initSelect(data))
	#https://stackoverflow.com/questions/3704568/tkinter-button-command-activates-upon-running-program

	data.quitButton = Button(canvas, text = "Quit", command = canvas.quit)
	data.quitButton.configure(font = "System 25 bold", bg = "light slate blue",
			activebackground = "dark slate blue")

def initSelectButtons(canvas, data):
	data.leftButton = Button(canvas, text = "<")
	data.leftButton.configure(font = "System 25 bold",
			command = lambda: turnPageLeft(data))
	#https://stackoverflow.com/questions/3704568/tkinter-button-command-activates-upon-running-program

	data.rightButton = Button(canvas, text = ">")
	data.rightButton.configure(font = "System 25 bold",
			command = lambda: turnPageRight(data))
	#https://stackoverflow.com/questions/3704568/tkinter-button-command-activates-upon-running-program

	data.playButton = Button(canvas, text = "Play Song")
	data.playButton.configure(font = "System 15 bold", bg = "pale turquoise",
			activebackground = "light blue", command = lambda: initGame(data))
	#https://stackoverflow.com/questions/3704568/tkinter-button-command-activates-upon-running-program

def initEndButtons(canvas, data):
	data.replayButton = Button(canvas, text = "Replay")
	data.replayButton.configure(font = "System 15 bold", bg = "pale turquoise",
			activebackground = "light blue", command = lambda: initGame(data))
	#https://stackoverflow.com/questions/3704568/tkinter-button-command-activates-upon-running-program

def initButtons(canvas, data):
	initGenButtons(canvas, data)
	initTitleButtons(canvas, data)
	initSelectButtons(canvas, data)
	initEndButtons(canvas, data)

################################################################################
#Screen Init Helpers
################################################################################

def getSongDisplays(songList):
	songDisplays = []
	songPage = []
	index = 0

	for song in songList:
		fileName = song.split("|")[0]
		songName = fileName[:-4]
		difficulty = song.split("|")[1]
		beatmap = songList[song]
		songDis = songDisplay(fileName, songName, difficulty, beatmap, index)
		songPage.append(songDis)
		index += 1

		if index == 3:
			index = 0
			songDisplays.append(songPage)
			songPage = []

	return songDisplays

def getSong(data):
	currSongDisplay = data.songDisplays[data.currentPage-1][data.displayIndex]

	data.songName = currSongDisplay.songName + "|" + currSongDisplay.difficulty
	data.songSeg = loadSongPydub("songs" + os.sep + currSongDisplay.fileName)
	data.beatmap = currSongDisplay.beatmap

################################################################################
#Screen Inits
################################################################################

def initTitle(data):
	data.curBackground = PhotoImage(
			file = "images" + os.sep + "background_title.png")

	data.titleMenu = False

	data.screen = "title"

def initSelect(data):
	data.curBackground = PhotoImage(
		file = "images" + os.sep + "background_title.png")

	data.songList = getSongs()
	data.songDisplays = getSongDisplays(data.songList)

	data.displayIndex = 0
	data.currentPage = 1
	data.totalPages = len(data.songDisplays)

	data.screen = "select"

def initGame(data):
	data.curBackground = PhotoImage(
		file = "images" + os.sep + "background_game.png")
	data.healthImage = PhotoImage(
		file = "images" + os.sep + "health_image.png")

	getSong(data)

	data.currentNotes = []
	data.beatmapIndex = 0
	data.noteIndex = 0

	data.score = 0
	data.totalScore = 1
	data.scoreCounts = [0, 0, 0, 0]

	data.startTime = time.time()

	data.health = 100

	data.screen = 'game'
	data.process = Process(target=playSong, args = (data.songSeg,),
						daemon = True)
	data.process.start()

def initEnd(data):
	data.percentage = round(data.score/data.totalScore * 100, 2)

	if data.health > 0:
		updateHighscore(data.songName, data.percentage, data)
		saveHighscores(data)

	data.screen = 'end'

################################################################################
#Screen Mouse Pressed
################################################################################

def pressedSelect(event, data):
	for display in data.songDisplays[data.currentPage - 1]:
		display.onClick(event.x, event.y, data)

def pressedGame(event, data):
	data.pressX = event.x
	data.pressY = event.y

################################################################################
#Screen Mouse Released
################################################################################

def releasedGame(event, data):
	data.releaseX = event.x
	data.releaseY = event.y

	for note in data.currentNotes:
		if note.checkIfSwiped(data):
			note.addScore(data)
			note.addHealth(data)
			data.currentNotes.remove(note)
			data.noteIndex += 1
			break

################################################################################
#Screen Key Pressed
################################################################################

def keySelect(event, data):
	if event.keysym == "Return":
		initGame(data)

	if event.keysym == "Left":
		turnPageLeft(data)
	if event.keysym == "Right":
		turnPageRight(data)

	if event.keysym == "Up":
		data.displayIndex = (data.displayIndex - 1)%3
	if event.keysym == "Down":
		data.displayIndex = (data.displayIndex + 1)%3

	if event.keysym == "Escape":
		init(data)

def keyEnd(event, data):
	if event.keysym == "Escape":
		initSelect(data)

	if event.char == "r":
		initGame(data)

################################################################################
#Screen Timer Fired
################################################################################

def timerGame(data):
	currentTime = time.time()
	songTime = currentTime - data.startTime

	if (songTime > len(data.songSeg)/1000 and
		 data.noteIndex == len(data.beatmap)) or data.health <= 0:
		initEnd(data)
		data.process.terminate()

	if data.beatmapIndex < len(data.beatmap):
		second, direction = data.beatmap[data.beatmapIndex]
		if (songTime - 1.4) >= second:
			rand = random.randint(1, 20)
			if rand == 1:
				note = harmfulNote(data, data.beatmapIndex, direction)
			elif rand == 20:
				note = helpfulNote(data, data.beatmapIndex, direction)
			else: note = Note(data, data.beatmapIndex, direction)

			data.totalScore += note.maxScore
			data.currentNotes.append(note)
			data.beatmapIndex += 1

	for note in data.currentNotes:
		note.move()
		note.checkForLimit(data)

################################################################################
#Screen Draw Helpers
################################################################################

def drawSelectButtons(canvas, data):
	canvas.create_window(data.width*2/5, data.height * 9/10,
			window = data.leftButton, height = 25, width = 25)
	canvas.create_window(data.width*3/5, data.height * 9/10,
			window = data.rightButton, height = 25, width = 25)
	canvas.create_window(data.width*4/5, data.height * 9/10,
			window = data.playButton, height = 50, width = 100)
	canvas.create_window(data.width//5, data.height * 9/10,
			window = data.backButton, height = 50, width = 100)
	canvas.create_window(data.width-20, 20,
			window = data.helpButton, height = 20, width = 20)

def drawEndButtons(canvas, data):
	canvas.create_window(data.width//5, data.height*9/10,
			window = data.backButton, width = 100, height = 50)
	canvas.create_window(data.width*4/5, data.height *9/10,
			window = data.replayButton, width = 100, height = 50)
	canvas.create_window(data.width-20, 20,
			window = data.helpButton, height = 20, width = 20)

def drawHighScore(canvas, data):
	currSongDisplay = data.songDisplays[data.currentPage-1][data.displayIndex]
	songInfo = currSongDisplay.songName + "|" + currSongDisplay.difficulty
	canvas.create_rectangle(data.width//2+10, data.height//3, data.width - 10,
			data.height*2/3, fill = "light blue")
	canvas.create_text(data.width*3/4, data.height*2/5,
			text = "High Score", font = "System 25 bold")
	if songInfo in data.highscores:
		canvas.create_text(data.width*3/4, data.height//2, 
			text = str(data.highscores[songInfo]) + "%", font = "System 25")
	else:
		canvas.create_text(data.width*3/4, data.height//2, text = "None",
			font = "System 25")

def drawScore(canvas, data, score, percentage, grade):
	canvas.create_text(data.width*3/5, data.height * 3/10, 
			text = "Score: " + str(score), font = "System 25")
	canvas.create_text(data.width*3/5, data.height * 2/5,
	text = "Total Score Possible: " + str(data.totalScore), font = "System 25")
	canvas.create_text(data.width*3/5, data.height * 3/5,
			text = "Percentage: " + str(percentage), font = "System 25") 
	canvas.create_text(data.width*3/5, data.height * 4/5,
						text = "Grade: " + grade, font = "System 25 bold")
	canvas.create_text(data.width/5, data.height * 3/10,
			text = "300s: " + str(data.scoreCounts[3]), font = "System 25")
	canvas.create_text(data.width/5, data.height * 2/5,
			text = "200s: " + str(data.scoreCounts[2]), font = "System 25")
	canvas.create_text(data.width/5, data.height * 3/5,
			text = "100s: " + str(data.scoreCounts[1]), font = "System 25")
	canvas.create_text(data.width/5, data.height * 4/5,
			text = "Missed: " + str(data.scoreCounts[0]), font = "System 25")

def calculateGrade(failed, percentage, data):
		if failed:
			return "F"
		elif data.scoreCounts[3] == len(data.beatmap):
			return "SSS"
		elif data.scoreCounts[0] == 0:
			return "SS"
		elif percentage >= 98:
			return "S"
		elif percentage >= 90:
			return "A"
		elif percentage >= 80:
			return "B"
		elif percentage >= 70:
			return "C"
		else:
			return "D"

def getSelectHelp():
	return """Help:
	*At any point, pressing F11 will toggle fullscreen*

	Song Select: Choose a song to play with your mouse, or arrow keys.
	Use the left and right arrow keys or the arrow buttons to turn pages.
	Songs have three difficulties: easy, medium, and hard.
	High scores are both song and difficulty specific.
	Press 'Enter' or click Play Song to start the selected song.
	The back button returns you to the title screen."""

def getGameHelp():
	return """Help:
	Gameplay: In game, notes (cubes) will start to appear, growing in
	visibility the closer they are. When the note's color is fully visible,
	the note is about to disappear.
	There are three types of notes: blue notes are normal. Depending on when
	they are hit, they either give 100, 200, 300, or no points.
	Green notes are beneficial: they are worth double points.
	Both green and blue notes give health when hit correctly and take health
	when missed.
	Red notes are harmful: hitting these will make you lose health and 
	gain no points. Letting them pass will give 300 points and health.
	In the top left corner is your health bar. This changes based on your
	performance. If the health reaches zero, the song is failed and you
	will go to the end screen.
	At the top of the screen is your score. Score increases based on your
	performance.
	At the top right corner is your percentage, calculated by your current
	score divided by the total score you could have earned. The percentage
	determines what grade you get at the end of the song.
	Failing a song with automatically earn an F.
	Your highest percentage for each song is saved and displayed during
	the song select screen."""

def getEndHelp():
	return """Help:
	*At any point, pressing F11 will toggle fullscreen*

	End Screen:
	This screen displays your stats.
	The values on the left tell for each point category how many notes you hit.
	The values on the right tell what score you had compared to the total
	number of points you could have scored, and your percentage.
	Your grade for the song is displayed at the bottom.
	The back button returns you to the song select screen, as well as pressing
	'Backspace' or 'Enter', and the replay button replays the current song,
	as well as pressing 'r'."""

################################################################################
#Screen Draws
################################################################################

def drawTitle(canvas, data):
	canvas.create_window(data.width//2, data.height//2,
			window = data.titleButton, height = 200, width = 200)

	if data.titleMenu:
		startButtonWindow = canvas.create_window(data.width*3/4, data.height//2,
			window = data.startButton, height = 50, width = 100)
		quitButtonWindow = canvas.create_window(data.width//4, data.height//2,
			window = data.quitButton, height = 50, width = 100)

def drawSelect(canvas, data):
	for display in data.songDisplays[data.currentPage-1]:
		display.draw(canvas, data)

	canvas.create_text(data.width//2, data.height * 9/10,
			text = "Page %d/%d" %(data.currentPage, data.totalPages))

	drawSelectButtons(canvas, data)
	drawHighScore(canvas, data)

	if data.help:
		data.helpText = getSelectHelp() + "\n" + getGameHelp()
		canvas.create_rectangle(data.width//5, data.height//5,data.width*4/5,
			data.height*4/5, fill = "light blue")
		canvas.create_text(data.width//2, data.height//2, text = data.helpText,
			width = data.width*3/5)

def drawGame(canvas, data):
	for note in data.currentNotes:
		note.draw(canvas, data.noteIndex)

	percent = round((data.score/data.totalScore) * 100, 2)

	canvas.create_text(data.width//2, 50,
			text = "Score: " + str(data.score), font = "System 25")
	canvas.create_text(data.width-50, 50, text = str(percent) + "%",
			font = "System 25")
	canvas.create_rectangle(15, 5, 15 + data.health*2, 15, fill = "red")
	canvas.create_image(115, 10, image = data.healthImage)

def drawEnd(canvas, data):
	if data.health <= 0: completionText = "Failed..."
	else: completionText = "Complete!"
	songNameInfo = data.songName.split("|")
	songText = songNameInfo[0] + '\t' + songNameInfo[1].upper()

	grade = calculateGrade(data.health <= 0, data.percentage, data)

	canvas.create_text(data.width//2, data.height//10,
			text = songText + "\n" + completionText,
			font = "System 30 bold", width = data.width)

	drawEndButtons(canvas, data)
	drawScore(canvas, data, data.score, data.percentage, grade)

	if data.help:
		data.helpText = getEndHelp()
		canvas.create_rectangle(data.width//5, data.height//5,data.width*4/5,
			data.height*4/5, fill = "light blue")
		canvas.create_text(data.width//2, data.height//2, text = data.helpText,
			width = data.width*3/5)

################################################################################
#Animation Framework
################################################################################

def init(data):
	data.help = False

	data.highscores = getHighscores()

	initTitle(data)

def mousePressed(event, data):
	if data.screen == "select": pressedSelect(event, data)
	elif data.screen == "game": pressedGame(event, data)

def mouseReleased(event, data):
	if data.screen == "game": releasedGame(event, data)

def keyPressed(event, data):
	if data.screen == "select": keySelect(event, data)
	elif data.screen == "end": keyEnd(event, data)

def timerFired(data):
	if data.screen == "game": timerGame(data)

def redrawAll(canvas, data):
	if data.screen == "title": drawTitle(canvas, data)
	elif data.screen == "select": drawSelect(canvas, data)
	elif data.screen == "game": drawGame(canvas, data)
	elif data.screen == "end": drawEnd(canvas, data)

def run(width=300, height=300):
	def redrawAllWrapper(canvas, data):
		canvas.delete(ALL)
		canvas.create_image(data.width//2, data.height//2,
			image = data.curBackground)
		redrawAll(canvas, data)
		canvas.update()

	def mousePressedWrapper(event, canvas, data):
		mousePressed(event, data)
		redrawAllWrapper(canvas, data)

	def mouseReleasedWrapper(event, canvas, data):
		mouseReleased(event, data)
		redrawAllWrapper(canvas, data)

	def keyPressedWrapper(event, canvas, data):
		keyPressed(event, data)
		redrawAllWrapper(canvas, data)

	def timerFiredWrapper(canvas, data):
		timerFired(data)
		redrawAllWrapper(canvas, data)
		# pause, then call timerFired again
		canvas.after(data.timerDelay, timerFiredWrapper, canvas, data)

	def toggleFullScreen(root, width, height, data):
		#https://stackoverflow.com/questions/7966119/display-fullscreen-mode-on-tkinter
		data.fullScreen = not data.fullScreen
		if data.fullScreen:
			root.attributes("-fullscreen", True)
			data.width = root.winfo_screenwidth()
			data.height = root.winfo_screenheight()
		else:
			root.attributes("-fullscreen", False)
			data.width = width
			data.height = height

	# Set up data and call init
	class Struct(object): pass
	data = Struct()
	data.width = width
	data.height = height
	data.fullScreen = False
	data.timerDelay = 50 # milliseconds

	# create the root and the canvas
	root = Tk()

	canvas = Canvas(root, width=data.width, height=data.height)
	canvas.configure(bd=0, highlightthickness=0, cursor = "target")
	canvas.pack(fill = BOTH, expand = 1)

	init(data)
	initButtons(canvas, data)

	# set up events
	root.bind("<Button-1>", lambda event:
							mousePressedWrapper(event, canvas, data))
	root.bind("<Key>", lambda event:
							keyPressedWrapper(event, canvas, data))
	root.bind("<ButtonRelease-1>", lambda event:
							mouseReleasedWrapper(event, canvas, data))
	root.bind("<F11>", lambda event: toggleFullScreen(root, width, height, data))

	timerFiredWrapper(canvas, data)
	# and launch the app

	root.mainloop()  # blocks until window is closed
	print("bye!")

if __name__ == "__main__":
	saveSongs()
	run(800, 800)