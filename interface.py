from tkinter import Tk, Label, StringVar, Button, Entry, OptionMenu, Spinbox, Toplevel, IntVar, Canvas, Text, END
from tkcalendar import Calendar
from datetime import datetime
from functools import partial
from PIL import ImageTk, Image
import isro
import asyncio
import threading
import sys
import Database


class EntryWindow:
    def __init__(self):
        """The window where people enter values, can be better, could be a frame, but I am not in the mood."""
        self.root = Tk()
        self.root.geometry("880x450")
        self.root.resizable(False, False)
        self.root.title('Time-Lapse')
        self.font = ("Arial", 12)
        self.settings = [None, None, None, None, 24]        # [video-name, start-date, end-date, type, frame-rate]
        self.calendar = None
        self.fields = []
        self.db = Database.Database()
        self.setScreen()

    def setScreen(self):
        labelNames = ["Video Name", "Start Date", "End Date", "Type", "Frame-Rate"]
        for i, label in enumerate(labelNames):
            Label(self.root, text=label, font=self.font).place(x=20, y=20 + 40 * i)

        TYPES = ["L1C_ASIA_MER_BIMG", "L1C_SGP_3D_IR1", "L1C_SGP_DMP", "L1C_SGP_NMP", "L1C_ASIA_MER_RGB", "L1C_SGP_RGB",
                 "L1B_STD_IR1", "L1B_STD_IR2", "L1B_STD_MIR", "L1B_STD_WV", "L1B_STD_VIS", "L1B_STD_SWIR",
                 "L1B_STD_BT_IR1_TEMP"]
        option_value = StringVar(value=TYPES[0])
        self.fields = [Entry(self.root, font=self.font),
                       Button(self.root, text="Get Calendar Date", command=partial(self.get_date, 1, 60),
                              font=self.font),
                       Button(self.root, text="Get Calendar Date", command=partial(self.get_date, 2, 100),
                              font=self.font),
                       OptionMenu(self.root, option_value, *TYPES),
                       Spinbox(self.root, from_=0, to=10000, textvariable=IntVar(value=24), font=self.font)]

        for i, field in enumerate(self.fields):
            field.place(x=120, y=20 + 40 * i)
        self.fields[3] = option_value
        now = datetime.now()
        self.calendar = Calendar(self.root, selectmode='day', year=now.year, month=now.month, day=now.day,
                                 date_pattern='dd-mm-y')
        self.calendar.place(x=20, y=250)
        Button(self.root, text='Preview', font=self.font, command=self.previewThread).place(x=20, y=210)
        Button(self.root, text='Run', font=self.font, command=self.make_vid).place(x=230, y=210)
        Button(self.root, text='Show Data', font=self.font, command=self.showTable).place(x=130, y=210)
        console_out = Text(self.root, state='disabled', height=25, width=63)
        console_out.place(x=360, y=20)
        # redirecting everything into the textbox
        redirect = StdoutRedirect(console_out)
        sys.stdout = redirect
        sys.stderr = redirect

    def get_date(self, index, y):
        var_ = self.calendar.get_date()
        self.settings[index] = var_
        Label(self.root, text=var_, font=self.font).place(x=270, y=y)

    def show_error(self, msg):
        newWindow = Toplevel(self.root)
        newWindow.title("Error")
        Label(newWindow, text=msg).pack()

    def showTable(self):
        for i in self.db.displayData():
            print(i)

    def previewThread(self):
        print("Loading preview images...")
        t1 = threading.Thread(target=self.preview)
        t1.start()

    def preview(self):
        if not self.get_settings():
            self.show_error(msg='You have not entered all the values yet')
            return

        image_list = []
        for i, date_string in enumerate(self.settings[1:3]):
            d = datetime.strptime(date_string, "%d-%m-%Y")
            date = d.strftime("%d%b").upper()
            year = d.strftime("%Y")
            a = asyncio.run(isro.preview(date, year, self.settings[3], i))
            if a:
                img = Image.open(f"{i}.jpg")
                img = img.resize((500, 500))
                img = ImageTk.PhotoImage(img)
                image_list.append(img)

        if not image_list:
            self.show_error(msg="Could not retrieve any images for the given parameters")
            return
        index = 0
        img = image_list[index]
        preview_Window = Toplevel(self.root)
        preview_Window.title(self.settings[3])
        preview_Window.geometry('500x500')
        preview_Window.resizable(False, False)
        canvas = Canvas(preview_Window, width=500, height=500)
        canvas.place(x=0, y=0)
        canvas.create_image(0, 0, image=img, anchor='nw')

        def changeImage():
            nonlocal index, image_list, canvas
            if index < len(image_list) - 1:
                index += 1
            else:
                index = 0
            img = image_list[index]
            canvas.create_image(0, 0, image=img, anchor='nw')

        Button(preview_Window, text='Toggle', command=changeImage).place(x=430, y=450)
        print("Preview Images Loaded!")

    def get_settings(self):
        name = self.fields[0].get()
        if name == '':
            self.settings[0] = datetime.now().strftime('%d-%m-%Y_%H-%M')
        else:
            self.settings[0] = name
        self.settings[3] = self.fields[3].get()
        frame_rate = self.fields[4].get()
        if frame_rate == 0:
            self.show_error(msg='Frame-rate cannot be zero')
        else:
            self.settings[4] = int(frame_rate)
        return all(self.settings)

    def make_vid(self):
        if self.get_settings():
            video = isro.TimeLapse(*self.settings)
            t1 = threading.Thread(target=video.video)
            t1.start()
        else:
            self.show_error(msg='You have not entered all the values yet')


class StdoutRedirect:
    def __init__(self, text_widget):
        self.text_space = text_widget

    def write(self, string):
        self.text_space.configure(state='normal')
        self.text_space.insert(END, string)
        self.text_space.configure(state='disabled')
        self.text_space.see(END)

    def fileno(self):
        return 0

    def close(self):
        pass

    def flush(self):
        pass


if __name__ == '__main__':
    entryWindow = EntryWindow()
    entryWindow.root.mainloop()
