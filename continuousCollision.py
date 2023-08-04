from tkinter import *
import PlatformerTextbox
import numpy as np
import pygame
from time import time


def physicsLoop(dt=30):
    # Queue the next frame
    Character.nextFrame = Character.root.after(dt, physicsLoop)
    newHash = {}
    for P in Character.instances:
        # update the Spacial Hash Table
        for _ in rectangleTraversal(P, 64, dt):
            if _ not in newHash:
                newHash[_] = {}
            newHash[_][P] = True
    Character.hashTable = newHash

    # Check for collisions and apply reactions
    # start by going through each hash bucket to check for collisions.
    # If a collision happens, add the collision to the time queue.
    collisionPears = []
    for val in Character.hashTable.values():
        val = list(val.keys())
        if len(val) > 1:
            for _ in range(len(val)):
                for __ in range(_ + 1, len(val)):
                    pear = (val[_].index, val[__].index)
                    if pear not in collisionPears:
                        timeC, normX, normY = SweptAABB(val[_].x, val[_].y, val[_].x_, val[_].y_, val[_].image.width(),
                                                        val[_].image.height(),
                                                        val[__].x, val[__].y, val[__].x_, val[__].y_,
                                                        val[__].image.width(), val[__].image.height(),
                                                        dt)
                        collisionPears.append(pear)
                        if timeC != 1:
                            if timeC not in Character.collisions:
                                Character.collisions[timeC] = []
                            Character.collisions[timeC].append((val[_], val[__]))

    timeElapsed = 0
    tP = 0
    timeQueue = sorted(Character.collisions)
    while tP < len(timeQueue):
        for P in Character.instances:
            P.x += P.x_ * dt * (timeQueue[tP] - timeElapsed)
            P.y += P.y_ * dt * (timeQueue[tP] - timeElapsed)
        for A, B in Character.collisions[timeQueue[tP]]:
            tim, normX, normY = SweptAABB(A.x, A.y, A.x_, A.y_, A.image.width(), A.image.height(),
                                          B.x, B.y, B.x_, B.y_, B.image.width(), B.image.height(), 1 - timeQueue[tP])
            if tim != 1:
                if A.dynamic != B.dynamic:
                    if normX:
                        A.x_ = 0
                        B.x_ = 0
                    else:
                        A.y_ = 0
                        B.y_ = 0

        timeElapsed = timeQueue[tP]
        tP += 1

    Character.collisions.clear()
    Character.collisions[1] = []

    # update coordinates of the picture and apply acceleration
    for P in Character.instances:
        # x direction acceleration
        P.x_ = P.x_ + sum(P.x__.values()) * dt - P.xDrag * P.x_ * dt
        # y direction acceleration
        P.y_ = P.y_ + sum(P.y__.values()) * dt - P.yDrag * P.y_ * dt

        Character.canvas.coords(P.imageID, P.x, P.y)

    if Character.controlled is not None:
        # Sets the position of the screen and text to follow the Character being controlled
        setScreenPositionX(Character.controlled.x - Character.screenAdjustX)
        setScreenPositionY(Character.controlled.y - Character.screenAdjustY)
        adjustX = PlatformerTextbox.textBox.xScreenPosition
        adjustY = PlatformerTextbox.textBox.yScreenPosition
        if len(PlatformerTextbox.textBox.imagesShown) != 0:
            Character.canvas.coords(PlatformerTextbox.textBox.imagesShown['textBox'],
                                    632 + adjustX,
                                    690 + adjustY)
            Character.canvas.coords(PlatformerTextbox.textBox.imagesShown['faceBox'],
                                    148 + adjustX,
                                    690 + adjustY)
            Character.canvas.coords(PlatformerTextbox.textBox.imagesShown['face'],
                                    148 + adjustX,
                                    690 + adjustY)
        if PlatformerTextbox.textBox.textShown['mainText'] is not None:
            Character.canvas.coords(PlatformerTextbox.textBox.textShown['mainText'],
                                    314 + adjustX,
                                    610 + adjustY)
            if PlatformerTextbox.textBox.textShown['options'] is not None:
                Character.canvas.coords(PlatformerTextbox.textBox.textShown['options'],
                                        750 + adjustX,
                                        610 + adjustY)
                Character.canvas.coords(PlatformerTextbox.textBox.textShown['arrow'],
                                        730 + adjustX,
                                        610 + adjustY)


