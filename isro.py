import httpx
import asyncio
from datetime import datetime, timedelta
import os
import cv2


class TimeLapse:
    def __init__(self, name, start_date, end_date, type_, frame_rate=24):
        """Works by creating a list of urls with the given parameters of date and type amd then fetches them to
        stitch together into a video."""
        self.name = name
        self.type_ = type_
        self.frame_rate = frame_rate
        start = datetime.strptime(start_date, "%d-%m-%Y")
        end = datetime.strptime(end_date, "%d-%m-%Y")
        self.dateList = [
            start + timedelta(days=x) for x in range(0, (end - start).days)
        ]
        self.urls = self.generateURLS()
        self.createDir()

    # creating the folders
    def createDir(self):
        if os.path.isdir(f"Images/{self.name}"):
            print(f"Images/{self.name} already exists, the file will be overwritten")
        else:
            os.makedirs(f"Images/{self.name}")

        if os.path.isdir("Videos"):
            pass
        else:
            os.mkdir("Videos")
        print('Folders Created!')

    def generateURLS(self):
        # this can be better I think
        urls = []
        mosdacString = "https://mosdac.gov.in/look/3D_IMG/gallery"
        print("Creating URLs")
        for d in self.dateList:  # looping through each day in the date-list created to generate urls
            print(d)
            time = "0000"
            date = d.strftime("%d%b").upper()
            year = d.strftime("%Y")
            while int(time) <= 2330:
                # increments the time by 30 minutes
                if time[2:] == "00":
                    time = time[:-2] + "30"
                else:
                    time = str(int(time[:-2]) + 1) + "00"
                if len(time) == 3:
                    time = "0" + time
                url = f"{mosdacString}/{year}/{date}/3DIMG_{date}{year}_{time}_{self.type_}.jpg"
                urls.append(url)
                # trying 29 and 59 in case it returns a 404 using a NEWtime variable to keep the first part of this
                # while loop intact and not messing with the time variable
                if time[2:] == "00":
                    NEWtime = str(int(time[:-2]) - 1) + "59"
                else:
                    NEWtime = time[:-2] + "29"
                if len(NEWtime) == 3:
                    NEWtime = "0" + NEWtime
                url = f"{mosdacString}/{year}/{date}/3DIMG_{date}{year}_{NEWtime}_{self.type_}.jpg"
                urls.append(url)
                url = f"{mosdacString}/{year}/{date}/3DIMG_{date}{year}_{0000}_{self.type_}.jpg"
                urls.append(url)
        return urls

    async def getImages(self):
        fileLIST = []
        async with httpx.AsyncClient(timeout=None) as client:
            tasks = (client.get(url) for url in self.urls)
            reqs = await asyncio.gather(*tasks)

        for i in reqs:
            if i.status_code == 200:
                ImageName = str(i.url).split("/")[-1]
                with open(f"Images/{self.name}/{ImageName}", "wb") as file:
                    file.write(i.content)
                    fileLIST.append(f"Images/{self.name}/{ImageName}")
        return fileLIST

    def video(self):
        image_list = []
        image_files = asyncio.run(self.getImages())

        for image in image_files:
            img = cv2.imread(image)
            image_list.append(img)
        height, width = image_list[0].shape[0:2]
        size = (width, height)
        out = cv2.VideoWriter(
            f"Videos/{self.name}.avi",
            cv2.VideoWriter_fourcc(*"DIVX"),
            self.frame_rate,
            size,
        )

        print("Creating Video")
        for image in image_list:
            out.write(image)
        out.release()
        del out
        del image_files
        print("DONE!")


async def preview(date, year, time, type_, file_name):
    """To get the preview images when the preview button is clicked.
    Copy pasted from https://github.com/clodman84/AternosReborn/blob/master/space.py"""
    count = 0
    urls = []
    mosdacString = 'https://mosdac.gov.in/look/3D_IMG/gallery'
    if int(time[2:]) >= 30:
        time = str(int(time[0:2]) + 1) + "00"
        if len(time) == 3:
            time = "0" + time
    else:
        time = time[0:2] + "30"
    while int(time) > 0 and count <= 10:
        count += 1
        if time[2:] == "00":
            time = str(int(time[:-2]) - 1) + "30"
        else:
            time = time[:-2] + "00"
        if len(time) == 3:
            time = "0" + time
        url = f"{mosdacString}/{year}/{date}/3DIMG_{date}{year}_{time}_{type_}.jpg"
        urls.append(url)
        # trying 29 and 59
        if time[2:] == "00":
            NEWtime = str(int(time[:-2]) - 1) + "59"
        else:
            NEWtime = time[:-2] + "29"
        if len(NEWtime) == 3:
            NEWtime = "0" + NEWtime
            url = f"{mosdacString}/{year}/{date}/3DIMG_{date}{year}_{NEWtime}_{type_}.jpg"
            urls.append(url)

    async with httpx.AsyncClient(timeout=None) as client:
        tasks = (client.get(url) for url in urls)
        reqs = await asyncio.gather(*tasks)

    for i in reqs:
        if i.status_code == 200:
            with open(f"{file_name}.jpg", "wb") as file:
                file.write(i.content)
            return True

    return False
