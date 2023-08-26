from continuousCollision import *


def startGame():
    text = Character.canvas.create_text(width / 2, height / 2, text="Press X to start", fill="white", font="system 18")
    textFlicker(Character.root, Character.canvas, text)
    Character.canvas.bind("<KeyPress-z>", lambda event: openCredit())


def textFlicker(root, canvas, text):
    """Switches the color of text from white to black every 0.5 seconds"""
    if canvas.itemcget(text, 'fill') == 'white':
        canvas.itemconfigure(text, fill='black')
    else:
        canvas.itemconfigure(text, fill='white')
    loop = root.after(800, textFlicker, root, canvas, text)
    Character.loopsRunning.append(loop)


def openCredit():
    clearWindow()
    audio('Ironic')
    Character.canvas.create_text(width / 2, height / 2, text="by Jack Meyer Garvey", fill="white", font="system 32")
    loop = Character.root.after(1200, testGame)
    Character.loopsRunning.append(loop)


def testGame():
    clearWindow()
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
    Character('WhiteWall.png', dynamic=False).spawnChar(2050, 300 + 300)
    PlatformerTextbox.runQueue()

    sign = funcHold('Sign.png')
    sign.queueText("Do you like it?", options=["Yes", "No", " Maybe LOL"])
    sign.spawn(400, 760 + 300)

    You = Character(pic='blueBox.png', pic2='WhiteBox.png')

    You.spawnChar(300, 0)
    You.gainControl()

    setLevelSize(2400, 1500)
    physicsLoop()


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

startGame()
Character.start = time()

Character.canvas.pack()
mainloop()
