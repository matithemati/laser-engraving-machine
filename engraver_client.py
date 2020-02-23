from PIL import Image, ImageTk
from tkinter import ttk, filedialog, Label, Entry, END, messagebox
import tkinter as tk
import socket
import time

class Engraver():
    # Opens the socket connection
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.soc.connect((host, port))

    # Destructor
    def __del__(self):
        self.soc.close()

    # Sends a message
    def _send_message(self, message):
        packet = "\x5f\x5f\x5e\x5f\x5f"
        packet += str(chr(len(message)))
        packet += message

        self.soc.sendto(packet.encode(), (self.host, self.port))

    # Reads a message
    def _read_message(self):
        message = ""
        packet_pattern = "\x5f\x5f\x5e\x5f\x5f"

        while True:
            message += self.soc.recv(1).decode()

            if len(message) <= 5:
                continue

            if packet_pattern in message:
                while True:
                    try:
                        packet_length = bytearray(message[message.index(packet_pattern) + len(packet_pattern)].encode())[0]
                        break
                    except IndexError:
                        message += self.soc.recv(1).decode()
                        continue

                for x in range(packet_length):
                    message += self.soc.recv(1).decode()

                return message[message.index(packet_pattern) + len(packet_pattern) + 1:]

    # Closes a connection
    def close(self):
        self._send_message("close")

        message = self._read_message()

        if message == 'close':
            self.soc.close()

            return True

    # Make one pixel
    def pixel(self, dir, count, laser, dur, gap):
        data = "y"

        if dir == True:
            data += '+'
        elif dir == False:
            data += '-'

        data += str(gap)

        for i in range(count):
            if laser == True:
                self._send_message("laser=on")

                if (self._read_message() != "laser=on"):
                    return False

                time.sleep(dur)

                self._send_message("laser=off")

                if (self._read_message() != "laser=off"):
                    return False

            self._send_message(data)
            answ = self._read_message()

            if (answ == "cali"):
                guiError("Kalibracja jest wymagana!")

                self._send_message("lcd=clear")

                if (self._read_message() != "lcd=clear"):
                    return False

                self._send_message("lcd1=Kalibracja")

                if (self._read_message() != "lcd1=Kalibracja"):
                    return False

                self._send_message("lcd2= jest wymagana!")

                if (self._read_message() != "lcd2= jest wymagana!"):
                    return False

                return False
            elif (answ != data):
                guiError("Błąd wewnętrzny!")
                return False

        return True

    def stop(self):
        self._send_message("laser=off")

        if (self._read_message() != "laser=off"):
            return False

        self.close()

# engraver = Engraver('192.168.0.1', 29000)
#
# engraver._send_message("buzzers=2")
# engraver._read_message()
#
# engraver.close()
# del engraver

root = tk.Tk()
root.title("Laser Engraving Machine")

style = ttk.Style()
style.theme_use('classic')

nb = ttk.Notebook(root, width=800, height=500)

def guiInfo(text):
    messagebox.showinfo("Information", text)

def guiError(text):
    messagebox.showerror("Error", text)

# Engraver Tab
engraverTab = ttk.Frame(nb)
nb.add(engraverTab, text='Graweruj')

updateLabelAlgorithm = Label(engraverTab, text="Algorytm konwersji obrazka", width=20, bd=3)
updateLabelAlgorithm.place(relx=0.04, rely=0.23)

updateEntryAlgorithm = Entry(engraverTab, width=20, bd=0, justify='center')
updateEntryAlgorithm.insert(END, "180")
updateEntryAlgorithm.place(relx=0.04, rely=0.3)

updateLabelWidth = Label(engraverTab, text="Szerokość obrazka", width=14, bd=3)
updateLabelWidth.place(relx=0.3, rely=0.23)

updateEntryWidth = Entry(engraverTab, width=14, bd=0, justify='center')
updateEntryWidth.insert(END, "32")
updateEntryWidth.place(relx=0.3, rely=0.3)

updateLabelHeight = Label(engraverTab, text="Wysokość obrazka", width=14, bd=3)
updateLabelHeight.place(relx=0.5, rely=0.23)

