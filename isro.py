import httpx
import asyncio
from datetime import datetime, timedelta
import os
from subprocess import run


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
        print("Folders Created!")

    def generateURLS(self):
        # this can be better I think
        urls = []
        mosdacString = "https://mosdac.gov.in/look/3D_IMG/gallery"
        print("Creating URLs")
        for d in self.dateList:  # looping through each day in the date-list created to generate urls
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
        fileIndex = 0
        # Breaking the downloads into chunks for stability and less ram usage
        n = 850
        chunks = [self.urls[i * n: (i + 1) * n] for i in range((len(self.urls) + n - 1) // n)]
        for i, chunk in enumerate(chunks):
            while True:
                try:
                    print(f"Downloading Chunk {i+1}/{len(chunks)}...")
                    async with httpx.AsyncClient(timeout=None) as client:
                        sub_tasks = (client.get(url) for url in chunk)
                        requests = await asyncio.gather(*sub_tasks)

                    requests[:] = [i for i in requests if i.status_code == 200]     # filtering out all failed requests

                    for image in requests:
                        ImageName = f"{self.type_}_{fileIndex}.jpg"
                        with open(f"Images/{self.name}/{ImageName}", "wb") as file:
                            file.write(image.content)
                        fileIndex += 1
                    requests.clear()
                except httpx.ConnectError:      # random error \_(o_o)_/
                    print("ConnectError encountered, trying again...")
                    continue
                break

    def video(self):
        asyncio.run(self.getImages())
        # using ffmpeg instead of OpenCV because OpenCV videos are too big,
        # and they take up far too much ram and its too slow
        print('Generating Video...')
        args = ['ffmpeg', '-loglevel', 'quiet','-stats', '-framerate', str(self.frame_rate), '-i', f'./Images/{self.name}/{self.type_}_%d.jpg', '-vf',
                'pad=ceil(iw/2)*2:ceil(ih/2)*2', '-vcodec', 'libx264', '-y', '-an', f'./Videos/{self.name}.mp4']
        run(args=args)
        print("DONE!")


async def preview(date, year, time, type_, file_name):
    """To get the preview images when the preview button is clicked.
    Copy pasted from https://github.com/clodman84/AternosReborn/blob/master/space.py"""
    count = 0
    urls = []
    mosdacString = "https://mosdac.gov.in/look/3D_IMG/gallery"
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
            url = (
                f"{mosdacString}/{year}/{date}/3DIMG_{date}{year}_{NEWtime}_{type_}.jpg"
            )
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
