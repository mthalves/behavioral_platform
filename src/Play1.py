# Interface Imports
import tkinter
from tkinter import *
from tkinter import font
from tkinter import LEFT, RIGHT, BOTTOM, TOP, NONE
from tkinter import messagebox, filedialog, StringVar
from tkinter.font import Font

# Utils Imports
from copy import deepcopy
import datetime
import numpy as np
import os
import random
import time

from pygame import mixer
import winsound

from MyCommons import *
import utils

AUTO = False

class Play1:

	def __init__(self, master, prev_sc, main_bg):
		# 1. Initializing the necessary variables
		# a. screen and log components
		self.update_screen(master,main_bg)
		self.update_variables(prev_sc)

		# c. log text
		self.start_log = 		"---------------------------------\n" + \
								"| LOG STAGE 1 PLAY SCREEN       |\n" + \
								"---------------------------------"
		self.left_txt = 		"| Left Button Pressed           |"
		self.right_txt = 		"| Right Button Pressed          |"
		self.timeout_txt = 		"| Time Out                      |"
		self.finish_txt = 		"| Stage Finished                |"
		print(self.start_log)

		# 2. Setting the Buttons and Point Counter
		# a. buttons
		self.createButtons()

		# b. points counter
		self.points_label = tkinter.Label(master, bg='white', textvariable=self.points,width=3,\
									 fg = 'black', font=Font(family='Helvetica', size=30, weight='bold'),\
									 padx=20,pady=20,bd=2,highlightbackground='black',highlightthickness=2)
		self.points_label.place(x=self.sw/2,y=self.sh/2,anchor='center')

		# c. loading sound and reset mouse position
		#mixer.init()
		#mixer.music.load('local/default/sfx.wav')
		self.reset_mouse_position()

		self.ableButtonsAndMouse()

	def update_screen(self,master,main_bg):
		self.master = master
		self.main_bg = main_bg
		self.main_bg.destroy()
		self.main_bg = tkinter.Label(master, bg= "#%02x%02x%02x" % (255,255,255))
		self.main_bg.place(x=0,y=0,relwidth=1,relheight=1)
		self.sw, self.sh = self.master.winfo_screenwidth(), self.master.winfo_screenheight()

	def update_variables(self,prev_sc):
		self.prev_sc = prev_sc

		# a. experiment variables
		self.experiment = prev_sc.experiment
		self.settings = prev_sc.settings
		self.nickname = prev_sc.nickname
		self.start_time = prev_sc.start_time
		self.round_start_time = datetime.datetime.now()
		self.block_start_time = datetime.datetime.now()

		# b. round variables
		self.clicks = ''
		self.points = tkinter.StringVar()
		self.points.set(0)
		self.repeat = 0
		self.reinforcement = []

		# c. game variables
		self.combinations = ['EEEE','EEED','EEDE','EDEE',\
		'DEEE','EEDD','EDDE','DDEE','DEED','DEDE','EDED','DDDE',\
		'DDED','DEDD','EDDD','DDDD']
		self.frequency = {'EEEE':1,'EEED':1,'EEDE':1,'EDEE':1,\
		'DEEE':1,'EEDD':1,'EDDE':1,'DDEE':1,'DEED':1,'DEDE':1,'EDED':1,'DDDE':1,\
		'DDED':1,'DEDD':1,'EDDD':1,'DDDD':1}
		self.total_frequency = prev_sc.total_frequency
		self.memo_accuracy = prev_sc.memo_accuracy
		self.memo_reinforced = prev_sc.memo_reinforced
		self.saved_order = prev_sc.saved_order
		self.stages = prev_sc.stages

		# d. result variables
		self.results = []
		self.result_set = set()
		self.blocks = prev_sc.blocks

	# THE GAME METHODS
	def reset_mouse_position(self):
		self.master.event_generate('<Motion>', warp=True, x=self.sw/2, y=self.sh/2)

	def auto_play(self):
		coin = random.uniform(0.5,1.0)
		if coin < 0.5:
			self.left_button_click()
		else:
			self.right_button_click()

	def check_game_status(self):
		self.disableButtonsAndMouse()
		if datetime.datetime.now() - self.start_time >\
			datetime.timedelta(minutes=float(self.settings['max_time']))\
			and len(self.blocks) >= int(self.settings['blocks1']):
			self.timeOut()
		elif len(self.clicks) == 4:	
			print('| Clicks:',self.clicks)
			self.repeat += 1
			self.reinforcement.append(True)
			self.removeButtons()
			self.rgb = np.array([255.0,255.0,255.0])

			self.points.set(int(self.points.get())+int(self.settings['points']))
			#mixer.music.play() 
			winsound.PlaySound('local/default/sfx.wav', winsound.SND_ASYNC)
			self.master.after(20,self.fadeColor)
		else:
			self.master.after(int(float(self.settings['iri'])*1000),self.ableButtonsAndMouse)

	def fadeColor(self):
		self.rgb -= np.array([255*0.01,55*0.01,255*0.01])
		self.main_bg.configure(bg="#%02x%02x%02x" % (int(self.rgb[0]),\
			int(self.rgb[1]),int(self.rgb[2])))
		if self.rgb[1] > 200:
			self.master.after(10,self.fadeColor)
		else:
			self.main_bg.configure(bg="#%02x%02x%02x" % (0,200,0))
			self.rgb = np.array([0.0,200.0,0.0])
			self.master.after(int(float(self.settings['iti'])*1000),self.replay)

	def replay(self):
		# 1. Updating the variables
		self.results.append(self.clicks)
		self.result_set.add(self.clicks)

		# 2. Writing results
		if self.repeat == 16:
			self.blocks.append([deepcopy(self.results),\
			(datetime.datetime.now() - self.block_start_time).total_seconds() ,1])
			utils.write_result('1',self,False)

			self.results = []
			self.result_set = set()
			self.repeat = 0
			self.block_start_time = datetime.datetime.now()
		else:
			utils.write_result('1',self,True)

		self.frequency[self.clicks] += 1 #frequency calculated later
		self.total_frequency[self.clicks] += 1

		# 3. Checking replay conditions
		if len(self.blocks) >= int(self.settings['blocks1'])\
		and utils.Stability(self.blocks,float(self.settings['stability'])):
			self.rgb = np.array([0.0,200.0,0.0])
			self.win_txt = tkinter.Label(self.master, bg= "#%02x%02x%02x" % (0, 200, 0), fg = "#%02x%02x%02x" % (0, 200, 0),\
				 text='ATÉ O MOMENTO VOCÊ ACUMULOU '+str(int(self.points.get())+int(self.prev_sc.points.get()))+\
				 ' PONTOS!', font=Font(family='Helvetica', size=16, weight='bold'))
			self.master.after(20,self.fadeResetText)
		else:
			self.clicks = ''
			self.round_start_time = datetime.datetime.now()
			self.main_bg.configure(bg="#%02x%02x%02x" % (255,255,255))
			self.createButtons()
			self.ableButtonsAndMouse()

	def fadeResetText(self):
		self.rgb -= np.array([0*0.02,200*0.02,0*0.02])
		self.win_txt.place(x=self.sw/2,y=self.sh/2-150,anchor='center')
		self.win_txt.configure(fg="#%02x%02x%02x" % (int(self.rgb[0]),\
			int(self.rgb[1]),int(self.rgb[2])))

		if self.rgb[1] > 0:
			self.master.after(20,self.fadeResetText)
		else:
			self.points.set(int(self.points.get())+int(self.prev_sc.points.get()))
			self.master.after(1500,self.reset)

	def reset(self):
		self.master.configure(cursor='')
		self.reset_mouse_position()
		if utils.U(self.total_frequency) < float(self.settings['u_threshold']):
			self.master.after(1500,self.next_stage)
		else:
			self.fail()
	
	# BUTTONS AND SCREEN METHODS
	def next_stage(self):
		print(self.finish_txt)
		# 1. Reseting global counters
		self.repeat = 0
		self.blocks = []
		self.total_frequency = {'EEEE':1,'EEED':1,'EEDE':1,'EDEE':1,\
		'DEEE':1,'EEDD':1,'EDDE':1,'DDEE':1,'DEED':1,'DEDE':1,'EDED':1,'DDDE':1,\
		'DDED':1,'DEDD':1,'EDDD':1,'DDDD':1}
		self.memo_accuracy = 0

		# 2. Starting next stage
		from IntroStage2 import IntroStage2
		IntroStage2(self.master,self,self.main_bg)

	def timeOut(self):
		print(self.timeout_txt)
		self.disableButtons()
		myReturnMenuPopUp(self,'Fim do Experimento!\nPor favor, contacte o pesquisador e informe o fim da tarefa.\n Obrigado pela sua participação!')

	def fail(self):
		myFailPopUp(self,'Fim do Experimento!\nPor favor, contacte o pesquisador e informe o fim da tarefa.\n Obrigado pela sua participação!')

	def goMenu(self):
		self.destroyWidgets()
		from Menu import Menu
		Menu(self.master,self,self.main_bg)

	def createButtons(self):
		# 1. Loading the images
		left_image = tkinter.PhotoImage(file='local/default/blank.png')
		right_image = tkinter.PhotoImage(file='local/default/blank.png')

		# 2. Building the buttons
		# a. left button
		self.left_button = Button(self.master, anchor = 'center', compound = 'center', 
									font = Font(family='Helvetica', size=18, weight='bold'),
									bg = "#%02x%02x%02x" % (30, 30, 30), fg = 'white',
									command = self.left_button_click,
									highlightthickness = 0, image=left_image,
									bd = 0, padx=0,pady=0,height=80,width=80)
		self.left_button.image = left_image
		self.left_button.place(x=2*self.sw/10, y=self.sh/2, anchor='center')

		# b. right button
		self.right_button = Button(self.master, anchor = 'center', compound = 'center', 
									font = Font(family='Helvetica', size=18, weight='bold'),
									bg = "#%02x%02x%02x" % (30, 30, 30), fg = 'white',
									command = self.right_button_click,
									highlightthickness = 0, image=right_image,
									bd = 0, padx=0,pady=0,height=80,width=80)
		self.right_button.image = right_image
		self.right_button.place(x=8*self.sw/10, y=self.sh/2, anchor='center')

	def left_button_click(self):
		#print(self.left_txt)
		self.reset_mouse_position()
		self.clicks += 'E'

		self.check_game_status()
			
	def right_button_click(self):
		#print(self.right_txt)
		self.reset_mouse_position()
		self.clicks += 'D'

		self.check_game_status()

	def ableButtons(self):
		self.left_button.configure(state="normal")
		self.right_button.configure(state="normal")

	def disableButtons(self):
		self.left_button.configure(state="disabled")
		self.right_button.configure(state="disabled")

	def ableButtonsAndMouse(self):
		self.left_button.configure(state="normal")
		self.right_button.configure(state="normal")
		self.master.configure(cursor='')
		self.reset_mouse_position()
		if AUTO:
			self.auto_play()

	def disableButtonsAndMouse(self):
		self.left_button.configure(state="disabled")
		self.right_button.configure(state="disabled")
		self.master.configure(cursor='none')

	def removeButtons(self):
		self.left_button.destroy()
		self.right_button.destroy()

	def destroyWidgets(self):
		self.left_button.destroy()
		self.right_button.destroy()
		self.points_label.destroy()
