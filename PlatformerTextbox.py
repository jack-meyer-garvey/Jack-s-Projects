from tkinter import *
import textwrap
import re
import collections


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


def queueText(textSpeed, text, options, condition, face):
    """Queues textbox text"""
    textBox.textQueue.append((textSpeed, text, condition, face))
    textBox.questionQueue.append(options)


def faceBox(xpos, ypos):
    """Draws the small box to the left of the textbox"""
    img = PhotoImage(file="faceBox.png")
    textBox.imageInstances.append(img)
    box = textBox.canvas.create_image((xpos, ypos), image=img)
    textBox.imagesShown['faceBox'] = box


def closeBoxes():
    """closes the images shown due to a textbox opening."""
    textBox.canvas.delete(textBox.face)
    for _ in textBox.imagesShown.keys():
        textBox.canvas.delete(textBox.imagesShown[_])
        textBox.imagesShown[_] = -1
    textBox.canvas.unbind("<KeyPress-x>")
    textBox.canvas.unbind("<KeyPress-z>")
    textBox.imageInstances.clear()
    for _ in textBox.exitFunctions:
        _()
    textBox.exitFunctions.clear()


def makeText(text):
    """Instantly types text in the box"""
    if textBox.textShown['mainText'] is not None:
        textBox.canvas.delete(textBox.textShown['mainText'])

    this = textBox.canvas.create_text(314 + textBox.xScreenPosition, 610 + textBox.yScreenPosition, text=text, fill="white", font="system 18",
                                      anchor=NW)
    textBox.textShown['mainText'] = this


def clearText():
    """Deletes all text being shown and cancels all planned text"""
    for _ in textBox.textShown.keys():
        textBox.canvas.delete(textBox.textShown[_])
        textBox.textShown[_] = None
    for loop in textBox.loopsRunning:
        textBox.root.after_cancel(loop)
    textBox.loopsRunning.clear()


def moveArrow(event, text, options):
    """Keeps track of the options' path while also moving the arrow"""
    # Remember the path
    path = textBox.arrow - textBox.arrow % 10
    textBox.arrow = textBox.arrow % 10
    if event.keysym == 'Up':
        textBox.arrow -= 1
    if event.keysym == 'Down':
        textBox.arrow += 1
    if textBox.arrow < 1:
        textBox.arrow = len(options)
    if textBox.arrow > len(options):
        textBox.arrow = 1
    things = ''
    for _ in range((2 * textBox.arrow) - 2):
        things += '\n'
    # Re-institute path
    textBox.arrow += path
    textBox.canvas.itemconfigure(text, text=things + '>')


def makeOption(options):
    """Makes the option text appear and begins a new option path. Also binds the up and down keys to move the
    arrow """
    if len(options) == 0:
        textBox.arrow = 0
    if len(options) != 0:
        text = ''
        for _ in options:
            text += _ + '\n\n'
        this = textBox.canvas.create_text(750 + textBox.xScreenPosition, 610 + textBox.yScreenPosition, text=text, fill="white", font="system 18",
                                          anchor=NW)
        textBox.textShown['options'] = this
        this = textBox.canvas.create_text(730 + textBox.xScreenPosition, 610 + textBox.yScreenPosition, text='>', fill="white", font="system 18",
                                          anchor=NW)
        textBox.textShown['arrow'] = this

        # Puts the new arrow at position 1 within the path
        textBox.arrow = textBox.arrow * 10 + 1

        textBox.arrowBindings.append(
            textBox.canvas.bind("<KeyPress-Down>", lambda event: moveArrow(event, this, options), '+'))
        textBox.arrowBindings.append(
            textBox.canvas.bind("<KeyPress-Up>", lambda event: moveArrow(event, this, options), '+'))


def nextQueue():
    """clears the textbox and runs the next queued text box. If the queue is empty it closes the boxes. If the
    arrow meets the condition of the next box in the queue, it runs it. Otherwise, it moves on to the next one """
    clearText()
    if len(textBox.arrowBindings) != 0:
        textBox.canvas.unbind("<KeyPress-Down>", textBox.arrowBindings[0])
        textBox.canvas.unbind("<KeyPress-Up>", textBox.arrowBindings[1])
        textBox.arrowBindings.clear()

    if len(textBox.textQueue) != 0:
        thing = textBox.textQueue.popleft()
        textSpeed = thing[0]
        text = thing[1]
        face = thing[3]
        options = textBox.questionQueue.popleft()
        functions = textBox.openFunctions.popleft()[:]
        if textBox.arrow == int(thing[2]) or int(thing[2]) == 0:
            runBox(textSpeed, text, options, face)
            for _ in functions:
                _()

        else:
            nextQueue()
    else:
        closeBoxes()


