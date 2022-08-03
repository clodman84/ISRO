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
        self.dateList = [start + timedelta(days=x) for x in range((end - start).days)]
        self.urls = self.generateURLS()
        self.createDir()
        self.fileIndex = 0  # made this a class variable for the database thing

    # creating the folders
    def createDir(self):
        if os.path.isdir(f"Images/{self.name}"):
            print(f"Images/{self.name} already exists, the file will be overwritten")
        else:
            os.makedirs(f"Images/{self.name}")

        if not os.path.isdir("Videos"):
            os.mkdir("Videos")
        print("Folders Created!")

    def generateURLS(self):
        # this can be better I think
        minutes = ("00", "59", "30", "29")   # the satellite takes images in a 30 minute time-offset
        urls = []
        mosdacString = "https://mosdac.gov.in/look/3D_IMG/preview"
        print("Creating URLs")
        for d in self.dateList:  # looping through each day in the date-list created to generate urls

            date = d.strftime("%d%b").upper()
            year = d.strftime("%Y")
            for hour in range(23):
                # increments the time by 30 minutes
                hour = f"0{str(hour)}" if hour < 10 else str(hour)
                for minute in minutes:
                    time = hour + minute
                    url = f"{mosdacString}/{year}/{date}/3DIMG_{date}{year}_{time}_{self.type_}.jpg"
                    urls.append(url)
        return urls

    async def getImages(self):
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
                        ImageName = f"{self.type_}_{self.fileIndex}.jpg"
                        with open(f"Images/{self.name}/{ImageName}", "wb") as file:
                            file.write(image.content)
                        self.fileIndex += 1

                except httpx.ConnectError:      # random error \_(o_o)_/
                    print("ConnectError encountered, trying again...")
                    continue
                break

    def video(self):
        asyncio.run(self.getImages())
        # using ffmpeg instead of OpenCV because OpenCV videos are too big,
        # and they take up far too much ram and its too slow
        print('Generating Video...')
        args = ['ffmpeg', '-loglevel', 'quiet', '-stats', '-framerate', str(self.frame_rate), '-i',
                f'./Images/{self.name}/{self.type_}_%d.jpg', '-vf', 'pad=ceil(iw/2)*2:ceil(ih/2)*2', '-vcodec',
                'libx264', '-y', '-an', f'./Videos/{self.name}.mp4']
        run(args=args)
        print("DONE!")


async def preview(date, year, type_, file_name):
    """To get the preview images when the preview button is clicked.
    Copy pasted from https://github.com/clodman84/AternosReborn/blob/master/space.py"""

    minutes = ("00", "59", "30", "29")  # the satellite takes images in a 30 minute time-offset
    urls = []
    mosdacString = "https://mosdac.gov.in/look/3D_IMG/preview"

    for hour in range(4):
        # increments the time by 30 minutes
        hour = f"0{str(hour)}" if hour < 10 else str(hour)
        for minute in minutes:
            time = hour + minute
            url = f"{mosdacString}/{year}/{date}/3DIMG_{date}{year}_{time}_{type_}.jpg"
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
