import httpx
import asyncio
from datetime import datetime, timedelta
import os
import cv2

# -----------------------------------------------------------------------------------------------------------------------
'''
    This is code that will generate a time-lapse of ISRO satellite images by downloading all their available satellite 
    images and stitching them together to form a video.
    
    The images on the MOSDAC website follow a simple time format in their URLs and this code simply generates a URL,
    tries a request.get() on the url and then if it 404s it tries the another URL. I tried my best to get the URLs by 
    simple post requests but I wasn't able to get that to work, so you have to deal with this pile of crap :-)

    To operate this code, specify a start and end date, if you enter a date for when the satellite was not in orbit or if
    it is in the future, the code will run as usual and not give any warnings, but it will take a very long time since 
    every generated url will just 404.
    
    By default it takes blended images that are available on this website:- 
    
    https://mosdac.gov.in/gallery/index.html?=&prod=3DIMG_%2A_L1C_ASIA_MER_BIMG.jpg
    
    If you want to take a video of a any image image type the above website, copy the image adress which is usually 
    in this format: https://mosdac.gov.in/look/3D_IMG/gallery/2021/23MAY/3DIMG_23MAY2021_2300_L1C_ASIA_MER_BIMG.jpg 
    
    Copy the last part after the 4 digit number that denotes time. In this case, L1C_ASIA_MER_BIMG
    and enter this value as the type.

'''
# enter all the variables here

start = '13-05-2021'              # The start date for the video format - 'dd-mm-yyyy'
end = '21-05-2021'                # if you want it to time-lapse till 20, enter 21
type = 'L1C_ASIA_MER_BIMG'        # the desired image type
framerate = 24                    # there will be around 48 images a day, so chose a frame-rate accordingly
VideoName = 'Tauktae'             # the name of the saved video.

# creating the folders
if os.path.isdir(f"Images/{VideoName}"):
    print(f"Images/{VideoName} already exists, the file will be overwritten")
    None
else:
    os.makedirs(f"Images/{VideoName}")

if os.path.isdir('Videos'):
    None
else:
    os.mkdir('Videos')

# Creates a list of dates between the specified dates
start = datetime.strptime(start, '%d-%m-%Y')
end = datetime.strptime(end, '%d-%m-%Y')
dateList = [start + timedelta(days=x) for x in range(0, (end - start).days)]

async def images():
    """
    This is where the image URLs are generated, it returns a list of saved file-names which makes it easy for
    the video creation part of the code.

    For each day, the code starts with 0030 and then tries a get request,then it will increment the time by 30 minutes
    and gets the next image.

    Sometimes the image timings are off by a minute, so it check 0029 and 0059 etc as well. Sometimes images are missing
    completely.
    """
    urls = []
    fileLIST = []  # stores a list of file-names to return
    for d in dateList:   # looping through each day in the date-list created
        time = '0000'
        date = d.strftime('%d%b').upper()
        year = d.strftime('%Y')
        print('Generating Image URLs')
        while int(time) <= 2330:
            # increments the time by 30 minutes
            if time[2:] == '00':
                time = time[:-2] + "30"
            else:
                time = str(int(time[:-2]) + 1) + '00'
            if len(time) == 3:
                time = '0' + time
            url = f"https://mosdac.gov.in/look/3D_IMG/gallery/{year}/{date}/3DIMG_{date}{year}_{time}_{type}.jpg"
            urls.append(url)

            # trying 29 and 59 in case it returns a 404 using a NEWtime variable to keep the first part of this while
            # loop intact and not messing with the time variable
            if time[2:] == '00':
                    NEWtime = str(int(time[:-2]) - 1) + '59'
            else:
                    NEWtime = time[:-2] + "29"
            if len(NEWtime) == 3:
                    NEWtime = '0' + NEWtime
            url = f"https://mosdac.gov.in/look/3D_IMG/gallery/{year}/{date}/3DIMG_{date}{year}_{NEWtime}_{type}.jpg"
            urls.append(url)
            url = f"https://mosdac.gov.in/look/3D_IMG/gallery/{year}/{date}/3DIMG_{date}{year}_{0000}_{type}.jpg"
            urls.append(url)
    print('Finished generating URLs')
    print('Getting Data')
    async with httpx.AsyncClient(timeout=None) as client:
        tasks = (client.get(url) for url in urls)
        reqs = await asyncio.gather(*tasks)
    for i in reqs:
        if i.status_code == 200:
            ImageName = str(i.url).split('/')[-1]
            with open(f"Images/{VideoName}/{ImageName}", 'wb') as file:
                file.write(i.content)
                fileLIST.append(f"Images/{VideoName}/{ImageName}")
    print('Done')
    return fileLIST

def video():
    image_list = []
    image_files = asyncio.run(images())
    for image in image_files:
        img = cv2.imread(image)
        height, width, layers = img.shape
        size = (width, height)
        image_list.append(img)

    out = cv2.VideoWriter(f"Videos/{VideoName}.avi", cv2.VideoWriter_fourcc(*'DIVX'), framerate, size)

    print('Creating Video')
    for i in range(len(image_list)):
        out.write(image_list[i])

    out.release()
    print('DONE!')


if __name__ == '__main__':
    video()