def skipText(text, options):
    """Skips through the text that is currently being written and binds the z key to move to the next text box"""
    textBox.canvas.unbind("<KeyPress-x>")
    textBox.canvas.unbind("<KeyPress-z>")
    if textBox.textShown['mainText'] is not None:
        clearText()
        makeText(text)
        textBox.canvas.bind("<KeyPress-z>", lambda event: nextQueue())
        makeOption(options)


def runBox(textSpeed, text, options, face):
    """Types out text at a given speed. Also binds the x and z keys to move through text boxes"""
    textBox.canvas.unbind("<KeyPress-x>")
    textBox.canvas.unbind("<KeyPress-z>")
    if textBox.imagesShown['face'] != -1:
        textBox.canvas.delete(textBox.imagesShown['face'])
    if face is not None:
        if textBox.imagesShown['faceBox'] == -1:
            faceBox(148 + textBox.xScreenPosition, 690 + textBox.yScreenPosition)
        img = PhotoImage(file=face)
        textBox.imageInstances.append(img)
        image = textBox.canvas.create_image((148 + textBox.xScreenPosition, 690 + textBox.yScreenPosition), image=img)
        textBox.imagesShown['face'] = image
        textBox.canvas.tag_raise(textBox.imagesShown['faceBox'])
    elif textBox.imagesShown['faceBox'] != -1:
        textBox.canvas.delete(textBox.imagesShown['faceBox'])
        textBox.imagesShown['faceBox'] = -1
    wait = 0
    for _ in range(len(text) + 1):
        wait += int(textSpeed)
        loop = textBox.root.after(wait, makeText, text[:_])
        textBox.loopsRunning.append(loop)

    textBox.canvas.bind("<KeyPress-x>", lambda event: skipText(text, options))

    loop = textBox.root.after(wait, textBox.canvas.bind, "<KeyPress-z>", lambda event: nextQueue())
    textBox.loopsRunning.append(loop)
    loop = textBox.root.after(wait, makeOption, options)
    textBox.loopsRunning.append(loop)


def runQueue():
    img = PhotoImage(file="textBox.png")
    textBox.imageInstances.append(img)
    image = textBox.canvas.create_image((632 + textBox.xScreenPosition, 690 + textBox.yScreenPosition), image=img)
    textBox.imagesShown['textBox'] = image
    nextQueue()


class textBox:
    # saves all the image locations
    imageInstances = []
    # saves the instances
    instances = []
    # keeps track of all the images being shown at once by this class
    imagesShown = {'faceBox': -1, 'textBox': -1, 'face': -1}
    # keeps track of which face is in the facebox
    face = None
    # ordered lists of text boxes to be shown
    textQueue = collections.deque()
    questionQueue = collections.deque()
    # Optional functions that can run whenever a textbox opens. Make sure to define them as lambda functions
    openFunctions = collections.deque()
    # Optional functions that cun run when the textbox view is exited
    exitFunctions = []
    # root and canvas that the text is on
    root = None
    canvas = None
    # used in cleanup functions
    loopsRunning = []
    textShown = {'mainText': None, 'options': None, 'arrow': None}
    # Arrow keeps track of the textbox path.
    arrow = 0
    arrowBindings = []
    # Keeps track of screen position for drawing
    xScreenPosition = 0
    yScreenPosition = 0

    def __init__(self, text, face=None, textSpeed=20, options=[], condition=0, openFunctions=[], exitFunctions=[]):
        textBox.instances.append(self)
        textBox.openFunctions.append(openFunctions)
        for _ in exitFunctions:
            textBox.exitFunctions.append(_)
        sentences = re.split('(?<=[.?!]\")(?=[\s$\"])|(?<=[.?!])(?=[\s$])', text)
        if len(options) != 0:
            maxChar = 30
        else:
            maxChar = 40
        for _ in range(len(sentences)):
            sentences[_] = textwrap.fill(sentences[_], maxChar)
        newText = ''
        for _ in sentences:
            if len(_) != 0:
                newText += '*' + _.strip() + '\n'
        queueText(textSpeed, newText, options, condition, face)

        maxLines = 5
        if newText.count('\n') > maxLines:
            textBox.textQueue.pop()
            textBox.questionQueue.pop()
            groups = newText.split('\n')
            textBox.openFunctions.pop()
            for _ in range(len(groups) // maxLines + 1):
                start = _ * maxLines
                end = maxLines * (_ + 1)
                if _ != (len(groups) // maxLines):
                    queueText(textSpeed, '\n'.join(groups[start:end]), [], condition, face)
                    textBox.openFunctions.append([])
                else:
                    queueText(textSpeed, '\n'.join(groups[start:end]), options, condition, face)
                    textBox.openFunctions.append(openFunctions)