updateEntryHeight = Entry(engraverTab, width=14, bd=0, justify='center')
updateEntryHeight.insert(END, "32")
updateEntryHeight.place(relx=0.5, rely=0.3)

updateLabelUploadedFile = Label(engraverTab, text="Załadowany obrazek: brak", width=81, bd=3)
updateLabelUploadedFile.place(relx=0.04, rely=0.1)

uploadedFilePath = None

def uploadFile():
    global uploadedFilePath
    uploadedFilePath = filedialog.askopenfilename()

    updateLabelUploadedFile.config(text="Załadowany obrazek: "+uploadedFilePath)

uploadButton = tk.Button(engraverTab, text="Wczytaj obrazek", command=uploadFile)
uploadButton.place(relx=0.04, rely=0.05)

def blackFile():
    blackFilePath = uploadedFilePath[:uploadedFilePath.rfind('/')+1]
    blackFilePath += uploadedFilePath[uploadedFilePath.rfind('/')+1:uploadedFilePath.rfind('.')]
    blackFilePath += "_bw"
    blackFilePath += uploadedFilePath[uploadedFilePath.rfind('.'):]

    col = Image.open(uploadedFilePath)

    gray = col.convert('L')
    bw = gray.point(lambda x: 255 if x < 128 else 0, '1')

    bw.save(blackFilePath)

blackButton = tk.Button(engraverTab, text="Stwórz czarno-biały obrazek", command=blackFile)
blackButton.place(relx=0.04, rely=0.42)

newFilePath = None

def convertFile():
    global newFilePath
    newFilePath = uploadedFilePath[:uploadedFilePath.rfind('/')+1]
    newFilePath += uploadedFilePath[uploadedFilePath.rfind('/')+1:uploadedFilePath.rfind('.')]
    newFilePath += "_engraver"
    newFilePath += uploadedFilePath[uploadedFilePath.rfind('.'):]

    img = Image.open(uploadedFilePath)
    pixels = img.load()

    # print(img.mode)

    # for i in range(img.size[0]):
    #     for j in range(img.size[1]):
    #         print(pixels[i, j])

    # GRAYSCALE IMG
    if ((img.mode == 'LA') and (len(pixels[0, 0]) == 2)):
        for i in range(img.size[0]):
            for j in range(img.size[1]):
                if pixels[i, j] != (0, 255):
                    pixels[i, j] = (0, 0)

        img = img.resize((int(updateEntryWidth.get()), int(updateEntryHeight.get())), Image.ANTIALIAS)
        pixels = img.load()

        for i in range(img.size[0]):
            for j in range(img.size[1]):
                if pixels[i, j][1] < int(updateEntryAlgorithm.get()):
                    pixels[i, j] = (0, 0)
                else:
                    pixels[i, j] = (0, 255)

    # RGB IMG
    elif ((img.mode == 'RGB') and (len(pixels[0, 0]) == 3)):
        for i in range(img.size[0]):
            for j in range(img.size[1]):
                if pixels[i, j] != (0, 0, 0):
                    pixels[i, j] = (255, 255, 255)

        img = img.resize((int(updateEntryWidth.get()), int(updateEntryHeight.get())), Image.ANTIALIAS)
        pixels = img.load()

        for i in range(img.size[0]):
            for j in range(img.size[1]):
                if pixels[i, j][1] < int(updateEntryAlgorithm.get()):
                    pixels[i, j] = (0, 0, 0)
                else:
                    pixels[i, j] = (255, 255, 255)

    # RGBA IMG
    elif ((img.mode == 'RGBA') and (len(pixels[0, 0]) == 4)):
        for i in range(img.size[0]):
            for j in range(img.size[1]):
                if pixels[i, j] != (0, 0, 0, 255):
                    pixels[i, j] = (255, 255, 255, 255)

        img = img.resize((int(updateEntryWidth.get()), int(updateEntryHeight.get())), Image.ANTIALIAS)
        pixels = img.load()

        for i in range(img.size[0]):
            for j in range(img.size[1]):
                if pixels[i, j][1] < int(updateEntryAlgorithm.get()):
                    pixels[i, j] = (0, 0, 0, 255)
                else:
                    pixels[i, j] = (255, 255, 255, 255)

    img.save(newFilePath)

