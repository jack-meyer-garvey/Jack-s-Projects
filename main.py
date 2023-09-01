from continuousCollision import *


def startGame(func):
    text = Character.canvas.create_text(width / 2, height / 2, text="Press A to start", fill="white", font="system 18")
    textFlicker(Character.root, Character.canvas, text)
    Character.canvas.bind("<KeyPress-z>", lambda event: openCredit(func))


def textFlicker(root, canvas, text):
    """Switches the color of text from white to black every 0.5 seconds"""
    if canvas.itemcget(text, 'fill') == 'white':
        canvas.itemconfigure(text, fill='black')
    else:
        canvas.itemconfigure(text, fill='white')
    loop = root.after(800, textFlicker, root, canvas, text)
    Character.loopsRunning.append(loop)


def openCredit(func):
    clearWindow()
    Character.canvas.create_text(width / 2, height / 2, text="by Jack Meyer Garvey", fill="white", font="system 32")
    loop = Character.root.after(1200, func)
    Character.loopsRunning.append(loop)


def bottomWell():
    brick = background('GrayBrickBack.png')
    brick.spawn(415, 1067)
    brick = background('WhiteBrickBack.png')
    brick.spawn(475, -133, numDown=6)
    Character('WhiteBrickLeft.png', dynamic=False).spawnChar(595, 0)
    Character('WhiteBrickRight.png', dynamic=False).spawnChar(415, 0)
    Character('ShadedBrickCornerBR.png', dynamic=False).spawnChar(415, 1024)
    Character('ShadedBrickCornerBL.png', dynamic=False).spawnChar(595, 1024)
    Character('WaterFloor.png', dynamic=False).spawnChar(0, 1224)
    You = Character(pic='blueBox.png', pic2='WhiteBox.png')

    You.spawnChar(0, 1224 - 63)
    You.gainControl()

    setLevelSize(1330, 1500)


def testGame():
    background('Clouds1.png', 0).spawn(0, 0)
    background('Clouds2.png', 2).spawn(0, 0)
    background('Clouds3.png', 1).spawn(0, 0)
    Character('WhiteFloor.png', dynamic=False).spawnChar(300, 900 + 300)
    Character('WhiteFloor.png', dynamic=False).spawnChar(760, 500 + 300)
    You = Character('BlueBoxDot.png')
    You.y__['gravity'] = Fraction(0.004)
    You.spawnChar(760, 200 + 300)
    You = Character('BlueBoxDot.png')
    You.y__['gravity'] = Fraction(0.004)
    You.spawnChar(760, 300)
    You = Character('BlueBoxDot.png')
    You.y__['gravity'] = Fraction(0.004)
    You.spawnChar(900, 1060)
    Character('WhiteWall.png', dynamic=False).spawnChar(700, 780 + 300)
    Character('WhiteBrickLeft.png', dynamic=False).spawnChar(2050, 300 + 300)
    PlatformerTextbox.runQueue()

    sign = funcHold('Sign.png')
    sign.queueText("Do you like it?", options=["Yes", "No", " Maybe LOL"])
    sign.spawn(400, 760 + 300)

    You = Character(pic='blueBox.png', pic2='WhiteBox.png')

    You.spawnChar(300, 0)
    You.gainControl()

    setLevelSize(2400, 1500)


width = 1330
height = 845
Character.root = Tk()
PlatformerTextbox.textBox.root = Character.root
Character.root.geometry(f"{width}x{height}")
Character.root.configure(background='black')
Character.root.attributes("-fullscreen", True)
Character.root.title("PlatFormer")
Character.canvas = Canvas(Character.root, width=width, height=height, bg='black')
PlatformerTextbox.textBox.canvas = Character.canvas
Character.canvas.focus_set()

startWorld()
a = world(bottomWell, 'Well')
world.location = a
b = world(testGame, 'Test')
a.link(b, 'r')

startGame(a.run)
Character.start = time()

Character.canvas.pack()
mainloop()
