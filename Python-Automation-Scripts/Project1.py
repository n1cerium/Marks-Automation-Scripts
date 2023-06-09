from datetime import datetime
import argparse
import pymongo
import sys
import os
import csv
import getpass

print(getpass.getuser())


def checkValidBaselightFlameFile(FileArray):
    if(FileArray is None):
        return False
    for file in FileArray:
        if (file) is None or not os.path.isfile('./import_files/' + file):
            return False
        if checkCorrectFile(file) == True:
            return False
    
    return True

def checkCorrectFile(File):
    FileParse = File.split("_")
    print(FileParse[0])
    if FileParse[0] == "Xytech":
        return True
    
    return False

def checkValidXytechFile(FileArray):
    if(FileArray is None):
        return False
    for file in FileArray:
        if (file) is None or not os.path.isfile('./import_files/' + file):
            return False
        if checkCorrectFile(file) == False:
            return False
        
    return True


def checkDuplicateFile(FileArray):
    for file in FileArray:
        if file in FileArray[(FileArray.index(file)+1)::]:
            return False
        
    return True

def toStringRange(arr):
    if(len(arr) == 1):
        return str(arr[0])
    
    return str(arr[0]) + "-" + str(arr[-1])

def orderInRange(AnArray):
    dict = {}
    counter = 0
    arr = [AnArray[0]]
    for x in range(1, len(AnArray)):
        if AnArray[x] == "<err>" or AnArray[x] == "<null>":
            x = x+1
            continue
        if(int(arr[-1]) + 1 != int(AnArray[x])):
            dict[counter] = toStringRange(arr)
            counter += 1
            arr = []
        arr.append(int(AnArray[x]))
    dict[counter] = toStringRange(arr)
    return dict

def StoreFileContent(fileName):
    info = []
    for file in fileName:
        with open('./import_files/' + file, 'r') as contents:
            for cont in contents:
                if file.split('_')[0] == "Flame":
                    cont = cont.replace(' ', '/', 1)
                info.append(cont)
    
    return info

def RemoveElementNewLine(array):
    for i in range(0, len(array)):
        array[i] = array[i].rstrip()
    
    return array

def FindIndex(AnArray, str):
    for elem in range(0, len(AnArray)):
        if str == AnArray[elem]:
            return elem
    return -1
    
def FindDir(Arr2, Str1):
    for j in Arr2:
        arr1 = j.split("/")[1::]
        for x in arr1:
            idx = FindIndex(Str1, x)
            if idx != -1:
                return idx
    return -1

def storeValidXytech(file):
    if checkValidXytechFile(file) == True and checkDuplicateFile(file) == True:
        return file
    
    print("Only enter a valid Xytech Files")
    sys.exit(0)

def storeValidBLF(file):
    if checkValidBaselightFlameFile(file) == True and checkDuplicateFile(file) == True:
        return file
    
    print("Make sure no duplicates are entered and only enter Baselight/Flames Text Files")
    sys.exit(0)

def parseFileName(files):
    copyFiles = files
    FileNameContents = []
    for file in copyFiles:
        file = file.replace(".txt", "")
        print(file)
        FileArray = file.split("_")
        FileNameContents.append(FileArray)

    return FileNameContents

parser = argparse.ArgumentParser(description="Project 2")
parser.add_argument("--files", nargs='+', help="Baselight/Flames Text File")
parser.add_argument("-v", "--verbose", action="store_true", help="Store results in database")
parser.add_argument("-xytech", nargs='+', help="Xytech Files")
parser.add_argument("-output", dest="DBDestination", help="CSV file or MongoDB Database information for the data to get stored in")
parser.add_argument("-videoFIle", help="Video File")
args = parser.parse_args()

IsCSV = False
BLFFiles = ""
if(not args.files is None):
    BLFFiles = storeValidBLF(args.files)
if(not args.xytech is None):
    XTFile = storeValidXytech(args.xytech)


if args.DBDestination.endswith('.csv'):
    IsCSV = True

if IsCSV == False:
    myclient = pymongo.MongoClient(args.DBDestination)
    mydb = myclient["ProjectDatabase"]
    mycol1 = mydb["Informations"]
    mycol2 = mydb["LocationFrames"]