convertButton = tk.Button(engraverTab, text="Konwertuj załadowany obrazek", command=convertFile)
convertButton.place(relx=0.04, rely=0.63)

laserDur = 7
xGap = 100
yGap = 200

def engraveFile():
    img = Image.open(newFilePath)

    engraverImage = list(img.getdata())
    width, height = img.size
    engraverImage = [engraverImage[i * width:(i + 1) * width] for i in range(height)]

    for i in range(len(engraverImage)):
        for j in range(len(engraverImage[i])):
            engraverImage[i][j] = engraverImage[i][j][1]

    engraver = Engraver('192.168.0.1', 29000)

    # Get the beginning position of laser
    engraver._send_message("x")
    startX = int((engraver._read_message()).partition('=')[2])

    engraver._send_message("y")
    startY = int((engraver._read_message()).partition('=')[2])

    # Play sound at the beginning of engraving
    engraver._send_message("buzzers=0.8")

    if (engraver._read_message() != "buzzers=0.8"):
        return False

    # Clear LCD and set "Engraving..." information
    engraver._send_message("lcd=clear")

    if (engraver._read_message() != "lcd=clear"):
        return False

    engraver._send_message("lcd1=Grawerowanie...")

    if (engraver._read_message() != "lcd1=Grawerowanie..."):
        return False

    if (img.mode == 'LA'):
        blackPixelDef = 255
    else:
        blackPixelDef = 0

    allPixels = len(engraverImage) * (len(engraverImage[0]) * 2)

    for height in range(len(engraverImage)):
        countPixel = 1

        for pixel in engraverImage[height]:
            if pixel == blackPixelDef:
                if not engraver.pixel(True, 1, True, laserDur, yGap):
                    engraver.stop()
                    return False
            else:
                if not engraver.pixel(True, 1, False, laserDur, yGap):
                    engraver.stop()
                    return False

            actualPercent = int((height * (len(engraverImage[0]) * 2) + countPixel) / allPixels * 100)
            countPixel += 1

            engraver._send_message("lcd2=        " + str(actualPercent) + "%")

            if (engraver._read_message() != ("lcd2=        " + str(actualPercent) + "%")):
                return False

        engraver._send_message("x+"+str(xGap))
        answ = engraver._read_message()

        if answ == "cali":
            guiError("Kalibracja jest wymagana!")

            engraver._send_message("lcd=clear")

            if (engraver._read_message() != "lcd=clear"):
                return False

            engraver._send_message("lcd1=Kalibracja")

            if (engraver._read_message() != "lcd1=Kalibracja"):
                return False

            engraver._send_message("lcd2= jest wymagana!")

            if (engraver._read_message() != "lcd2= jest wymagana!"):
                return False

            engraver.stop()
            return False
        elif answ != ("x+"+str(xGap)):
            engraver.stop()
            return False

        engraver._send_message("y-"+str(yGap))
        answ = engraver._read_message()

        if answ == "cali":
            guiError("Kalibracja jest wymagana!")

            engraver._send_message("lcd=clear")

            if (engraver._read_message() != "lcd=clear"):
                return False

            engraver._send_message("lcd1=Kalibracja")

            if (engraver._read_message() != "lcd1=Kalibracja"):
                return False

            engraver._send_message("lcd2= jest wymagana!")

            if (engraver._read_message() != "lcd2= jest wymagana!"):
                return False

            engraver.stop()
            return False
        elif answ != ("y-"+str(yGap)):
            engraver.stop()
            return False

        engraverImage[height].reverse()

        countPixel = 1

        for pixel in engraverImage[height]:
            if pixel == blackPixelDef:
                if not engraver.pixel(False, 1, True, laserDur, yGap):
                    engraver.stop()
                    return False
            else:
                if not engraver.pixel(False, 1, False, laserDur, yGap):
                    engraver.stop()
                    return False

            actualPercent = int((height * (len(engraverImage[0]) * 2) + len(engraverImage[0]) + countPixel) / allPixels * 100)
            countPixel += 1

            engraver._send_message("lcd2=        " + str(actualPercent) + "%")

            if (engraver._read_message() != ("lcd2=        " + str(actualPercent) + "%")):
                return False

        engraver._send_message("x+"+str(xGap))
        answ = engraver._read_message()

        if answ == "cali":
            guiError("Kalibracja jest wymagana!")

            engraver._send_message("lcd=clear")

            if (engraver._read_message() != "lcd=clear"):
                return False

            engraver._send_message("lcd1=Kalibracja")

            if (engraver._read_message() != "lcd1=Kalibracja"):
                return False

            engraver._send_message("lcd2= jest wymagana!")

            if (engraver._read_message() != "lcd2= jest wymagana!"):
                return False

            engraver.stop()
            return False
        elif answ != ("x+"+str(xGap)):
            engraver.stop()
            return False

        engraver._send_message("y+"+str(yGap))
        answ = engraver._read_message()

        if answ == "cali":
            guiError("Kalibracja jest wymagana!")

            engraver._send_message("lcd=clear")

            if (engraver._read_message() != "lcd=clear"):
                return False

            engraver._send_message("lcd1=Kalibracja")

            if (engraver._read_message() != "lcd1=Kalibracja"):
                return False

            engraver._send_message("lcd2= jest wymagana!")

            if (engraver._read_message() != "lcd2= jest wymagana!"):
                return False

            engraver.stop()
            return False
        elif answ != ("y+"+str(yGap)):
            engraver.stop()
            return False

    # Clear LCD and set "Returning" information
    engraver._send_message("lcd=clear")

    if (engraver._read_message() != "lcd=clear"):
        return False

    engraver._send_message("lcd1=Wracanie...")

    if (engraver._read_message() != "lcd1=Wracanie..."):
        return False

    # Get X position and return to 0
    engraver._send_message("x")
    answ = int((engraver._read_message()).partition('=')[2])

    if answ != startX:
        if answ > startX:
            data = "x-" + str(answ-startX)
        else:
            data = "x+" + str(abs(answ)+startX)

        engraver._send_message(data)

        if (engraver._read_message() != data):
            return False

    # Get Y position and return to 0
    engraver._send_message("y")
    answ = int((engraver._read_message()).partition('=')[2])

    if answ != startY:
        if answ > startY:
            data = "y-" + str(answ-startY)
        else:
            data = "y+" + str(abs(answ)+startY)

        engraver._send_message(data)

        if (engraver._read_message() != data):
            return False

    # Clear LCD and set "Ready" information
    engraver._send_message("lcd=clear")

    if (engraver._read_message() != "lcd=clear"):
        return False

    engraver._send_message("lcd1=Gotowy")

    if (engraver._read_message() != "lcd1=Gotowy"):
        return False

    # Play sound at the end of engraving
    engraver._send_message("buzzers=0.3")

    if (engraver._read_message() != "buzzers=0.3"):
        return False

    time.sleep(0.5)

    engraver._send_message("buzzers=0.3")

    if (engraver._read_message() != "buzzers=0.3"):
        return False

    time.sleep(0.5)

    engraver._send_message("buzzers=0.6")

    if (engraver._read_message() != "buzzers=0.6"):
        return False

    engraver.close()
    del engraver

    guiInfo("Obrazek został pomyślnie wygrawerowany!")

