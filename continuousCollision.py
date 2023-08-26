from tkinter import *
from audio import *
import PlatformerTextbox
import numpy as np
from time import time
import collections
from fractions import Fraction


def physicsLoop():
    grid = Character.grid
    dt = Character.dt
    start = time()

    # Queue the next frame
    Character.nextFrame = Character.root.after(dt, physicsLoop)

    if Character.jumpBuffer:
        Character.jumpBuffer -= 1
        Character.controlled.jump(False)

    # Run the queued functions from between frames
    for _ in Character.oncePerFrame:
        _()
    Character.oncePerFrame.clear()

    # If x is being pressed, rewind
    if Character.keys['x']:
        rewind()
        return

    if Character.controlled is not None:
        if Character.controlled.y_ >= 0:
            Character.controlled.y__['gravity'] = Fraction(0.004)
        if Character.keys['space'] and Character.controlled.beneath(grid):
            Character.controlled.glide()
        elif Character.keys['Left'] and not Character.keys['Right']:
            Character.controlled.move(-1)
        elif Character.keys['Right'] and not Character.keys['Left']:
            Character.controlled.move(1)

    newHash = {key: val.copy() for key, val in Character.stableHashTable.items()}
    for P in Character.dynamicChars:
        # Save the previous frame for rewind
        P.xPath.append(P.x)
        P.yPath.append(P.y)
        P.x_Path.append(P.x_)
        P.y_Path.append(P.y_)
        # update the Spacial Hash Table
        for _ in P.rectangleTraversal(grid, dt):
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
                        truth, normX, normY, timeC = SweptAABB(val[_].x, val[_].y, val[_].x_, val[_].y_,
                                                               val[_].image.width(),
                                                               val[_].image.height(),
                                                               val[__].x, val[__].y, val[__].x_, val[__].y_,
                                                               val[__].image.width(), val[__].image.height(),
                                                               dt)
                        collisionPears.append(pear)
                        if not truth:
                            if timeC not in Character.collisions:
                                Character.collisions[timeC] = {}
                            Character.collisions[timeC][(val[_].index, val[__].index)] = True
    # sequentially resolve collisions in the order that they occur
    # for each pair of colliding objects, check if the collision should still occur
    # then resolve the collision
    # finally, check for any new collisions resulting from this resolution
    timeElapsed = 0
    tP = 0
    timeQueue = sorted(Character.collisions.keys())
    while tP < len(timeQueue):
        for P in Character.dynamicChars:
            P.x += P.x_ * dt * (timeQueue[tP] - timeElapsed)
            P.y += P.y_ * dt * (timeQueue[tP] - timeElapsed)
        pairQueue = list(Character.collisions[timeQueue[tP]].keys())
        for A, B in pairQueue:
            A = Character.instances[A]
            B = Character.instances[B]
            truth, normX, normY, tim = SweptAABB(A.x, A.y, A.x_, A.y_, A.image.width(), A.image.height(),
                                                 B.x, B.y, B.x_, B.y_, B.image.width(), B.image.height(),
                                                 1 - timeQueue[tP])
            if not truth:
                if A.dynamic != B.dynamic:
                    if normX:
                        A.x_ = 0
                        B.x_ = 0
                    else:
                        A.y_ = 0
                        B.y_ = 0
                else:
                    if normX:
                        A.x_, B.x_ = B.x_, A.x_
                    else:
                        A.y_, B.y_ = B.y_, A.y_
                collisionPears = set()
                for C in [A, B]:
                    if C.dynamic:
                        for _ in C.rectangleTraversal(grid, dt * (1 - timeQueue[tP])):
                            if _ in Character.hashTable:
                                for D in Character.hashTable[_]:
                                    if (C.index, D.index) not in collisionPears and C.index != D.index:
                                        collisionPears.add((C.index, D.index))
                                        truth, normX, normY, timeC = SweptAABB(C.x, C.y, C.x_, C.y_,
                                                                               C.image.width(),
                                                                               C.image.height(),
                                                                               D.x, D.y, D.x_, D.y_,
                                                                               D.image.width(), D.image.height(),
                                                                               dt * (1 - timeQueue[tP]))
                                        if not truth:
                                            timeC = timeQueue[tP] + (1 - timeQueue[tP]) * timeC
                                            if timeC not in Character.collisions:
                                                Character.collisions[timeC] = {}
                                            Character.collisions[timeC][(C.index, D.index)] = True
                                            if timeC not in timeQueue:
                                                timeQueue.append(timeC)
                                            elif timeC == timeQueue[tP]:
                                                pairQueue.append((C.index, D.index))
                            else:
                                Character.hashTable[_] = {}
                            Character.hashTable[_][A] = True
        timeQueue = sorted(timeQueue)
        timeElapsed = timeQueue[tP]
        tP += 1
    Character.collisions.clear()
    Character.collisions[1] = {}

    if Character.controlled is not None:
        truth, Character.controlled.relativeX_ = Character.controlled.onGround(grid)
        if truth:
            Character.isGrounded.append(True)
            if Character.keys['Right']:
                Character.controlled.xDrag = max(-Fraction(0.01) * np.sign(Character.controlled.x_), 0)
            elif Character.keys['Left']:
                Character.controlled.xDrag = max(Fraction(0.01) * np.sign(Character.controlled.x_), 0)
            else:
                Character.controlled.xDrag = Fraction(0.01)

        else:
            Character.isGrounded.append(False)
            Character.controlled.xDrag = 0

        truth, direction, jumpDirection = Character.controlled.onWall(grid)
        if truth and Character.keys[direction]:
            Character.controlled.yDrag = max(Fraction(0.01) * np.sign(Character.controlled.y_), 0)
        else:
            Character.controlled.yDrag = 0

            # update coordinates of the picture and apply acceleration
    for P in Character.dynamicChars:
        # x direction acceleration
        P.x_ = round(P.x_ + sum(P.x__.values()) * dt - P.xDrag * (P.x_ - P.relativeX_) * dt, 5)
        # y direction acceleration
        P.y_ = round(P.y_ + sum(P.y__.values()) * dt - P.yDrag * P.y_ * dt, 5)

        Character.canvas.coords(P.imageID, float(P.x), float(P.y))

    for P in animation.active.copy():
        animation.instances[P].nextFrame()

    centerScreen()

    end = time()
    total = 1000 * (end - start)
    if total > 20:
        print(total)