if args.verbose:    
    UserThatRanScript = getpass.getuser()
    FileNameInformation = parseFileName(BLFFiles)
    todayDate = datetime.now()
    if IsCSV == False:
        for fileInfo in FileNameInformation:
            FileList = [
                {
                    "User" : UserThatRanScript,
                    "Machine" : fileInfo[0],
                    "Name on File" : fileInfo[1],
                    "Date on File" : fileInfo[2],
                    "Submitted Date" : todayDate.strftime("%d/%m/%Y %H:%M:%S")
                }
            ]
            mycol1.insert_many(FileList)
    
    current_date_time = todayDate.strftime("%d/%m/%Y %H:%M:%S")
    print("date and time =", current_date_time)

    for x in FileNameInformation:
        print(x)

    print()
    print()
    XyInfo = StoreFileContent(XTFile)
    BaseInfo = StoreFileContent(BLFFiles)
    XyInfo = RemoveElementNewLine(XyInfo)
    BaseInfo = RemoveElementNewLine(BaseInfo)
    Producer = ""
    Operator = ""
    Job = ""
    Notes = ""

    for content in XyInfo:
        print(content)
        
        TempStrings = content.split(" ", 1)
        if(TempStrings[0] == "Producer:"):
            Producer = TempStrings[1]
        if(TempStrings[0] == "Operator:"):
            Operator = TempStrings[1]
        if(TempStrings[0] == "Job:"):
            Job = TempStrings[1]
        if(TempStrings[0] == "Notes:"):
            Notes = XyInfo[XyInfo.index(content)+1]
        

    print()

    for content in BaseInfo:
        print(content)

    XyPaths = []
    for content in XyInfo:
        if content != "" and content[0] == '/':
            XyPaths.append(content)

    print()

    for content in XyPaths:
        print(content)

    BasePaths =[]
    Frames = []

    for content in BaseInfo:
        SplitContent = content.split(" ", 1)
        BasePaths.append(SplitContent[0])
        Frames.append(SplitContent[-1])

    print()
    print()

    for content in BasePaths:
        print(content)

    print()
    print()

    for content in Frames:
        print(content)

    print()
    print()

    LocationToFix = []
    for paths in BasePaths:
        SplitPath = paths.split("/")[1::]
        idx = FindDir(XyPaths, SplitPath)
        BaseLocation = paths.find(SplitPath[idx])

        for xPath in XyPaths:
            if xPath.find(paths[BaseLocation:]) != -1:
                LocationToFix.append(xPath)

    for content in LocationToFix:
        print(content)
                
    print()
    print()

    DictArray = []
    for fr in Frames:
        FramesSplit = fr.split(" ")
        DictArray.append(orderInRange(FramesSplit))

    for content in DictArray:
        print(content)

    print()
    print()

    print(str(Producer) + " " + str(Operator) + " " + str(Job))
    print(Notes)

    FramesToFix = []

    for i in range(0, len(LocationToFix)):
        for frame in DictArray[i]:
            FramesToFix.append((LocationToFix[i], DictArray[i][frame]) )

    for item in FramesToFix:
        print(item)

    if IsCSV == False:
        for fileInfo in FileNameInformation:
            for Item in FramesToFix:
                FileList = [
                    {
                        "Name on File" : fileInfo[1],
                        "Date on File" : fileInfo[2],
                        "Location" : Item[0],
                        "Frames/Ranges" : Item[1]
                    }
                ]
                mycol2.insert_many(FileList)

    if IsCSV:
        with open(args.DBDestination, 'w', newline='') as contents:
            fieldnames = (Producer, Operator, Job, Notes)

            content = csv.writer(contents)
            content.writerow(fieldnames)
            content.writerow(())
            content.writerow(())
            for tp in FramesToFix:
                content.writerow(tp)

print()
print()
if IsCSV == False:
    print("Database Calls")
    print("1) List all work done by user TDanza")

    myquery = {"Name on File" : "TDanza"}

    for work in mycol2.find(myquery, {"_id" : 0, "Date on File" : 0}):
        print(work['Location'] + " : " + work['Frames/Ranges'])

    print()
    print()

    print("2) All work done before 3-25-2023 date on Flame")
    myCol1Query = {"Machine" : "Flame"}
    for work1 in mycol1.find(myCol1Query):
        MyCol2Query = {"Name on File" : work1['Name on File']}

        for work2 in mycol2.find(MyCol2Query, {"_id" : 0, "Name on File" : 0}):
            if(int(work2['Date on File']) < 20230325):
                print(work2['Location'] + " : " + work2['Frames/Ranges'])


    print()
    print()

    print("3) What work done on hpsans13 on date 3-26-2023")
    MyCol2Query = {"Date on File" : "20230326"}
    for work in mycol2.find(MyCol2Query, {"_id": 0, "Name on File" : 0, "Date on File" : 0}):
        if 'hpsans13' in work['Location']:
            print(work)

    print()
    print()

    print("4) Name of all Autodesk Flame users")
    myCol1Query = {"Machine" : "Flame"}
    ExistingUser = []
    for work1 in mycol1.find(myCol1Query, {"_id" : 0, "User" : 0, "Date on File" : 0, "Submitted Date" : 0}):
        if work1['Name on File'] not in ExistingUser:
            print(work1['Name on File'])
            ExistingUser.append(work1['Name on File'])

    print()
    print()