engraveButton = tk.Button(engraverTab, text="Graweruj załadowany obrazek", command=engraveFile)
engraveButton.place(relx=0.04, rely=0.72)

# Configuration Tab
configTab = ttk.Frame(nb)
nb.add(configTab, text='Konfiguracja')

laserLabel = Label(configTab, text="Czas grawerowania laserem [sek]", width=30, bd=3)
laserLabel.place(relx=0.1, rely=0.13)

laserEntry = Entry(configTab, width=30, bd=0, justify='center')
laserEntry.insert(END, str(laserDur))
laserEntry.place(relx=0.1, rely=0.2)

xGapLabel = Label(configTab, text="Poziomy odstęp pikseli [kroki]", width=30, bd=3)
xGapLabel.place(relx=0.1, rely=0.3)

xGapEntry = Entry(configTab, width=30, bd=0, justify='center')
xGapEntry.insert(END, str(xGap))
xGapEntry.place(relx=0.1, rely=0.37)

yGapLabel = Label(configTab, text="Pionowy odstęp pikseli [kroki]", width=30, bd=3)
yGapLabel.place(relx=0.1, rely=0.47)

yGapEntry = Entry(configTab, width=30, bd=0, justify='center')
yGapEntry.insert(END, str(yGap))
yGapEntry.place(relx=0.1, rely=0.54)

