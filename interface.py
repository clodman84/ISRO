from tkinter import *
from tkcalendar import Calendar
import datetime
from functools import partial
import isro


class EntryWindow:
    def __init__(self):
        self.root = Tk()
        self.root.geometry("380x450")
        self.root.resizable(False, False)
        self.root.title('Time-Lapse')
        self.font = ("Arial", 12)
        self.settings = [None, None, None, None, 24]
        self.calendar = None
        self.fields = []
        self.setScreen()

    def setScreen(self):
        labelNames = ["Video Name", "Start Date", "End Date", "Type", "Frame-Rate"]
        for i, label in enumerate(labelNames):
            Label(self.root, text=label, font=self.font).place(x=20, y=20 + 40 * i)

        TYPES = ["L1C_ASIA_MER_BIMG", "ISRO_BIMG", "ISRO_BRUH", "ISRO_NOOOOO"]
        option_value = StringVar(value=TYPES[0])
        self.fields = [Entry(self.root, font=self.font),
                       Button(self.root, text="Get Calendar Date", command=partial(self.get_date, 1, 60),
                              font=self.font),
                       Button(self.root, text="Get Calendar Date", command=partial(self.get_date, 2, 100),
                              font=self.font),
                       OptionMenu(self.root, option_value, *TYPES),
                       Spinbox(self.root, from_=0, to=10000, textvariable=DoubleVar(value=24), font=self.font)]

        for i, field in enumerate(self.fields):
            field.place(x=120, y=20 + 40 * i)
        self.fields[3] = option_value
        now = datetime.datetime.now()
        self.calendar = Calendar(self.root, selectmode='day', year=now.year, month=now.month, day=now.day,
                                 date_pattern='dd-mm-y')
        self.calendar.place(x=20, y=250)
        Button(self.root, text='Preview', font=self.font).place(x=20, y=210)
        Button(self.root, text='Run', font=self.font, command=self.make_vid).place(x=230, y=210)

    def get_date(self, index, y):
        var_ = self.calendar.get_date()
        self.settings[index] = var_
        Label(self.root, text=var_, font=self.font).place(x=270, y=y)
        print(self.settings)

    def show_error(self, msg):
        newWindow = Toplevel(self.root)
        newWindow.title("Error")
        Label(newWindow,
              text=msg).pack()

    def get_settings(self):
        name = self.fields[0].get()
        print(name)
        if name is None:
            self.settings[0] = str(datetime.datetime.now())
        else:
            self.settings[0] = name
        self.settings[3] = self.fields[3].get()
        frame_rate = self.fields[4].get()
        if frame_rate == 0:
            self.show_error(msg='Frame-rate cannot be zero')
            pass
        else:
            self.settings[4] = int(frame_rate)
        return all(self.settings)

    def make_vid(self):
        if self.get_settings():
            video = isro.TimeLapse(*self.settings)
            video.video()
        else:
            self.show_error(msg='You have not entered all the values yet')


if __name__ == '__main__':
    entryWindow = EntryWindow()
    entryWindow.root.mainloop()