def SweptAABB(x1, y1, x1_, y1_, width1, height1, x2, y2, x2_, y2_, width2, height2, dt):
    """see https://www.gamedev.net/tutorials/_/technical/game-programming/swept-aabb-collision-detection-and-response-r3084/"""
    vx = (x1_ - x2_) * dt
    vy = (y1_ - y2_) * dt
    if vx > 0:
        xInvEntry = x2 - (x1 + width1)
        xInvExit = (x2 + width2) - x1
    else:
        xInvEntry = (x2 + width2) - x1
        xInvExit = x2 - (x1 + width1)
    if vy > 0:
        yInvEntry = y2 - (y1 + height1)
        yInvExit = (y2 + height2) - y1
    else:
        yInvEntry = (y2 + height2) - y1
        yInvExit = y2 - (y1 + height1)
    if vx == 0:
        xEntry = float('-inf')
        xExit = float('inf')
    else:
        xEntry = xInvEntry / vx
        xExit = xInvExit / vx
    if vy == 0:
        yEntry = float('-inf')
        yExit = float('inf')
    else:
        yEntry = yInvEntry / vy
        yExit = yInvExit / vy
    entryTime = max(xEntry, yEntry)
    exitTime = min(xExit, yExit)
    # If there was no collision
    if entryTime > exitTime or (xEntry < 0 and yEntry < 0) or xEntry > 1 or yEntry > 1:
        normalX = 0
        normalY = 0
        return 1, normalX, normalY
    # If there was a collision
    else:
        # calculate normal of collided surface
        if xEntry > yEntry:
            if xInvEntry < 0:
                normalX = 1
                normalY = 0
            else:
                normalX = -1
                normalY = 0
        else:
            if yInvEntry < 0:
                normalX = 0
                normalY = 1
            else:
                normalX = 0
                normalY = -1
        return entryTime, normalX, normalY