def freezePhysics():
    Character.root.after_cancel(Character.nextFrame)


def unfreezePhysics():
    Character.oncePerFrame.clear()
    physicsLoop()


def centerScreen():
    if Character.controlled is not None:
        previous = Character.canvas.xview()[0]
        # Sets the position of the screen and text to follow the Character being controlled
        setScreenPositionX(float(Character.controlled.x) - Character.screenAdjustX)
        setScreenPositionY(float(Character.controlled.y) - Character.screenAdjustY)
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
        netChange = Character.canvas.xview()[0] - previous
        for P in background.instances:
            if P.layer:
                P.x -= netChange * 0.1 * P.layer * Character.xLevelSize
                Character.canvas.coords(P.imageID, float(P.x), float(P.y))


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
        if x1 >= x2 + width2 or x2 >= x1 + width1:
            return 1, 0, 0, 1
        xEntry = float('-inf')
        xExit = float('inf')
    else:
        xEntry = xInvEntry / vx
        xExit = xInvExit / vx
    if vy == 0:
        if y1 >= y2 + height2 or y2 >= y1 + height1:
            return 1, 0, 0, 1
        yEntry = float('-inf')
        yExit = float('inf')
    else:
        yEntry = yInvEntry / vy
        yExit = yInvExit / vy
    entryTime = max(xEntry, yEntry)
    exitTime = min(xExit, yExit)
    # If there was no collision
    if entryTime > exitTime or xEntry > 1 or yEntry > 1:
        normalX = 0
        normalY = 0
        return 1, normalX, normalY, 1
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
        if xEntry < 0 and yEntry < 0:
            return 1, normalX, normalY, entryTime

        return 0, normalX, normalY, entryTime


