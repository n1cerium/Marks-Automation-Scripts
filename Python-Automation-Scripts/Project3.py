from datetime import datetime
import argparse
import pymongo
import shlex
import subprocess
import math
import xlsxwriter

FPS = 60
RangesList = []


def convertTime(NumberOfSeconds, TotalSeconds): #Number of seconds = from frame, total seconds = the number of seconds of a day, hour or minute
    TimeConverted = math.trunc(NumberOfSeconds / TotalSeconds)
    RemainingSeconds = NumberOfSeconds % TotalSeconds

    return (TimeConverted, RemainingSeconds)

def GetTimeCode(ConvertedTime, CurrTimeCode):
    Value = ConvertedTime[0]

    return CurrTimeCode + str(Value).zfill(2) + ":"

def FrameToTimeCode(frame):
    FramesInSeconds = math.trunc(frame / FPS)
    RemainingFrames = frame % FPS

    ConvertedTime = convertTime(FramesInSeconds, 3600)
    TimeCode = GetTimeCode(ConvertedTime, "")

    ConvertedTime = convertTime(ConvertedTime[1], 60)
    TimeCode = GetTimeCode(ConvertedTime, TimeCode)

    RemainingSeconds = ConvertedTime[1]
    TimeCode = TimeCode + str(RemainingSeconds).zfill(2) + "." + str(RemainingFrames).zfill(2)

    return TimeCode



parser = argparse.ArgumentParser(description="Project 3")
parser.add_argument("-inputDB", help="MongoDB Collections")
parser.add_argument("--process", help="Video File")
parser.add_argument("--output", dest="XLSOutput", help="XLS File for the data to output in")
args = parser.parse_args()

print(args.process)
print(args.inputDB)
if(args.inputDB is not None):
    myclient = pymongo.MongoClient(args.inputDB)
    mydb = myclient["ProjectDatabase"]
    mycol1 = mydb["Informations"]
    mycol2 = mydb["LocationFrames"]


command = 'ffprobe -i "C:\\Users\\Sarmiento PC\\Desktop\\467_Project\\import_files\\twitch_nft_demo.mp4" -show_entries format=duration -v quiet -of csv="p=0"'.format(args.process)
x = shlex.split(command)

process = subprocess.Popen(
    shlex.split (command),
    stdout = subprocess.PIPE,
    stderr = subprocess.STDOUT, # Redirect STDERR to STDOUT, conjoining the two streams
    shell = True
)

for line in iter(process.stdout.readline, ""):
    if line == b'':
        break
    lengthOfVideo = math.trunc(float(str(line).replace("b'", "").replace("\\r\\n'", ""))) 
    #removing characters and truncate the decimal values, the command from the command variable returns the length of the video in seconds and the decimal part are the
    #milliseconds

print(lengthOfVideo)

lengthOfVideoInFrames = lengthOfVideo * FPS
print("lengthOfVideo in FPS: " + str(lengthOfVideoInFrames))
DictLocAndRangeArray = []
for work2 in mycol2.find({}, {"_id" : 0, "Name on File" : 0, "Date on File" : 0}):
    ranges = work2['Frames/Ranges']
    location = work2['Location']
    if "-" in ranges:
        EndFrame = int(ranges[ranges.index("-")+1::])
        if(lengthOfVideoInFrames >= EndFrame):
            if (location, ranges) not in DictLocAndRangeArray:
                DictLocAndRangeArray.append((location, ranges))
                RangesList.append(ranges)
        
for x in DictLocAndRangeArray:
    print(x)
TimeCodeRanges = []
MiddleTC = []
for ranges in RangesList:
    hyphenIdx = ranges.index("-")
    StartFrame = int(ranges[0:hyphenIdx])
    EndFrame = int(ranges[hyphenIdx+1::])
    MiddleTC.append( FrameToTimeCode(int( (StartFrame + EndFrame) / 2)) )
    StartTime = FrameToTimeCode(StartFrame)
    EndTime = FrameToTimeCode(EndFrame)
    TimeCodeRanges.append((StartTime, EndTime))


'''
The code below that is commented is part of the code
I commented it because it creates all of the thumbnails (41)
and my computer got lag so I commented it out so I do not have
to populate the thumbnails again, but this code is part of the submission

'''
# num = 0
# for VideoOutput in MiddleTC:
#     num = num + 1
#     command = 'ffmpeg -i "C:\\Users\\Sarmiento PC\\Desktop\\467_Project\\import_files\\twitch_nft_demo.mp4" '
#     command =  command + '-ss {} -vframes 1 "C:\\Users\\Sarmiento PC\\Desktop\\467_Project\\Thumbnails\\output{}.png" '.format(VideoOutput, str(num))
#     print(command)
#     x = shlex.split(command)

#     process = subprocess.Popen(
#         shlex.split (command),
#         stdout = subprocess.PIPE,
#         stderr = subprocess.STDOUT, # Redirect STDERR to STDOUT, conjoining the two streams
#         shell = True
#     )

if args.XLSOutput is not None and args.XLSOutput.endswith(".xlsx"):
    workbook = xlsxwriter.Workbook(args.XLSOutput)
    workSheet = workbook.add_worksheet()
    workSheet.set_column('A:D', 80)

    workSheet.write("A1", "Location")
    workSheet.write("B1", "Frames/Ranges")
    workSheet.write("C1", "Timecode Ranges")
    workSheet.write("D1", "Thumbnail")

    TCidx = 0
    IMGidx = 1
    rowCell = 2
    for LocAndRange in DictLocAndRangeArray:
        workSheet.set_row(rowCell, 100)
        workSheet.write('A{}'.format(str(rowCell)), LocAndRange[0])
        workSheet.write('B{}'.format(str(rowCell)), LocAndRange[1])
        workSheet.write('C{}'.format(str(rowCell)), str(TimeCodeRanges[TCidx][0]) + "-" + str(TimeCodeRanges[TCidx][1]))
        workSheet.insert_image('D{}'.format(str(rowCell+1)), 'Thumbnails\output{}.png'.format(str(IMGidx)),  {'x_scale': 0.1, 'y_scale': 0.1})
        TCidx = TCidx + 1
        IMGidx = IMGidx + 1
        rowCell = rowCell + 1

    workbook.close()