def loadDefault():
    global laserDur
    laserDur = 7
    laserEntry.delete(0, END)
    laserEntry.insert(END, "7")

    global xGap
    xGap = 100
    xGapEntry.delete(0, END)
    xGapEntry.insert(END, "100")

    global yGap
    yGap = 200
    yGapEntry.delete(0, END)
    yGapEntry.insert(END, "200")

defaultButton = tk.Button(configTab, text="Wczytaj domyślne ustawienia", command=loadDefault)
defaultButton.place(relx=0.1, rely=0.8)

def saveSettings():
    global laserDur
    laserDur = int(laserEntry.get())

    global xGap
    xGap = int(xGapEntry.get())

    global yGap
    yGap = int(yGapEntry.get())

saveButton = tk.Button(configTab, text="Zapisz ustawienia", command=saveSettings)
saveButton.place(relx=0.38, rely=0.8)

# Calibration Tab
caliTab = ttk.Frame(nb)
nb.add(caliTab, text='Kalibracja')

moveXLabel = Label(caliTab, text="Przesuń w osi X [kroki]", width=17, bd=3)
moveXLabel.place(relx=0.1, rely=0.23)

moveXEntry = Entry(caliTab, width=17, bd=0, justify='center')
moveXEntry.insert(END, 0)
moveXEntry.place(relx=0.1, rely=0.3)

moveYLabel = Label(caliTab, text="Przesuń w osi Y [kroki]", width=17, bd=3)
moveYLabel.place(relx=0.32, rely=0.23)

moveYEntry = Entry(caliTab, width=17, bd=0, justify='center')
moveYEntry.insert(END, 0)
moveYEntry.place(relx=0.32, rely=0.3)

moveZLabel = Label(caliTab, text="Przesuń w osi Z [kroki]", width=17, bd=3)
moveZLabel.place(relx=0.54, rely=0.23)

moveZEntry = Entry(caliTab, width=17, bd=0, justify='center')
moveZEntry.insert(END, 0)
moveZEntry.place(relx=0.54, rely=0.3)

def moveCNC():
    engraver = Engraver('192.168.0.1', 29000)

    engraver._send_message("cali=on")

    if (engraver._read_message() != "cali=on"):
        return False

    engraver._send_message("buzzers=0.5")

    if (engraver._read_message() != "buzzers=0.5"):
        return False

    engraver._send_message("lcd=clear")

    if (engraver._read_message() != "lcd=clear"):
        return False

    engraver._send_message("lcd1=Gotowy")

    if (engraver._read_message() != "lcd1=Gotowy"):
        return False

    zSteps = int(moveZEntry.get())

    if zSteps != 0:
        data = 'z'
        data += '+' if zSteps > 0 else '-'
        data += str(abs(zSteps))

        engraver._send_message(data)

        if (engraver._read_message() != data):
            guiError("Błąd wewnętrzny!")
            return False

    xSteps = int(moveXEntry.get())

    if xSteps != 0:
        data = 'x'
        data += '+' if xSteps > 0 else '-'
        data += str(abs(xSteps))

        engraver._send_message(data)

        if (engraver._read_message() != data):
            guiError("Błąd wewnętrzny!")
            return False

    ySteps = int(moveYEntry.get())

    if ySteps != 0:
        data = 'y'
        data += '+' if ySteps > 0 else '-'
        data += str(abs(ySteps))

        engraver._send_message(data)

        if (engraver._read_message() != data):
            guiError("Błąd wewnętrzny!")
            return False

    engraver._send_message("cali=off")

    if (engraver._read_message() != "cali=off"):
        return False

    engraver.close()
    del engraver

moveCNCButton = tk.Button(caliTab, text="Wykonaj powyższy ruch", command=moveCNC)
moveCNCButton.place(relx=0.1, rely=0.7)

nb.pack(expand=1, fill="both")

root.mainloop()