def key_pressed(event, func=None):
    if func is not None:
        Character.oncePerFrame.append(func)
    Character.keys[event.keysym] = True


def key_release(event, func=None):
    if func is not None:
        Character.oncePerFrame.append(func)
    Character.keys[event.keysym] = False


def rewind():
    Character.isGrounded.clear()
    Character.jumpBuffer = 0
    newHash = {key: val.copy() for key, val in Character.stableHashTable.items()}
    for P in Character.dynamicChars:
        if len(P.xPath):
            P.x = P.xPath.pop()
            P.y = P.yPath.pop()
            P.x_ = P.x_Path.pop()
            P.y_ = P.y_Path.pop()

            Character.canvas.coords(P.imageID, float(P.x), float(P.y))

        for _ in P.rectangleTraversal(Character.grid, Character.dt):
            if _ not in newHash:
                newHash[_] = {}
            newHash[_][P] = True
    Character.hashTable = newHash
    Character.isGrounded.append(Character.controlled.onGround(Character.grid)[0])
    for P in animation.active:
        P = animation.instances[P]
        if len(P.framePath):
            P.previousFrame()

    centerScreen()


class Character:
    canvas = None
    root = None
    instances = []
    dynamicChars = []
    notDynChars = []
    nextFrame = None
    hashTable = {}
    stableHashTable = {}
    collisions = {1: {}}
    controlled = None
    keys = {'z': False, 'x': False, 'space': False, 'Left': False, 'Right': False, 'Up': False, 'Down': False}
    isGrounded = collections.deque(maxlen=4)
    jumpBuffer = 0
    oncePerFrame = []
    screenAdjustX = 602
    screenAdjustY = 450

    loopsRunning = []

    xLevelSize = 1024
    yLevelSize = 768
    grid = 300
    dt = 20

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
        self.relativeX_ = 0
        self.image = PhotoImage(file=pic)
        self.imageID = None
        if pic2 is not None:
            self.image2 = PhotoImage(file=pic2)
        self.dynamic = dynamic
        if dynamic:
            Character.dynamicChars.append(self)
        else:
            Character.notDynChars.append(self)
        self.mass = 1

        Character.instances.append(self)
        self.index = len(Character.instances) - 1

        if self.dynamic:
            self.xPath = collections.deque(maxlen=3000)
            self.yPath = collections.deque(maxlen=3000)
            self.x_Path = collections.deque(maxlen=3000)
            self.y_Path = collections.deque(maxlen=3000)

    def spawnChar(self, x, y, anchor='nw'):
        """Draws character in given position"""
        self.x = Fraction(x)
        self.y = Fraction(y)
        self.imageID = Character.canvas.create_image(x, y, anchor=anchor, image=self.image)
        if self.dynamic:
            for _ in self.rectangleTraversal(Character.grid, Character.dt):
                if _ not in Character.hashTable:
                    Character.hashTable[_] = {}
                Character.hashTable[_][self] = True
        else:
            for _ in self.rectangleTraversal(Character.grid, Character.dt):
                if _ not in Character.hashTable:
                    Character.hashTable[_] = {}
                if _ not in Character.stableHashTable:
                    Character.stableHashTable[_] = {}
                Character.hashTable[_][self] = True
                Character.stableHashTable[_][self] = True

    def rectangleTraversal(self, grid, dt):
        """ see http://www.cse.yorku.ca/~amana/research/grid.pdf """
        vox = set()

        def mini(xAdj=0, yAdj=0):
            voxels = set()
            xPos = self.x + xAdj
            yPos = self.y + yAdj
            if self.x_ == 0 and self.y_ == 0:
                voxels.add((xPos // grid, yPos // grid))
            elif self.x_ == 0:
                voxels = voxels.union(
                    {(xPos // grid, y) for y in np.arange(min(yPos // grid, (yPos + self.y_ * dt) // grid),
                                                          max(yPos // grid,
                                                              (yPos + self.y_ * dt) // grid) + 1)})
            elif self.y_ == 0:
                voxels = voxels.union(
                    {(x, yPos // grid) for x in np.arange(min(xPos // grid, (xPos + self.x_ * dt) // grid),
                                                          max(xPos // grid,
                                                              (xPos + self.x_ * dt) // grid) + 1)})
            # Initialization
            else:
                xUnit = xPos // grid
                yUnit = yPos // grid
                stepX = np.sign(self.x_)
                stepY = np.sign(self.y_)
                xMax = (xPos + self.x_ * dt) // grid
                yMax = (yPos + self.y_ * dt) // grid
                tMaxX = (grid * (xUnit + (stepX > 0)) - xPos) / (self.x_ * dt)
                tMaxY = (grid * (yUnit + (stepY > 0)) - yPos) / (self.y_ * dt)
                tDeltaX = grid / abs(self.x_ * dt)
                tDeltaY = grid / abs(self.y_ * dt)
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

        if np.sign(self.x_) == 1 and np.sign(self.y_) == -1:
            vox = vox.union(mini())
            vox = vox.union(mini(self.image.width(), self.image.height()))
            for i in np.arange(self.x // grid, (self.x + self.image.width()) // grid + 1):
                vox.add((i, (self.y + self.image.height()) // grid))
            for j in np.arange(self.y // grid, (self.y + self.image.height()) // grid + 1):
                vox.add((self.x // grid, j))
            for i in np.arange((self.x + self.x_ * dt) // grid,
                               (self.x + self.x_ * dt + self.image.width()) // grid + 1):
                vox.add((i, (self.y + self.y_ * dt) // grid))
            for j in np.arange((self.y + self.y_ * dt) // grid,
                               (self.y + self.y_ * dt + self.image.height()) // grid + 1):
                vox.add(((self.x + self.image.width() + self.x_ * dt) // grid, j))
        elif np.sign(self.x_) == -1 and np.sign(self.y_) == 1:
            vox = vox.union(mini())
            vox = vox.union(mini(self.image.width(), self.image.height()))
            for i in np.arange(self.x // grid, (self.x + self.image.width()) // grid + 1):
                vox.add((i, self.y // grid))
            for j in np.arange(self.y // grid, (self.y + self.image.height()) // grid + 1):
                vox.add(((self.x + self.image.width()) // grid, j))
            for i in np.arange((self.x + self.x_ * dt) // grid,
                               (self.x + self.x_ * dt + self.image.width()) // grid + 1):
                vox.add((i, (self.y + self.image.height() + self.y_ * dt) // grid))
            for j in np.arange((self.y + self.y_ * dt) // grid,
                               (self.y + self.y_ * dt + self.image.height()) // grid + 1):
                vox.add(((self.x + self.x_ * dt) // grid, j))
        elif np.sign(self.x_) == 1 and np.sign(self.y_) == 1:
            vox = vox.union(mini(self.image.width(), 0))
            vox = vox.union(mini(0, self.image.height()))
            for i in np.arange(self.x // grid, (self.x + self.image.width()) // grid + 1):
                vox.add((i, self.y // grid))
            for j in np.arange(self.y // grid, (self.y + self.image.height()) // grid + 1):
                vox.add((self.x // grid, j))
            for i in np.arange((self.x + self.x_ * dt) // grid,
                               (self.x + self.x_ * dt + self.image.width()) // grid + 1):
                vox.add((i, (self.y + self.image.height() + self.y_ * dt) // grid))
            for j in np.arange((self.y + self.y_ * dt) // grid,
                               (self.y + self.y_ * dt + self.image.height()) // grid + 1):
                vox.add(((self.x + self.x_ * dt + self.image.width()) // grid, j))
        elif np.sign(self.x_) == -1 and np.sign(self.y_) == -1:
            vox = vox.union(mini(self.image.width(), 0))
            vox = vox.union(mini(0, self.image.height()))
            for i in np.arange(self.x // grid, (self.x + self.image.width()) // grid + 1):
                vox.add((i, (self.y + self.image.height()) // grid))
            for j in np.arange(self.y // grid, (self.y + self.image.height()) // grid + 1):
                vox.add(((self.x + self.image.width()) // grid, j))
            for i in np.arange((self.x + self.x_ * dt) // grid,
                               (self.x + self.x_ * dt + self.image.width()) // grid + 1):
                vox.add((i, (self.y + self.y_ * dt) // grid))
            for j in np.arange((self.y + self.y_ * dt) // grid,
                               (self.y + self.y_ * dt + self.image.height()) // grid + 1):
                vox.add(((self.x + self.x_ * dt) // grid, j))
        elif np.sign(self.x_) == 0 and np.sign(self.y_) == 1:
            for i in np.arange(self.x // grid, (self.x + self.image.width() + self.x_ * dt) // grid + 1):
                vox.add((i, (self.y + self.image.height() + self.y_ * dt) // grid))
                vox.add((i, self.y // grid))
            for j in np.arange(self.y // grid, (self.y + self.image.height() + self.y_ * dt) // grid + 1):
                vox.add(((self.x + self.image.width()) // grid, j))
                vox.add((self.x // grid, j))
        elif np.sign(self.x_) == 0 and np.sign(self.y_) == -1:
            for i in np.arange(self.x // grid, (self.x + self.image.width()) // grid + 1):
                vox.add((i, (self.y + self.y_ * dt) // grid))
                vox.add((i, (self.y + self.image.height()) // grid))
            for j in np.arange((self.y + self.y_ * dt) // grid, (self.y + self.image.height()) // grid + 1):
                vox.add(((self.x + self.image.width()) // grid, j))
                vox.add((self.x // grid, j))
        elif np.sign(self.x_) == 1 and np.sign(self.y_) == 0:
            for i in np.arange(self.x // grid, (self.x + self.image.width() + self.x_ * dt) // grid + 1):
                vox.add((i, self.y // grid))
                vox.add((i, (self.y + self.image.height()) // grid))
            for j in np.arange(self.y // grid, (self.y + self.image.height()) // grid + 1):
                vox.add(((self.x + self.image.width() + self.x_ * dt) // grid, j))
                vox.add((self.x // grid, j))
        else:
            for i in np.arange((self.x + self.x_ * dt) // grid, (self.x + self.image.width()) // grid + 1):
                vox.add((i, self.y // grid))
                vox.add((i, (self.y + self.image.height()) // grid))
            for j in np.arange(self.y // grid, (self.y + self.image.height()) // grid + 1):
                vox.add(((self.x + self.image.width()) // grid, j))
                vox.add(((self.x + self.x_ * dt) // grid, j))
        return vox

    def gainControl(self):
        """Binds the character controls and marks the given Character as being controlled"""
        Character.controlled = self
        Character.canvas.bind("<KeyPress-space>", lambda event: key_pressed(event, self.jump))
        Character.canvas.bind("<KeyRelease-space>", lambda event: key_release(event, self.jumpRelease))
        Character.canvas.bind("<KeyPress-z>", lambda event: key_pressed(event, self.inspect))
        Character.canvas.bind("<KeyRelease-z>", key_release)
        Character.canvas.bind("<KeyPress-x>", key_pressed)
        Character.canvas.bind("<KeyRelease-x>", key_release)
        Character.canvas.bind("<KeyPress-Up>", key_pressed)
        Character.canvas.bind("<KeyRelease-Up>", key_release)
        Character.canvas.bind("<KeyPress-Down>", key_pressed)
        Character.canvas.bind("<KeyRelease-Down>", key_release)
        Character.canvas.bind("<KeyPress-Left>", key_pressed)
        Character.canvas.bind("<KeyRelease-Left>", key_release)
        Character.canvas.bind("<KeyPress-Right>", key_pressed)
        Character.canvas.bind("<KeyRelease-Right>", key_release)
        Character.canvas.focus_set()

    def beneath(self, grid):
        for _ in np.arange(self.x // grid, (self.x + self.image.width()) // grid + 1):
            if (_, self.y // grid) in Character.stableHashTable:
                for P in Character.stableHashTable[(_, self.y // grid)]:
                    if self.y == P.y + P.image.height() and \
                            (self.x <= (P.x + P.image.width()) and P.x <= (self.x + self.image.width())):
                        return True
        return False

    def onGround(self, grid):
        for _ in np.arange(self.x // grid, (self.x + self.image.width()) // grid + 1):
            if (_, (self.y + self.image.height()) // grid) in Character.hashTable:
                for P in Character.hashTable[(_, (self.y + self.image.height()) // grid)]:
                    if P != self and P.y == self.y + self.image.height() and \
                            (self.x <= (P.x + P.image.width()) and P.x <= (self.x + self.image.width())):
                        return True, P.x_
        return False, 0

    def onWall(self, grid):
        for _ in np.arange(self.y // grid, (self.y + self.image.height()) // grid + 1):
            if (self.x // grid, _) in Character.hashTable:
                for P in Character.hashTable[(self.x // grid, _)]:
                    if P != self and self.x == P.x + P.image.width() and \
                            (self.y <= (P.y + P.image.height()) and P.y <= (self.y + self.image.height())):
                        return True, 'Left', 1
            if ((self.x + self.image.width()) // grid, _) in Character.hashTable:
                for P in Character.hashTable[((self.x + self.image.width()) // grid, _)]:
                    if P != self and P.x == self.x + self.image.width() and \
                            (self.y <= (P.y + P.image.height()) and P.y <= (self.y + self.image.height())):
                        return True, 'Right', -1
        return False, 'Left', 0

    def jump(self, pressed=True):
        if pressed:
            Character.jumpBuffer = 4
        truth, direction, jumpDirection = self.onWall(Character.grid)
        if Character.keys['space']:
            self.y__['gravity'] = Fraction(0.002)
        else:
            self.y__['gravity'] = Fraction(0.008)
        if any(Character.isGrounded):
            Character.isGrounded.clear()
            if self.y_ >= 0:
                self.y_ = -(abs(self.x_) / 4 + Fraction(4, 5))
            else:
                self.y_ -= abs(self.x_) / 4 + Fraction(4, 5)
            Character.jumpBuffer = 0
        elif truth and Character.keys[direction]:
            self.y_ = -Fraction(4, 5)
            self.x_ = jumpDirection
            Character.jumpBuffer = 0

    def jumpRelease(self):
        self.y__['gravity'] = Fraction(0.008)

    def move(self, direction):
        if self.x_ * direction < 1 + abs(self.relativeX_):
            self.x_ += direction * Fraction(1, 20)

    def glide(self):
        self.y_ = 0

    def inspect(self):
        for _ in np.arange(self.x // Character.grid, (self.x + self.image.width()) // Character.grid + 1):
            for __ in np.arange(self.y // Character.grid, (self.y + self.image.height()) // Character.grid + 1):
                if (_, __) in funcHold.hashTable:
                    for fH in funcHold.hashTable[(_, __)]:
                        if do_overlap(self, fH):
                            fH.inspect()
                            return


def do_overlap(chara, fH):
    if (chara.x < fH.x + fH.width and chara.x + chara.image.width() > fH.x and
            chara.y < fH.y + fH.height and chara.y + chara.image.height() > fH.y):
        return True
    return False


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


class funcHold:
    instances = []
    hashTable = {}

    def __init__(self, pic, *func):
        funcHold.instances.append(self)
        self.image = PhotoImage(file=pic)
        self.imageID = None
        self.func = list(func)
        self.x = 0
        self.y = 0
        self.width = self.image.width() + 20
        self.height = self.image.height() + 20

    def spawn(self, x, y):
        self.x = Fraction(x)
        self.y = Fraction(y)
        self.imageID = Character.canvas.create_image(x, y, anchor='nw', image=self.image)
        for _ in np.arange(self.x // Character.grid, (self.x + self.width) // Character.grid + 1):
            for __ in np.arange(self.y // Character.grid, (self.y + self.height) // Character.grid + 1):
                if (_, __) not in funcHold.hashTable:
                    funcHold.hashTable[(_, __)] = []
                funcHold.hashTable[(_, __)].append(self)

    def inspect(self):
        for func in self.func:
            func()

    def queueText(self, text, face=None, textSpeed=20, options=None, condition=0, openFunctions=None,
                  exitFunctions=None):
        if exitFunctions is None:
            exitFunctions = []
        if openFunctions is None:
            openFunctions = []
        if options is None:
            options = []
        openFunctions.append(freezePhysics)
        exitFunctions.append(unfreezePhysics)
        self.func.append(lambda: PlatformerTextbox.textBox(
            text, face, textSpeed, options, condition, openFunctions, exitFunctions))
        self.func.append(PlatformerTextbox.runQueue)


class background:
    instances = []

    def __init__(self, pic, layer=0):
        background.instances.append(self)
        self.image = PhotoImage(file=pic)
        self.imageID = None
        self.x = 0
        self.y = 0
        self.layer = layer

    def spawn(self, x, y):
        self.x = Fraction(x)
        self.y = Fraction(y)
        self.imageID = Character.canvas.create_image(x, y, anchor='nw', image=self.image)


class animation:
    instances = []
    active = set()

    def __init__(self, imageContainer):
        self.index = len(animation.instances)
        animation.instances.append(self)
        self.container = imageContainer
        self.packages = {}
        self.currentPackage = None
        self.packageIndex = 0
        self.framePath = collections.deque(maxlen=3000)
        self.endFunc = [self.restart]

    def nextFrame(self):
        self.framePath.append((self.packageIndex, self.currentPackage))
        self.packageIndex += 1
        if self.packageIndex == len(self.currentPackage):
            for _ in self.endFunc:
                _()
        else:
            Character.canvas.itemconfig(self.container.imageID, image=self.currentPackage[self.packageIndex])

    def restart(self):
        self.packageIndex = 0
        Character.canvas.itemconfig(self.container.imageID, image=self.currentPackage[self.packageIndex])

    def start(self):
        animation.active.add(self.index)

    def end(self):
        animation.active.remove(self.index)

    def previousFrame(self):
        self.packageIndex, self.currentPackage = self.framePath.pop()
        Character.canvas.itemconfig(self.container.imageID, image=self.currentPackage[self.packageIndex])

    def addImagePackage(self, name, numberOfFrames, specialName=None, switch=True, active=True):
        if specialName is None:
            specialName = name
        if active:
            animation.active.add(self.index)
        pack = []
        for _ in range(numberOfFrames):
            pack.append(PhotoImage(file=f"{name}{_ + 1}.png"))
        self.packages[specialName] = pack
        if switch:
            self.currentPackage = pack

    def switchPack(self, name, index=0, end=None):
        if end is not None:
            self.endFunc.append(end)
        self.currentPackage = self.packages[name]
        self.packageIndex = index


def clearWindow():
    """Destroys all widgets and ends all loops (including loops within text boxes)"""
    if Character.nextFrame is not None:
        Character.root.after_cancel(Character.nextFrame)
        Character.nextFrame = None
    Character.instances.clear()
    background.instances.clear()
    animation.instances.clear()
    animation.active.clear()
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
    Character.hashTable.clear()
    Character.collisions = {1: {}}
    Character.controlled = None
    Character.keys = {'z': False, 'x': False, 'space': False, 'Left': False, 'Right': False, 'Up': False, 'Down': False}
    Character.oncePerFrame.clear()
    Character.grid = 300
    Character.dt = 20
    Character.canvas = Canvas(Character.root, width=1330, height=845, bg='black')
    PlatformerTextbox.textBox.canvas = Character.canvas
    Character.canvas.focus_set()
    Character.canvas.pack()

    Character.dynamicChars.clear()
    Character.notDynChars .clear()
    Character.stableHashTable.clear()
    Character.isGrounded = collections.deque(maxlen=4)
    Character.jumpBuffer = 0

    funcHold.instances.clear()
    funcHold.hashTable.clear()