def rectangleTraversal(hoi, grid, dt):
    """ see http://www.cse.yorku.ca/~amana/research/grid.pdf """
    vox = set()

    def mini(xAdj=0, yAdj=0):
        voxels = set()
        xPos = hoi.x + xAdj
        yPos = hoi.y + yAdj
        if hoi.x_ == 0 and hoi.y_ == 0:
            voxels.add((xPos // grid, yPos // grid))
        elif hoi.x_ == 0:
            voxels = voxels.union({(xPos // grid, y) for y in np.arange(min(yPos // grid, (yPos + hoi.y_ * dt) // grid),
                                                                        max(yPos // grid,
                                                                            (yPos + hoi.y_ * dt) // grid) + 1)})
        elif hoi.y_ == 0:
            voxels = voxels.union({(x, yPos // grid) for x in np.arange(min(xPos // grid, (xPos + hoi.x_ * dt) // grid),
                                                                        max(xPos // grid,
                                                                            (xPos + hoi.x_ * dt) // grid) + 1)})
        # Initialization
        else:
            xUnit = xPos // grid
            yUnit = yPos // grid
            stepX = np.sign(hoi.x_)
            stepY = np.sign(hoi.y_)
            xMax = (xPos + hoi.x_ * dt) // grid
            yMax = (yPos + hoi.y_ * dt) // grid
            tMaxX = (grid * (xUnit + (stepX > 0)) - xPos) / (hoi.x_ * dt)
            tMaxY = (grid * (yUnit + (stepY > 0)) - yPos) / (hoi.y_ * dt)
            tDeltaX = grid / abs(hoi.x_ * dt)
            tDeltaY = grid / abs(hoi.y_ * dt)
            voxels.add((xUnit, yUnit))
            # incremental traversal
            while xUnit != xMax or yUnit != yMax:
                if tMaxX < tMaxY:
                    tMaxX = tMaxX + tDeltaX
                    xUnit = xUnit + stepX
                else:
                    tMaxY = tMaxY + tDeltaY
                    yUnit = yUnit + stepY
                voxels.add((xUnit, yUnit))
        return voxels

    if np.sign(hoi.x_) == 1 and np.sign(hoi.y_) == -1:
        vox = vox.union(mini())
        vox = vox.union(mini(hoi.image.width(), hoi.image.height()))
        for i in np.arange(hoi.x // grid, (hoi.x + hoi.image.width()) // grid + 1):
            vox.add((i, (hoi.y + hoi.image.height()) // grid))
        for j in np.arange(hoi.y // grid, (hoi.y + hoi.image.height()) // grid + 1):
            vox.add((hoi.x // grid, j))
        for i in np.arange((hoi.x + hoi.x_ * dt) // grid, (hoi.x + hoi.x_ * dt + hoi.image.width()) // grid + 1):
            vox.add((i, (hoi.y + hoi.y_ * dt) // grid))
        for j in np.arange((hoi.y + hoi.y_ * dt) // grid, (hoi.y + hoi.y_ * dt + hoi.image.height()) // grid + 1):
            vox.add(((hoi.x + hoi.image.width() + hoi.x_ * dt) // grid, j))
    elif np.sign(hoi.x_) == -1 and np.sign(hoi.y_) == 1:
        vox = vox.union(mini())
        vox = vox.union(mini(hoi.image.width(), hoi.image.height()))
        for i in np.arange(hoi.x // grid, (hoi.x + hoi.image.width()) // grid + 1):
            vox.add((i, hoi.y // grid))
        for j in np.arange(hoi.y // grid, (hoi.y + hoi.image.height()) // grid + 1):
            vox.add(((hoi.x + hoi.image.width()) // grid, j))
        for i in np.arange((hoi.x + hoi.x_ * dt) // grid, (hoi.x + hoi.x_ * dt + hoi.image.width()) // grid + 1):
            vox.add((i, (hoi.y + hoi.image.height() + hoi.y_ * dt) // grid))
        for j in np.arange((hoi.y + hoi.y_ * dt) // grid, (hoi.y + hoi.y_ * dt + hoi.image.height()) // grid + 1):
            vox.add(((hoi.x + hoi.x_ * dt) // grid, j))
    elif np.sign(hoi.x_) == 1 and np.sign(hoi.y_) == 1:
        vox = vox.union(mini(hoi.image.width(), 0))
        vox = vox.union(mini(0, hoi.image.height()))
        for i in np.arange(hoi.x // grid, (hoi.x + hoi.image.width()) // grid + 1):
            vox.add((i, hoi.y // grid))
        for j in np.arange(hoi.y // grid, (hoi.y + hoi.image.height()) // grid + 1):
            vox.add((hoi.x // grid, j))
        for i in np.arange((hoi.x + hoi.x_ * dt) // grid, (hoi.x + hoi.x_ * dt + hoi.image.width()) // grid + 1):
            vox.add((i, (hoi.y + hoi.image.height() + hoi.y_ * dt) // grid))
        for j in np.arange((hoi.y + hoi.y_ * dt) // grid, (hoi.y + hoi.y_ * dt + hoi.image.height()) // grid + 1):
            vox.add(((hoi.x + hoi.x_ * dt + hoi.image.width()) // grid, j))
    elif np.sign(hoi.x_) == -1 and np.sign(hoi.y_) == -1:
        vox = vox.union(mini(hoi.image.width(), 0))
        vox = vox.union(mini(0, hoi.image.height()))
        for i in np.arange(hoi.x // grid, (hoi.x + hoi.image.width()) // grid + 1):
            vox.add((i, (hoi.y + hoi.image.height()) // grid))
        for j in np.arange(hoi.y // grid, (hoi.y + hoi.image.height()) // grid + 1):
            vox.add(((hoi.x + hoi.image.width()) // grid, j))
        for i in np.arange((hoi.x + hoi.x_ * dt) // grid, (hoi.x + hoi.x_ * dt + hoi.image.width()) // grid + 1):
            vox.add((i, (hoi.y + hoi.y_ * dt) // grid))
        for j in np.arange((hoi.y + hoi.y_ * dt) // grid, (hoi.y + hoi.y_ * dt + hoi.image.height()) // grid + 1):
            vox.add(((hoi.x + hoi.x_ * dt) // grid, j))
    elif np.sign(hoi.x_) == 0 and np.sign(hoi.y_) == 1:
        for i in np.arange(hoi.x // grid, (hoi.x + hoi.image.width() + hoi.x_ * dt) // grid + 1):
            vox.add((i, (hoi.y + hoi.image.height() + hoi.y_ * dt) // grid))
            vox.add((i, hoi.y // grid))
        for j in np.arange(hoi.y // grid, (hoi.y + hoi.image.height() + hoi.y_ * dt) // grid + 1):
            vox.add(((hoi.x + hoi.image.width()) // grid, j))
            vox.add((hoi.x // grid, j))
    elif np.sign(hoi.x_) == 0 and np.sign(hoi.y_) == -1:
        for i in np.arange(hoi.x // grid, (hoi.x + hoi.image.width()) // grid + 1):
            vox.add((i, (hoi.y + hoi.y_ * dt) // grid))
            vox.add((i, (hoi.y + hoi.image.height()) // grid))
        for j in np.arange((hoi.y + hoi.y_ * dt) // grid, (hoi.y + hoi.image.height()) // grid + 1):
            vox.add(((hoi.x + hoi.image.width()) // grid, j))
            vox.add((hoi.x // grid, j))
    elif np.sign(hoi.x_) == 1 and np.sign(hoi.y_) == 0:
        for i in np.arange(hoi.x // grid, (hoi.x + hoi.image.width() + hoi.x_ * dt) // grid + 1):
            vox.add((i, hoi.y // grid))
            vox.add((i, (hoi.y + hoi.image.height()) // grid))
        for j in np.arange(hoi.y // grid, (hoi.y + hoi.image.height()) // grid + 1):
            vox.add(((hoi.x + hoi.image.width() + hoi.x_ * dt) // grid, j))
            vox.add((hoi.x // grid, j))
    else:
        for i in np.arange((hoi.x + hoi.x_ * dt) // grid, (hoi.x + hoi.image.width()) // grid + 1):
            vox.add((i, hoi.y // grid))
            vox.add((i, (hoi.y + hoi.image.height()) // grid))
        for j in np.arange(hoi.y // grid, (hoi.y + hoi.image.height()) // grid + 1):
            vox.add(((hoi.x + hoi.image.width()) // grid, j))
            vox.add(((hoi.x + hoi.x_ * dt) // grid, j))
    return vox


def gainControl(chara):
    Character.controlled = chara
    Character.canvas.bind("<KeyPress-space>", key_pressed)
    Character.canvas.bind("<KeyRelease-space>", key_release)
    Character.canvas.bind("<KeyPress-Up>", key_pressed)
    Character.canvas.bind("<KeyRelease-Up>", key_release)
    Character.canvas.bind("<KeyPress-Down>", key_pressed)
    Character.canvas.bind("<KeyRelease-Down>", key_release)
    Character.canvas.bind("<KeyPress-Left>", key_pressed)
    Character.canvas.bind("<KeyRelease-Left>", key_release)
    Character.canvas.bind("<KeyPress-Right>", key_pressed)
    Character.canvas.bind("<KeyRelease-Right>", key_release)
    Character.canvas.focus_set()


def key_pressed(event):
    Character.keys[event.keysym] = True
    if not Character.lockedKeys[event.keysym]:
        pass


def keyLock(key):
    Character.lockedKeys[key] = True


def keyUnlock(key):
    Character.lockedKeys[key] = False


def key_release(event):
    Character.keys[event.keysym] = False
    if not Character.lockedKeys[event.keysym]:
        pass


class Character:
    canvas = None
    root = None
    instances = []
    nextFrame = None
    hashTable = {}
    collisions = {1: []}
    controlled = None
    keys = {'Left': False, 'Right': False, 'Down': False}
    lockedKeys = {'Left': False, 'Right': False, 'Down': False, 'Up': False, 'space': False}
    screenAdjustX = 450
    screenAdjustY = 450

    loopsRunning = []

    xLevelSize = 1024
    yLevelSize = 768
    xScreenPosition = 0
    yScreenPosition = 0

    def __init__(self, pic, pic2=None, dynamic=True):
        self.x = 0
        self.y = 0
        self.x_ = 0
        self.y_ = 0
        self.x__ = {}
        self.y__ = {}

        self.xDrag = 0
        self.yDrag = 0
        self.xElastic = 0
        self.yElastic = 0
        self.image = PhotoImage(file=pic)
        self.imageID = None
        if pic2 is not None:
            self.image2 = PhotoImage(file=pic2)
        self.dynamic = dynamic
        self.mass = 1
        self.collisions = {}

        Character.instances.append(self)
        self.index = len(Character.instances)

    def spawnChar(self, x, y):
        """Draws character and saves them to the hash table"""
        self.x = x
        self.y = y
        self.imageID = Character.canvas.create_image(x, y, anchor='nw', image=self.image)


def setLevelSize(xSize, ySize):
    """Defines the scrollable region of the canvas and saves the info within the Character class"""
    Character.canvas.configure(scrollregion=(0, 0, xSize, ySize))
    Character.xLevelSize = xSize
    Character.yLevelSize = ySize


def setScreenPositionX(x):
    Character.xScreenPosition = x
    PlatformerTextbox.textBox.xScreenPosition = min(max(0, x), Character.xLevelSize - int(1024 * 1.3))
    Character.canvas.xview_moveto(x / Character.xLevelSize)


def setScreenPositionY(y):
    Character.yScreenPosition = y
    PlatformerTextbox.textBox.yScreenPosition = min(max(0, y), Character.yLevelSize - int(768 * 1.1))
    Character.canvas.yview_moveto(y / Character.yLevelSize)


class Canvas(Canvas):
    def unbind(self, sequence, funcId=None):
        """
        See:
            https://stackoverflow.com/questions/6433369/
            deleting-and-changing-a-tkinter-event-binding-in-python
        """

        if not funcId:
            # noinspection PyUnresolvedReferences
            self.tk.call('bind', self._w, sequence, '')
            return
        # noinspection PyUnresolvedReferences
        func_callbacks = self.tk.call(
            'bind', self._w, sequence, None).split('\n')
        new_callbacks = [
            lo for lo in func_callbacks if lo[6:6 + len(funcId)] != funcId]
        # noinspection PyUnresolvedReferences
        self.tk.call('bind', self._w, sequence, '\n'.join(new_callbacks))
        self.deletecommand(funcId)


def startGame():
    text = Character.canvas.create_text(width / 2, height / 2, text="Press X to start", fill="white", font="system 18")
    textFlicker(Character.root, Character.canvas, text)
    Character.canvas.bind("<KeyPress-z>", lambda event: startOpeningScene())


def textFlicker(root, canvas, text):
    """Switches the color of text from white to black every 0.5 seconds"""
    if canvas.itemcget(text, 'fill') == 'white':
        canvas.itemconfigure(text, fill='black')
    else:
        canvas.itemconfigure(text, fill='white')
    loop = root.after(500, textFlicker, root, canvas, text)
    Character.loopsRunning.append(loop)


def startOpeningScene():
    clearWindow()
    pygame.mixer.music.load('PreludeInCMinor.mp3')
    pygame.mixer.music.play(loops=-1, fade_ms=3000)
    Character.canvas.create_text(width / 2, height / 2, text=" by Jack Meyer Garvey", fill="white",
                                 font="system 32")
    loop = Character.root.after(2500, openingScene)
    Character.loopsRunning.append(loop)


def openingScene():
    clearWindow()
    Character('WhiteFloor.png', dynamic=False).spawnChar(0, height / 2 + 63.01)
    Character('WhiteFloor.png', dynamic=False).spawnChar(width / 2 + 60, height / 2 + 64)
    You = Character('BlueBoxDot.png')
    You.y__['gravity'] = 0.002
    You.spawnChar(400.1, -64)

    You = Character(pic='BlueBox.png', pic2='WhiteBox.png')
    You.y__['gravity'] = 0.002
    You.x_ = 0.05
    gainControl(You)
    You.spawnChar(400.1, height / 2 - 10)
    setLevelSize(width, height)
    physicsLoop()


def clearWindow():
    """Destroys all widgets and ends all loops (including loops within text boxes)"""
    Character.instances.clear()
    if Character.nextFrame is not None:
        Character.root.after_cancel(Character.nextFrame)
        Character.nextFrame = None
    for loop in Character.loopsRunning:
        Character.root.after_cancel(loop)
    for loop in PlatformerTextbox.textBox.loopsRunning:
        Character.root.after_cancel(loop)
    Character.loopsRunning.clear()
    PlatformerTextbox.clearText()
    PlatformerTextbox.textBox.loopsRunning.clear()
    for widget in Character.root.winfo_children():
        widget.destroy()
    PlatformerTextbox.textBox.instances.clear()
    PlatformerTextbox.textBox.textQueue.clear()
    PlatformerTextbox.textBox.questionQueue.clear()
    PlatformerTextbox.textBox.openFunctions.clear()
    PlatformerTextbox.textBox.exitFunctions.clear()
    Character.controlled = None
    Character.keys = {'Left': False, 'Right': False, 'Down': False}
    Character.lockedKeys = {'Left': False, 'Right': False, 'Down': False, 'Up': False, 'space': False}
    Character.canvas = Canvas(Character.root, width=width, height=height, bg='black')
    PlatformerTextbox.textBox.canvas = Character.canvas
    Character.canvas.focus_set()
    Character.canvas.pack()


width = int(1024 * 1.3)
height = int(768 * 1.1)
Character.root = Tk()
PlatformerTextbox.textBox.root = Character.root
Character.root.geometry(f"{width}x{height}")
Character.root.configure(background='black')
Character.root.attributes("-fullscreen", True)
Character.root.title("PlatFormer")
Character.canvas = Canvas(Character.root, width=width, height=height, bg='black')
PlatformerTextbox.textBox.canvas = Character.canvas
Character.canvas.focus_set()
pygame.init()
pygame.mixer.init()

startGame()
Character.start = time()

Character.canvas.pack()
mainloop()
