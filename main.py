from tkinter import *
import PlatformerTextbox
import pygame


def physicsLoop(dt=30):
    # Queue the next frame
    Character.nextFrame = Character.root.after(dt, physicsLoop)
    newHash = {}
    for P in Character.instances:
        # Apply velocity
        P.x += P.x_ * dt
        P.y += P.y_ * dt
        # prepare for collision detection
        P.newX = P.x
        P.newY = P.y
        P.newX_ = P.x_
        P.newY_ = P.y_
        # update the Spacial Hash Table
        for _ in range(int(P.x // 64) - 1, int(P.x + P.image.width()) // 64):
            for __ in range(int(P.y // 64) - 1, int(P.y + P.image.height()) // 64):
                if (_, __) not in newHash:
                    newHash[(_, __)] = list()
                newHash[(_, __)].append(P)
    Character.hashTable = newHash

    # Check for collisions and apply collision functions
    checkCollision(dt)

    # Complete checks for the character controls
    if Character.controlled is not None:
        if on_Ground(Character.controlled):
            Character.controlled.xDrag = 0.02
        else:
            Character.controlled.xDrag = 0.0005

        # When pushing in an x direction, the drag is reduced, your speed is increased with an acceleration
        # Up until your max speed, which is constant. Midair acceleration is less. Moving into a wall gives a low speed
        if Character.keys['Left'] is True and not Character.lockedKeys['Left']:
            Character.controlled.xDrag = 0.0005
            if touching_Wall_Left(Character.controlled) and Character.controlled.y_ > 0.15:
                Character.controlled.y_ = 0.15
            if Character.controlled.x_ > -0.5:
                if on_Ground(Character.controlled):
                    Character.controlled.x__['move'] = -0.005
                else:
                    Character.controlled.x__['move'] = -0.002
            else:
                Character.controlled.x_ = -0.3

        if Character.keys['Right'] is True and not Character.lockedKeys['Right']:
            Character.controlled.xDrag = 0.0005
            if touching_Wall_Right(Character.controlled) and Character.controlled.y_ > 0.15:
                Character.controlled.y_ = 0.15
            if Character.controlled.x_ < 0.5:
                if on_Ground(Character.controlled):
                    Character.controlled.x__['move'] = 0.005
                else:
                    Character.controlled.x__['move'] = 0.002

            else:
                Character.controlled.x_ = 0.3
        # Sets the position of the screen and text to follow the Character being controlled
        if Character.controlled.x - Character.xScreenPosition > 612 + 10:
            setScreenPositionX(Character.controlled.x - (612 + 10))
        if Character.controlled.x - Character.xScreenPosition < 612 - 10:
            setScreenPositionX(Character.controlled.x - (612 - 10))
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

    # update coordinates of the picture and apply acceleration
    for P in Character.instances:
        # x direction acceleration
        P.x_ += sum(P.x__.values()) * dt - P.xDrag * P.x_ * dt
        # y direction acceleration
        P.y_ += sum(P.y__.values()) * dt - P.yDrag * P.y_ * dt
        Character.canvas.coords(P.imageID, P.x, P.y)


def do_overlap(l1, r1, l2, r2):
    # if rectangle has area 0, no overlap
    if l1[0] == r1[0] or l1[1] == r1[1] or r2[0] == l2[0] or l2[1] == r2[1]:
        return False

    # If one rectangle is on left side of other
    if l1[0] > r2[0] or l2[0] > r1[0]:
        return False

    # If one rectangle is above other
    if r1[1] > l2[1] or r2[1] > l1[1]:
        return False

    return True


def on_Ground(Object1, leniency=2):
    # check the hash buckets directly below the object for overlap
    for _ in range(int(Object1.x // 64) - 1, int(Object1.x + Object1.image.width()) // 64):
        if (_, int((Object1.y + Object1.image.height() + 0.001 * leniency) // 64) - 1) in Character.hashTable:
            for Object2 in Character.hashTable[
                (_, int((Object1.y + Object1.image.height() + 0.001 * leniency) // 64) - 1)]:
                if Object1 != Object2:
                    if do_overlap((Object1.x, - Object1.y),
                                  (Object1.x + Object1.image.width(),
                                   - Object1.y - 0.001 * leniency - Object1.image.height()),
                                  (Object2.x, -Object2.y),
                                  (Object2.x + Object2.image.width(), -Object2.y - Object2.image.height())):
                        return True
    return False


def touching_Wall_Right(Object1, leniency=2):
    for _ in range(int(Object1.y // 64) - 1, int(Object1.y + Object1.image.height()) // 64):
        if (int((Object1.x + Object1.image.height() + 0.001 * leniency) // 64) - 1, _) in Character.hashTable:
            for Object2 in Character.hashTable[
                (int((Object1.x + Object1.image.width() + 0.001 * leniency) // 64) - 1, _)]:
                if Object1 != Object2:
                    if do_overlap((Object1.x, - Object1.y),
                                  (Object1.x + Object1.image.width() + 0.001 * leniency,
                                   - Object1.y - Object1.image.height()),
                                  (Object2.x, -Object2.y),
                                  (Object2.x + Object2.image.width(), -Object2.y - Object2.image.height())):
                        return True
    return False


def touching_Wall_Left(Object1, leniency=2):
    for _ in range(int(Object1.y // 64) - 1, int(Object1.y + Object1.image.height()) // 64):
        if (int((Object1.x - 0.001 * leniency) // 64) - 1, _) in Character.hashTable:
            for Object2 in Character.hashTable[
                (int((Object1.x - 0.001 * leniency) // 64) - 1, _)]:
                if Object1 != Object2:
                    if do_overlap((Object1.x - 0.001 * leniency, - Object1.y),
                                  (Object1.x + Object1.image.width(),
                                   - Object1.y - Object1.image.height()),
                                  (Object2.x, -Object2.y),
                                  (Object2.x + Object2.image.width(), -Object2.y - Object2.image.height())):
                        return True
    return False


def checkCollision(dt):
    collisionFlag = False
    # start by going through each hash bucket to check for collisions.
    # If a collision happens, run the appropriate collision function
    for val in Character.hashTable.values():
        if len(val) > 1:
            for _ in range(len(val)):
                for __ in range(_ + 1, len(val)):
                    if do_overlap((val[_].x, -val[_].y),
                                  (val[_].x + val[_].image.width(), -val[_].y - val[_].image.height()),
                                  (val[__].x, -val[__].y),
                                  (val[__].x + val[__].image.width(), -val[__].y - val[__].image.height())):
                        collisionFlag = True
                        netX = val[_].x_ - val[__].x_
                        netY = val[_].y_ - val[__].y_
                        if netX == 0:
                            if netY > 0:
                                top(val[_], val[__])
                            else:
                                bottom(val[_], val[__])
                        if netY == 0:
                            if netX > 0:
                                left(val[_], val[__])
                            else:
                                right(val[_], val[__])
                        elif netX > 0 and netY > 0:
                            if (val[__].x - val[_].x - val[_].image.width()) / netX <= (
                                    val[__].y - val[_].y - val[_].image.height()) / netY:
                                top(val[_], val[__])
                            if (val[__].x - val[_].x - val[_].image.width()) / netX >= (
                                    val[__].y - val[_].y - val[_].image.height()) / netY:
                                left(val[_], val[__])
                        elif netX > 0 and netY < 0:
                            if (val[__].x - val[_].x - val[_].image.width()) / netX <= (
                                    val[__].y + val[__].image.height() - val[_].y) / netY:
                                bottom(val[_], val[__])
                            if (val[__].x - val[_].x - val[_].image.width()) / netX >= (
                                    val[__].y + val[__].image.height() - val[_].y) / netY:
                                left(val[_], val[__])
                        elif netX < 0 and netY > 0:
                            if (val[__].x + val[__].image.width() - val[_].x) / netX <= (
                                    val[__].y - val[_].y - val[_].image.height()) / netY:
                                top(val[_], val[__])
                            if (val[__].x + val[__].image.width() - val[_].x) / netX >= (
                                    val[__].y - val[_].y - val[_].image.height()) / netY:
                                right(val[_], val[__])
                        elif netX < 0 and netY < 0:
                            if (val[__].x + val[__].image.width() - val[_].x) / netX <= (
                                    val[__].y + val[__].image.height() - val[_].y) / netY:
                                bottom(val[_], val[__])
                            if (val[__].x + val[__].image.width() - val[_].x) / netX >= (
                                    val[__].y + val[__].image.height() - val[_].y) / netY:
                                right(val[_], val[__])

    newHash = {}
    for P in Character.instances:
        # Apply changes from the collision function
        P.x = P.newX
        P.y = P.newY
        P.x_ = P.newX_
        P.y_ = P.newY_
        # update the Spacial Hash Table
        for _ in range(int(P.x // 64) - 1, int(P.x + P.image.width()) // 64):
            for __ in range(int(P.y // 64) - 1, int(P.y + P.image.height()) // 64):
                if (_, __) not in newHash:
                    newHash[(_, __)] = list()
                newHash[(_, __)].append(P)
    Character.hashTable = newHash

    # if a collision happened check for more collisions until no more collisions occur
    if collisionFlag:
        checkCollision(dt)


# collision functions
def top(A, B):
    if not A.dynamic:
        B.newY = A.y + A.image.height() + 0.001
        B.newY_ = -A.yElastic * B.yElastic * B.y_
        if Character.controlled == B:
            Character.controlled.y__['gravity'] = 0.002
            keyUnlock('Right')
            keyUnlock('Left')
            if on_Ground(Character.controlled):
                if B.newY_ == 0:
                    Character.fastFall = True
                    Character.doubleJump = True
                    Character.canvas.itemconfig(Character.controlled.imageID, image=Character.controlled.image)
                elif Character.fastFall is False:
                    Character.fastFall = None
    if not B.dynamic:
        A.newY = B.y - A.image.height() - 0.001
        A.newY_ = -A.yElastic * B.yElastic * A.y_
        if Character.controlled == A:
            Character.controlled.y__['gravity'] = 0.002
            keyUnlock('Right')
            keyUnlock('Left')
            if on_Ground(Character.controlled):
                if A.newY_ == 0:
                    Character.fastFall = True
                    Character.doubleJump = True
                    Character.canvas.itemconfig(Character.controlled.imageID, image=Character.controlled.image)
                elif Character.fastFall is False:

                    Character.fastFall = None


def bottom(A, B):
    if not A.dynamic:
        B.newY = A.y - B.image.height() - 0.001
        B.newY_ = -A.yElastic * B.yElastic * B.y_
        if Character.controlled == B:
            Character.controlled.y__['gravity'] = 0.002
            keyUnlock('Right')
            keyUnlock('Left')
            if on_Ground(Character.controlled):
                if B.newY_ == 0:
                    Character.fastFall = True
                    Character.doubleJump = True
                    Character.canvas.itemconfig(Character.controlled.imageID, image=Character.controlled.image)
                elif Character.fastFall is False:
                    Character.fastFall = None
    if not B.dynamic:
        A.newY = B.y + B.image.height() + 0.001
        A.newY_ = -A.yElastic * B.yElastic * A.y_
        if Character.controlled == A:
            Character.controlled.y__['gravity'] = 0.002
            keyUnlock('Right')
            keyUnlock('Left')
            if on_Ground(Character.controlled):
                if A.newY_ == 0:
                    Character.fastFall = True
                    Character.doubleJump = True
                    Character.canvas.itemconfig(Character.controlled.imageID, image=Character.controlled.image)
                elif Character.fastFall is False:
                    Character.fastFall = None


def left(A, B):
    if not A.dynamic:
        B.newX = A.x + A.image.width() + 0.001
        B.newX_ = -A.xElastic * B.xElastic * B.x_
    if not B.dynamic:
        A.newX = B.x - A.image.width() - 0.001
        A.newX_ = -A.xElastic * B.xElastic * A.x_


def right(A, B):
    if not A.dynamic:
        B.newX = A.x - B.image.width() - 0.001
        B.newX_ = -A.xElastic * B.xElastic * B.x_
    if not B.dynamic:
        A.newX = B.x + B.image.width() + 0.001
        A.newX_ = -A.xElastic * B.xElastic * A.x_


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
        if event.keysym == 'Up':
            if Character.fastFall is False:
                Character.fastFall = None
                Character.controlled.y_ = 0
                Character.controlled.x_ = 0
                Character.controlled.y__['gravity'] = 0.002
                keyUnlock('Right')
                keyUnlock('Left')
        if event.keysym == 'Down':
            Character.controlled.yElastic = 0
            if Character.fastFall and not on_Ground(Character.controlled):
                Character.controlled.y_ = 0
                Character.controlled.x_ = 0
                Character.controlled.x__['move'] = 0
                Character.controlled.y__['gravity'] = 0.004
                keyLock('Right')
                keyLock('Left')
                Character.fastFall = False
        if event.keysym == 'space':
            if Character.fastFall is False:
                Character.fastFall = None
                Character.controlled.y__['gravity'] = 0.002
                keyUnlock('Right')
                keyUnlock('Left')
            if on_Ground(Character.controlled):
                Character.controlled.y_ = -0.8

            elif touching_Wall_Right(Character.controlled) and Character.keys['Right'] is True:
                Character.controlled.y_ = -0.75
                Character.controlled.x_ = -0.3
                Character.controlled.x__['move'] = 0
                keyLock('Right')
                keyUnlock('Left')
                Character.delays['wallJump'] = Character.root.after(300, lambda: keyUnlock('Right'))

            elif touching_Wall_Left(Character.controlled) and Character.keys['Left'] is True:
                Character.controlled.y_ = -0.75
                Character.controlled.x_ = 0.3
                Character.controlled.x__['move'] = 0
                keyLock('Left')
                keyUnlock('Right')
                Character.delays['wallJump'] = Character.root.after(300, lambda: keyUnlock('Left'))

            elif Character.doubleJump is True:
                Character.controlled.y_ = -0.8
                Character.doubleJump = False
                Character.canvas.itemconfig(Character.controlled.imageID, image=Character.controlled.image2)


def keyLock(key):
    Character.lockedKeys[key] = True


def keyUnlock(key):
    Character.lockedKeys[key] = False


def key_release(event):
    Character.keys[event.keysym] = False
    if not Character.lockedKeys[event.keysym]:
        if event.keysym == 'Down':
            Character.controlled.yElastic = 0.999
        if event.keysym == 'Left':
            Character.controlled.x__['move'] = 0
        if event.keysym == 'Right':
            Character.controlled.x__['move'] = 0


class Character:
    canvas = None
    root = None
    instances = []
    nextFrame = None
    hashTable = {}
    controlled = None
    keys = {'Left': False, 'Right': False, 'Down': False}
    lockedKeys = {'Left': False, 'Right': False, 'Down': False, 'Up': False, 'space': False}
    doubleJump = False
    fastFall = True
    screenAdjustY = 450

    loopsRunning = []

    xLevelSize = 1024
    yLevelSize = 768
    xScreenPosition = 0
    yScreenPosition = 0

    delays = {'wallJump': None}

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

        self.newX = 0
        self.newY = 0
        self.newX_ = 0
        self.newY_ = 0

        Character.instances.append(self)

    def spawnChar(self, x, y):
        """Draws character and saves them to the hash table"""
        self.x = x
        self.y = y
        self.imageID = Character.canvas.create_image(x, y, anchor='nw', image=self.image)

        # adds to spacial hash
        for _ in range(int(self.x // 64) - 1, int(self.x + self.image.width()) // 64):
            for __ in range(int(self.y // 64) - 1, int(self.y + self.image.height()) // 64):
                if (_, __) not in Character.hashTable:
                    Character.hashTable[(_, __)] = list()
                Character.hashTable[(_, __)].append(self)


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
    Character('BlackFloor.png', dynamic=False).spawnChar(0, height / 2 + 63.01)
    Character('WhiteWall.png', dynamic=False).spawnChar(-64, height / 2 - 1024.01 + 63)
    Character('WhiteWall.png', dynamic=False).spawnChar(width, height / 2 - 1024.01 + 63)
    Character('WhiteFloor.png', dynamic=False).spawnChar(width + 0.1, height / 2 + 63.01)
    You = Character('BlueBoxDot.png')
    You.y__['gravity'] = 0.002
    You.spawnChar(0, -64)

    You = Character(pic='BlueBox.png', pic2='WhiteBox.png')
    You.y__['gravity'] = 0.002
    You.spawnChar(width / 2 - 32, height / 2)
    setLevelSize(width, height)
    gainControl(You)
    physicsLoop()

    PlatformerTextbox.textBox('Hello, Press X to advance the text.', face='GuyFaceBox3.png')
    PlatformerTextbox.textBox('In this game, you are a blue box.',
                              face='GuyFaceBox3.png')
    PlatformerTextbox.textBox('To move, use the left control stick.',
                              face='GuyFaceBox3.png')
    PlatformerTextbox.textBox('To jump, press A.', face='GuyFaceBox3.png')
    PlatformerTextbox.textBox('', face='GuyFaceBox3.png')
    PlatformerTextbox.textBox('Try heading to the left.', face='GuyFaceBox3.png',
                              openFunctions=[lambda: setLevelSize(width + 1000, height)])

    loop = Character.root.after(3000, PlatformerTextbox.runQueue)
    Character.loopsRunning.append(loop)


def tutorial():
    clearWindow()
    You = Character('WhiteWall.png', dynamic=False)
    You.spawnChar(600 + 1000, 460)

    You = Character('WhiteWall.png', dynamic=False)
    You.spawnChar(600 + 1000, 460)

    You = Character('WhiteWall.png', dynamic=False)
    You.spawnChar(300 + 1000, 460)

    You = Character('WhiteFloor.png', dynamic=False)
    You.spawnChar(0 + 1000, 600 + 1000)

    You = Character(pic='BlueBox.png', pic2='WhiteBox.png')
    You.spawnChar(200 + 1000, 200 + 1000)
    gainControl(You)
    You.y__['gravity'] = 0.002
    You.yDrag = 0.0005
    You.xDrag = 0.0015
    You.yElastic = 0.999

    You = Character('WhiteWall.png', dynamic=False)
    You.spawnChar(100 + 1000, 460)

    You = Character('WhiteWall.png', dynamic=False)
    You.spawnChar(0 + 1000, 460)

    setLevelSize(2 * 1024, 10 * 1024)

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
    Character.doubleJump = False
    Character.fastFall = True
    Character.canvas = Canvas(Character.root, width=width, height=height, bg='black')
    PlatformerTextbox.textBox.canvas = Character.canvas
    Character.canvas.focus_set()
    Character.canvas.pack()


if __name__ == '__main__':
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

    Character.canvas.pack()
    mainloop()
