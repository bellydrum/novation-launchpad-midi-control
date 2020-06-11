## name=Novation Launchpad DEFAULT
# url=

import patterns
import mixer
import device
import transport
import arrangement
import general
import launchMapPages
import playlist

import midi
import utils

MaxInt = 2147483647
PadsW = 9
PadsH = 8
OverH = 8
OverW = 8
PadsStride = 16

LPBC = 0
LPBCD = 12
LPBCT = [LPBCD, LPBC]

class TLaunchPad():
	def __init__(self):

		self.ClipOfs = 0
		self.TrackOfs = 0
		self.BlockOfs = False # make arrows work in pages

		self.BtnT = [0x00, 0x00, 0x00, 0x00]
		self.ArrowT = [0x00, 0x00, 0x00, 0x00]
		self.BlinkOnBars = 0
		self.BtnLastClip = [[0 for x in range(PadsW)] for y in range(PadsH)]

		self.BtnMap = [[0 for x in range(PadsW)] for y in range(PadsH + 1)]
		self.AnimBtnMap = [[0 for x in range(PadsW)] for y in range(PadsH + 1)]
		self.OldBtnMap = [[0 for x in range(PadsW)] for y in range(PadsH + 1)]

		self.DoubleBuffering = 0
		self.NoFullRefresh = False

		self.BlinkState = 2

		self.BtnMapMode = 0 #animation
		self.BtnMapModeRefCount = 0

		self.VelToCol =  list(map(lambda n: ( (n >> 3) & 3) + (((n >> 3) >> 2) << 4), range(0, 128)))

	def ResetBtnLastClip(self):

		for y in range(0, PadsW):
			for x in range(0, PadsH):
				self.BtnLastClip[x][y] = utils.TClipLauncherLastClip(MaxInt, MaxInt, MaxInt)

	def ResetBtnMap(self, BtnMapObj, val):

		for y in range(0, PadsH + 1):
			for x in range(0, PadsW):
				BtnMapObj[y][x] = val

	def UpdateBlinking(self):  #check if any blinking button

		for y in range(0, PadsH + 1):
			for x in range(0, PadsW):
				if self.BtnMap[y][x] > 1:
					device.fullRefresh()
					break

	def Reset(self):

		if device.isAssigned():
			device.midiOutMsg(0xB0)

		self.ResetBtnMap(self.BtnMap, 0)
		self.ResetBtnMap(self.AnimBtnMap, 0)
		self.AnimBtnMap[PadsH][8] = 0x13
		self.ResetBtnMap(self.OldBtnMap, 0xFF)
		self.ResetBtnLastClip()

	def OnMidiMsg(self, event):

		print('heyyy')
		self.FullRefresh_Anim()

		if event.midiId == midi.MIDI_CONTROLCHANGE:
			# track offset
			if (event.data1 == 0x68) | (event.data1 == 0x69):
				event.handled = True
				BlockPages = (self.BtnT[0] > 0) | self.BlockOfs
				m = 150 + int(BlockPages) * 350; # faster in 1-pad increments
				device.repeatMidiEvent(event, m, m)
				if (event.data2 > 0) & (event.pmeFlags & midi.PME_System != 0):
					m = (event.data1 - 0x68) * 2 - 1
					if BlockPages:
						m = m * OverH
					self.SetOfs(self.TrackOfs + m, self.ClipOfs)
					self.BtnT[0] = int(self.BtnT[0] > 0) * 2; # so that session btn works as held

				self.ArrowT[event.data1 - 0x68] = event.data2
				CheckSpecialSwitches()
				playlist.lockDisplayZone(1 + event.data1 - 0x68, event.data2 > 0)

			# clip offset
			elif (event.data1 == 0x6A) | (event.data1 == 0x6B):
				event.handled = True
				BlockPages = (self.BtnT[0] > 0) | self.BlockOfs
				m = 150 + int(BlockPages) * 350 # faster in 1-pad increments
				device.repeatMidiEvent(event, m, m);
				if (event.data2 > 0) & (event.pmeFlags & midi.PME_System != 0):
					m = (event.data1 - 0x6A) * 2 - 1
					if self.ClipOfs >= 0:
						if (self.ClipOfs == 0) & (m == -1):
							o = -1
						else:
							if BlockPages:
								m = m * OverW
							o = max(self.ClipOfs + m, 0)
					else:
						o = self.ClipOfs + m
					self.SetOfs(self.TrackOfs, o)
					self.BtnT[0] = int(self.BtnT[0] > 0) * 2 # so that session btn works as held
					if self.ClipOfs <= 0:
						device.stopRepeatMidiEvent()

				self.ArrowT[event.data1 - 0x68] = event.data2
				CheckSpecialSwitches()
				playlist.lockDisplayZone(1 + event.data1 - 0x68, event.data2 > 0)
			# held buttons
			elif (event.data1 == 0x6D) | (event.data1 == 0x6E) | (event.data1 == 0x6F):
				event.handled = True
				if (event.pmeFlags & midi.PME_System != 0):
					o = event.data1 - 0x6C
					m2 = self.BtnT[o]
					if (m2 >= 2) & (event.data2 > 0):
						m = 0
						m2 = 0
					else:
						m = int(event.data2 > 0)
						if (m > 0) & device.isDoubleClick(event.data1) & ((self.ClipOfs >= -1) | (o != 2)):
							m += 1
					if (m > 0) | (m2 <= 1):
						SetBtn(o, m)
					if (o == 2) & (self.ClipOfs < -1) & (event.data2 > 0):
						launchMapPages.releaseMapItem(event, -self.ClipOfs - 2)
			# overview
			elif (event.data1 == 0x6C):
					event.handled = True
					if (event.pmeFlags & midi.PME_System != 0):
						if event.data2 > 0:
							SetBtn(0, int(self.BtnT[0] > 0) ^ 1)
						elif self.BtnT[0] == 2:
							SetBtn(0, 0)

		# NOTE
		if (event.midiId == midi.MIDI_NOTEON) | (event.midiId == midi.MIDI_NOTEOFF):
			if event.midiChan == 0:
				# live mode
				y = event.data1 // PadsStride
				x = event.data1 - y * PadsStride
				if (x >= PadsW) | (y >= PadsH):
					return

				# clip release safety
				if event.data2 == 0:
					if self.BtnLastClip[y][x].TrackNum != MaxInt:
						if (event.pmeFlags & midi.PME_System_Safe != 0):
							playlist.triggerLiveClip(self.BtnLastClip[y][x].TrackNum, self.BtnLastClip[y][x].SubNum, self.BtnLastClip[y][x].Flags | midi.TLC_Release)
						self.BtnLastClip[y][x].TrackNum = MaxInt;
						event.handled = True
						return

				if self.BtnT[0] > 0:
					# overview pick
					if event.data2 > 0:
						if x >= PadsW - 1:
							self.SetOfs(self.TrackOfs, -y - 1)
						else:
							self.SetOfs(y * OverH, x * OverW)
					else:
						SetBtn(0, 0)
					event.handled = True
				else:
					if self.ClipOfs < -1:
						# custom pages
						x2 = y * PadsW + x
						m = -self.ClipOfs - 2;
						if x2 <= launchMapPages.getMapCount(m):
							o = launchMapPages.getMapItemChannel(m, x2)
							if o > -128:
								m2 = event.data2
								if (m2 == 0) & (self.BtnT[1] > 0):
									m2 = -MaxInt # user1=hold
								print("processMapItem")
								launchMapPages.processMapItem(event, m, x2, m2)
					else:
						if self.ClipOfs >= 0:
							# first chance
							launchMapPages.processMapItem(event, -1, y * PadsW + x, event.data2)
							if event.handled:
								return

						if (event.pmeFlags & midi.PME_System_Safe != 0):
							x2 = x;
							y2 = y + self.TrackOfs + 1
							if self.ClipOfs >= 0:
								if event.data2 > 0:
									# clip launch
									if x2 >= PadsW - 1:
										x2 = -1
									else:
										x2 += self.ClipOfs
									m = midi.TLC_MuteOthers | midi.TLC_Fill
									if self.BtnT[3] > 0:
										m = m | midi.TLC_GlobalSnap # snap
									if self.BtnT[1] | (self.BtnT[2] > 0):
										m = m | midi.TLC_ColumnMode; # column mode
										if self.BtnT[1] == 0:
											m = m | midi.TLC_WeakColumnMode # weak
										elif self.BtnT[2] > 0:
											m = m | midi.TLC_TriggerCheckColumnMode # trigger-check

									playlist.triggerLiveClip(y2, x2, m)
									self.BtnLastClip[y][x].TrackNum = y2
									self.BtnLastClip[y][x].SubNum = x2
									self.BtnLastClip[y][x].Flags = m
							elif event.data2 > 0:
								# track properties
								# --> with CurPLArrangement.PLTrackInfoT[y2] do
								if (x2 == 2) | (x2 == 3):
									playlist.incLivePosSnap(y2, (x2 - 2) * 2 - 1)
								elif (x2 == 4) | (x2 == 5):
									playlist.incLiveTrigSnap(y2, (x2 - 4) * 2 - 1)
								elif (x2 == 6) | (x2 == 7):
									playlist.incLiveLoopMode(y2, (x2 - 6) * 2 - 1);
								elif x2 == 8        :
									playlist.incLiveTrigMode(y2, 1);

								playlist.refreshLiveClips()
							event.handled = True
		else:
			event.handled = False

	def DoubleBuffer(self):

		if device.isAssigned():
			device.midiOutMsg(0xB0 + ((self.DoubleBuffering + ((self.DoubleBuffering ^ 1) << 2) + (1 << 4) + (1 << 5)) << 16))
			self.DoubleBuffering = self.DoubleBuffering ^ 1

	def SetBrightness(self, Level):

		Den = 13 << 16
		if device.isAssigned():
			# duty cycle (for contrast)
			m = min(Round(Level * 18), 15)
			if m < 8:
				device.midiOutMsg(0x1EB0 + Den + (m << 20))
			else:
				device.midiOutMsg(0x1FB0 + Den + ((m - 8) << 20));

	# Numerator=1..16, Denominator=3..18
	def SetBrightness(self, Numerator, Denominator):
		if device.isAssigned():
			# duty cycle (for contrast)
			if Numerator < 9:
				device.midiOutMsg(0x1EB0 + ((Numerator - 1) << 20) + ((Denominator - 3) << 16))
			else:
				device.midiOutMsg(0x1FB0 + ((Numerator - 9) << 20) + ((Denominator - 3) << 16));

	def OnMidiOutMsg(self, event):

		event.handled = True
		ID = event.midiId
		n = 0
		if (ID == midi.MIDI_NOTEOFF) | (ID == midi.MIDI_NOTEON):
			NoteNum = event.note
			if ID == midi.MIDI_NOTEOFF:
				Velocity = 0
			else:
				Velocity = event.velocity

			if NoteNum >= 126:
				# change self.BtnMapMode
				if NoteNum == 126:
					if ID == midi.MIDI_NOTEON:
						self.BtnMapModeRefCount += 1
						if self.BtnMapModeRefCount == 1:
							device.fullRefresh()
					else:
						self.BtnMapModeRefCount -= 1
						if self.BtnMapModeRefCount == 0:
							device.fullRefresh()
				elif ID == midi.MIDI_NOTEON:
					self.BtnMapMode = Velocity >> 5
					device.fullRefresh()
			else:
				# change pad
				o, n = utils.DivModU(NoteNum, 12)
				if o < PadsH:
					o = PadsH - 1 - o

				if utils.InterNoSwap(o, 0, PadsH) & utils.InterNoSwap(n, 0, PadsW - 1) & ((o < PadsH) | (n < PadsW - 1)): #light shouldn't be touched'
					self.AnimBtnMap[o][n] = self.VelToCol[Velocity]
					self.FullRefresh_Anim()
		else:
			event.handled = False

	def OnDoFullRefresh(self):

		TempBtnMap = [[0 for x in range(PadsW)] for y in range(PadsH + 1)]

		if device.isAssigned():
			#local copy
			#EnterCriticalSection(BtnMapLock);
			if (self.BtnMapMode < 2) & (self.BtnMapModeRefCount == 0):
				for y in range(0, PadsH + 1):
					for x in range(0, PadsW):
						TempBtnMap[y][x] = self.BtnMap[y][x]

				if self.BtnMapMode == 1:
					for y in range(0, PadsH + 1):
						for x in range(0, PadsW):
							if self.AnimBtnMap[y][x] != 0:
								TempBtnMap[y][x] = self.AnimBtnMap[y][x]
			else:
				for y in range(0, PadsH + 1):
					for x in range(0, PadsW):
						TempBtnMap[y][x] = self.AnimBtnMap[y][x]
			#LeaveCriticalSection(BtnMapLock);

			# count differences & update blinking
			o = 0;

			for y in range(0, PadsH + 1):
				for x in range(0, PadsW):
					if TempBtnMap[y][x] != self.OldBtnMap[y][x]:
						o += 1

			if o == 0:
				return

			# light
			if TempBtnMap[PadsH][8] != self.OldBtnMap[PadsH][8]:
				device.midiOutMsg(midi.MIDI_CONTROLCHANGE + (0x1E << 8) + (TempBtnMap[PadsH][8] << 16));

			# double buffer if necessary
			b3 = o > 4
			p = LPBCT[b3]

			# update
			if o < (((PadsH + 1) * PadsW) >> 1): #todo len
				# normal version
				# pads & scene btns
				m = midi.MIDI_NOTEON
				for y in range(0, PadsH):
					for x in range(0, PadsW):
						b = TempBtnMap[y][x]
						if b != self.OldBtnMap[y][x]:
							device.midiOutMsg(m + (x << 8) + ((b + p) << 16))
					m += (PadsStride << 8)
				# system btns
				m = midi.MIDI_CONTROLCHANGE + (0x68 << 8)
				for x in range(0, 8):
					b = TempBtnMap[PadsH][x]
					if b != self.OldBtnMap[PadsH][x]:
						device.midiOutMsg(m + (x << 8) + ((b + p) << 16))
			else:
				# full fast version
				m = midi.MIDI_NOTEON + 2
				# pads
				for y in range(0, PadsH):
					for x in range(0, 4):
						device.midiOutMsg(m + ((TempBtnMap[y][x << 1] + p) << 8) + ((TempBtnMap[y][(x << 1) + 1] + p) << 16))
				# scene btns
				for x in range(0, 4):
					device.midiOutMsg(m + ((TempBtnMap[x << 1][8] + p) << 8) + ((TempBtnMap[(x << 1) + 1][8] + p) << 16))
				# system btns
				for x in range(0, 4):
					device.midiOutMsg(m + ((TempBtnMap[PadsH][x << 1] + p) << 8) + ((TempBtnMap[PadsH][(x << 1) + 1] + p) << 16))

			#DebugValue:=TimeGetTime-DebugValue;

			if b3:
				self.DoubleBuffer()

			# backup
			for y in range(0, PadsH + 1):
				for x in range(0, PadsW):
					self.OldBtnMap[y][x] = TempBtnMap[y][x]

	def FullRefresh_Btn(self):

		if (self.BtnMapMode < 2) & (self.BtnMapModeRefCount == 0):
			device.fullRefresh()

	def FullRefresh_Anim(self):

		if (self.BtnMapMode > 0) | (self.BtnMapModeRefCount != 0):
			device.fullRefresh()

	def SetOfs(slef, SetTrackOfs, SetClipOfs):

		OfsT = (LPBC, LPBC + 1, LPBC + (1 << 4), LPBC + 1 + (1 << 4), LPBC + 2, LPBC + (2 << 4), LPBC + 2 + (2 << 4), LPBC + 3, LPBC + (3 << 4), LPBC + 3 + (3 << 4))     # red/green/orange

		self.TrackOfs = utils.Limited(SetTrackOfs, 0, playlist.trackCount() - PadsH)
		self.ClipOfs = utils.Limited(SetClipOfs, -launchMapPages.length() - 1, 0x10000)
		if device.isAssigned():
			#EnterCriticalSection(BtnMapLock);

			# page buttons
			o = (self.TrackOfs + 7) >> 3
			v = OfsT[utils.Limited(o, 0, len(OfsT) -1)]
			v2 = 0
			self.BtnMap[PadsH][1] = v
			if self.ClipOfs >= 0:
				o = abs(self.ClipOfs + 7) >> 3
			else:
				o = -self.ClipOfs
			v = OfsT[utils.Limited(o, 0, len(OfsT) -1)]
			v2 = 0
			if self.ClipOfs >= 0:
				v, v2 = utils.SwapInt(v, v2)
			self.BtnMap[PadsH][2] = v
			self.BtnMap[PadsH][3] = v2
			#LeaveCriticalSection(BtnMapLock);

			if self.ClipOfs < -1:
				launchMapPages.updateMap(-self.ClipOfs - 2)
			else:
				launchMapPages.checkMapForHiddenItem()
			self.OnUpdateLiveMode(playlist.trackCount())

		if playlist.getDisplayZone() != 0:
			OnDisplayZone()

	def OnDisplayZone():
		if (self.ClipOfs >= 0) & (playlist.getDisplayZone() != 0):
			playlist.liveDisplayZone(self.ClipOfs, self.TrackOfs + 1, self.ClipOfs + PadsW - 1, self.TrackOfs + 1 + PadsH)
		else:
			playlist.liveDisplayZone(-1, -1, -1, -1)

	def CheckSpecialSwitches():

		if (self.ArrowT[0] + self.ArrowT[1] + self.ArrowT[2] + self.ArrowT[3]) >= 0x7F * 4:
			self.BlockOfs = not self.BlockOfs
			self.SetOfs(0, 0)
			device.stopRepeatMidiEvent()

	def SetBtn(Num, Value):
		ColT = [[LPBC, LPBC + 3 + (1 << 4)], [LPBC, LPBC + 3 + (3 << 4)], [LPBC, LPBC + 3]]

		self.BtnT[Num] = Value
		if Num > 0:
			v = ColT[Num-1][int(Value > 0)]
			self.BtnMap[PadsH][4 + Num] = v
			self.FullRefresh_Btn()
		else:
			#overview
			self.OnUpdateLiveMode(playlist.trackCount())
			device.stopRepeatMidiEvent() #  in case arrows were held
			playlist.lockDisplayZone(0, Value > 0);


	def OnIdle(self):

		BlinkSpeed = 0x20
		ColT = (LPBC, LPBC + 1,LPBC + 1 + (1 << 4), LPBC + 2 + (1 << 4), LPBC + 2 + (2 << 4), LPBC + 3 + (2 << 4), LPBC + 3 + (3 << 4))

		if (self.ClipOfs == -1) & (self.BtnT[0] == 0) & device.isAssigned():
			#EnterCriticalSection(BtnMapLock);
			for y in range(0, PadsH):
				m = self.TrackOfs + y + 1
				v2 = playlist.getTrackActivityLevelVis(m) * 2
				for x in range(0, 2):
					v = round(v2 * len(ColT))
					v = ColT[utils.Limited(v, 0, len(ColT)-1)]
					v2 = v2 - 1
					self.BtnMap[y][x] = v

			#LeaveCriticalSection(BtnMapLock);

			if self.NoFullRefresh != True:
				self.FullRefresh_Btn()

	def OnUpdateBeatIndicator(Value):

		SyncLEDMsg = [[0, 3 + (1 << 4), 2 + (3 << 4)], [0x02, 0x13, 0x02]]

		if device.isAssigned():
			self.BtnMap[PadsH][4] = SyncLEDMsg[0][Value]
			if self.ClipOfs < self.BlinkOnBars:
				Value = 0
			self.BtnMap[PadsH][8] = SyncLEDMsg[1][Value]
			self.FullRefresh_Btn()

	def OnRefresh(flags):
		if flags & midi.HW_Dirty_RemoteLinks != 0:
			if self.ClipOfs < -1:
				self.SetOfs(self.TrackOfs, self.ClipOfs)
			launchMapPages.updateMap(-1)

	def OnInit(self):
		# init mapping
		launchMapPages.createOverlayMap(3, 1, PadsW, PadsH)

		for y in range(0, PadsH):
			for x in range(0, PadsW):
				launchMapPages.setMapItemTarget(-1, y * PadsW + x, y * PadsStride + x)

		# load mapping
		launchMapPages.init('Novation Launchpad', PadsW, PadsH);
		print("On Init")
		self.Reset()
		self.DoubleBuffer()
		device.createRefreshThread()
		self.OnUpdateLiveMode(playlist.trackCount())

	def OnDeInit(self):
		device.destroyRefreshThread()
		self.Reset()

	def OnUpdateLiveMode(self, LastTrackNum):
		FirstTrackNum = 1
		StatusColT = [LPBC, LPBC, LPBC, LPBC]
		LoopBtnColT = [LPBC + 2 << 4, LPBC + 1 + (1 << 4), LPBC + 3 + (2 << 4), LPBC + 3 + (1 << 4), LPBC + 3, LPBC + 1 + (3 << 4), LPBC + 1 + (2 << 4)]
		LoopColT = [LPBC + 2 << 4, LPBC + 1 + (2 << 4), LPBC + 1 + (2 << 4), LPBC + 1 + (2 << 4), LPBC + 1 + (2 << 4), LPBC + 1 + (2 << 4), LPBC + 1 + (2 << 4)]
		TrigColT = [LPBC + 3 + (3 << 4), LPBC + 3, LPBC + 3, LPBC + 3 + (2 << 4)]
		PlayColT = [LPBC + 3 + (1 << 4), LPBC + 2, LPBC + 2, LPBC + 2 + (1 << 4)]
		SnapColT = [LPBC + 2, LPBC + 1 << 4, LPBC + 2 << 4, LPBC + 3 << 4, LPBC + 1 + (3 << 4), LPBC + 3 + (3 << 4), LPBC + 3 + (2 << 4)]
		OverviewColT = [[LPBC, LPBC + 2 << 4, LPBC + 3 + (3 << 4)],	[LPBC + 1, LPBC + 2, LPBC + 3 + (1 << 4)]]
		R = utils.TRect(0, 0, 0, 0)
		R2 = utils.TRect(0, 0, 0, 0)

		if device.isAssigned():
			#EnterCriticalSection(BtnMapLock);
			if (self.ClipOfs >= -1) | (self.BtnT[0] > 0):
				if self.BtnT[0] > 0:
					# overview
					R2.Left = self.ClipOfs;
					if R2.Left < 0:
						R2.Left -= 128
					R2.Right = R2.Left + OverW - 1
					R2.Top = 1 + self.TrackOfs
					R2.Bottom = R2.Top + OverH - 1
					for y in range(0, PadsH):
						for x in range(0, PadsW):
							if x < (PadsW - 1):
								R.Left = x * OverW
								R.Right = R.Left + OverW - 1
								R.Top = 1 + y * OverH
								R.Bottom = R.Top + OverH - 1
								o = patterns.getBlockSetStatus(R.Left, R.Top, R.Right, R.Bottom)
								v = OverviewColT[utils.RectOverlapEqual(R, R2)][o]
							else:
								v = OverviewColT[y == (-1 - self.ClipOfs)][int(y <= launchMapPages.length())]
							self.BtnMap[y][x] = v
				else:
					Ofs = self.TrackOfs
					for y in range(max(FirstTrackNum - Ofs, 1), min(LastTrackNum - Ofs, PadsH + 1)):
						StatusColT[1] = LoopColT[playlist.getLiveLoopMode(y + Ofs)]
						StatusColT[2] = TrigColT[playlist.getLiveTriggerMode(y + Ofs)]
						StatusColT[3] = PlayColT[playlist.getLiveTriggerMode(y + Ofs)]

						if self.ClipOfs >= 0:
							# clips
							for x in range(0, PadsW):
								v = launchMapPages.getMapItemColor(-1, (y - 1) * PadsW + x)
								if v < 0:
									if x < (PadsW - 1):
										m = self.ClipOfs + x
										o = playlist.getLiveBlockStatus(y + Ofs, m, midi.LB_Status_Simple)
										v = StatusColT[o]
										if o == self.BlinkState:
											v = v | (1 << 7)
									else:
										v = StatusColT[playlist.getLiveStatus(y + Ofs, midi.LB_Status_Simple)]
								self.BtnMap[y - 1][x] = v
						else:
							# track properties
							#{$IFNDEF CPUx64}
							v = 0
							#{$ENDIF}
							for x in range(0, PadsW):
								if (x == 2) | (x == 3):
									v = SnapColT[min(playlist.getLivePosSnap(y + Ofs), len(SnapColT))-1]
								elif (x == 4) | (x == 5):
									v = SnapColT[min(playlist.getLiveTrigSnap(y + Ofs), len(SnapColT))-1]
								elif (x == 6) | (x == 7):
									v = LoopBtnColT[playlist.getLiveLoopMode(y + Ofs)]
								elif x == 8:
									v = StatusColT[2]
								else:
									continue
								self.BtnMap[y - 1][x] = v

							self.NoFullRefresh = True
							OnIdle() # activity meters
							self.NoFullRefresh = False
			else:
				#custom pages
				for y in range(0, PadsH):
					for x in range(0, PadsW):
						self.BtnMap[y][x] = launchMapPages.getMapItemColor(-self.ClipOfs - 2, y * PadsW + x)

			#LeaveCriticalSection(BtnMapLock);
			self.FullRefresh_Btn()

LaunchPad = TLaunchPad()

def OnInit():
	LaunchPad.OnInit()

def OnDeInit():
	LaunchPad.OnDeInit()

def OnMidiMsg(event):
	LaunchPad.OnMidiMsg(event)

def OnMidiOutMsg(event):
	LaunchPad.OnMidiOutMsg(event)

def OnDoFullRefresh():
	LaunchPad.OnDoFullRefresh()

def OnDisplayZone():
	LaunchPad.OnDisplayZone()

def OnIdle():
	LaunchPad.OnIdle()

def OnUpdateBeatIndicator(Value):
	LaunchPad.OnUpdateBeatIndicator(Value)

def OnRefresh(Flags):
	LaunchPad.OnRefresh(Flags)

def OnUpdateLiveMode(LastTrackNum):
	LaunchPad.OnUpdateLiveMode(LastTrackNum)

