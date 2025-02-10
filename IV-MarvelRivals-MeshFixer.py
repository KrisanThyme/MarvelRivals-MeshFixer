##Script By: MrPolarburr
##Reverse Engineer: Krisan Thyme
##Asistance: rkss
##Version: 1.0
##This script is used to fix Meshes in Marvel Rivals.
##Code Based off UAssetGui https://github.com/atenfyr/UAssetGUI

import os
import struct
import shutil
from tkinter import Tk
from tkinter.filedialog import askopenfilename

MAKE_BACKUPS = True
UASSET_MAGIC = 0x9E2A83C1
ISLASTMASK = 0x0100

offsets = []
sizes = []

FinalSizeOffset = 0
bulkOffset = 0
materialCount = 0

def closeprogram():
    input('Press enter to Exit.')
    exit()

def readExports(f, exportCount, exportOffset):
    f.seek(exportOffset)
    for i in range(exportCount):
        classIndex = struct.unpack('i', f.read(4))[0]
        superIndex = struct.unpack('i', f.read(4))[0]
        templateIndex = struct.unpack('I', f.read(4))[0]
        outerIndex = struct.unpack('I', f.read(4))[0]
        nameMapPointer = struct.unpack('I', f.read(4))[0]
        number = struct.unpack('I', f.read(4))[0]
        objectFlags = struct.unpack('I', f.read(4))[0]

        ## assuming Asset Object Version is Automatic

        if i == exportCount - 1:
            global FinalSizeOffset
            FinalSizeOffset = f.tell()

        serialSize = struct.unpack('q', f.read(8))[0]
        serialOffset = struct.unpack('q', f.read(8))[0]

        sizes.append(serialSize)
        offsets.append(serialOffset)

        forcedExport = struct.unpack('i', f.read(4))[0]
        notForClient = struct.unpack('i', f.read(4))[0]
        notForServer = struct.unpack('i', f.read(4))[0]
        inheritedInstance = struct.unpack('i', f.read(4))[0]
        packageFlags = struct.unpack('I', f.read(4))[0]
        alwaysLoadedForEditorGame = struct.unpack('i', f.read(4))[0]
        isAsset = struct.unpack('i', f.read(4))[0]
        generatePublicHash = struct.unpack('i', f.read(4))[0]
        firstExportDependency = struct.unpack('I', f.read(4))[0]
        SerializationBeforeSerializationDependenciesSize = struct.unpack('I', f.read(4))[0]
        CreateBeforeSerializationDependenciesSize = struct.unpack('I', f.read(4))[0]
        SerializationBeforeCreateDependenciesSize = struct.unpack('I', f.read(4))[0]
        CreateBeforeCreateDependenciesSize = struct.unpack('I', f.read(4))[0]

def readuasset(file):
    with open(file, 'rb') as f:
        magic = struct.unpack('I', f.read(4))[0]
        
        if magic != UASSET_MAGIC:
            print('Invalid UAsset file')
            closeprogram()

        legacyfileversion = struct.unpack('i', f.read(4))[0]

        if legacyfileversion != -4:
            f.read(4) # skip

        fileversionUE5 = 0
        fileversionUE4 = struct.unpack('i', f.read(4))[0]

        if fileversionUE4 != 0:
            print("Unsupported UE4 file version")
            closeprogram()

        if legacyfileversion <= -8:
            fileversionUE5 = struct.unpack('i', f.read(4))[0]

        fileVersionLicenseeUE = struct.unpack('i', f.read(4))[0]

        if legacyfileversion <= -2:
            numCustomVersions = struct.unpack('i', f.read(4))[0]

            for i in range(numCustomVersions):
                f.read(16) ## ID
                f.read(4) ## verNum

        sectionSixOffset = struct.unpack('I', f.read(4))[0]
        folderNameLen = struct.unpack('I', f.read(4))[0]
        folderName = f.read(folderNameLen).decode('utf-8').rstrip('\x00')
        packageFlags = struct.unpack('I', f.read(4))[0]
        nameCount = struct.unpack('I', f.read(4))[0]
        nameOffset = struct.unpack('I', f.read(4))[0]

        ##assuming here that objectverUE5 is data_esource

        softObjectPathCount = struct.unpack('I', f.read(4))[0]
        softObjectPathOffset = struct.unpack('I', f.read(4))[0]

        ##assuming here that objectver is automatic ve
        gatherableTextDataCount = struct.unpack('I', f.read(4))[0]
        gatherableTextDataOffset = struct.unpack('I', f.read(4))[0]

        expotCount = struct.unpack('I', f.read(4))[0]
        exportOffset = struct.unpack('I', f.read(4))[0]
        importCount = struct.unpack('I', f.read(4))[0]
        importOffset = struct.unpack('I', f.read(4))[0]
        dependsOffset = struct.unpack('I', f.read(4))[0]
        SoftPackageReferencesCount = struct.unpack('I', f.read(4))[0]
        SoftPackageReferencesOffset = struct.unpack('I', f.read(4))[0]
        SearchableNamesOffset = struct.unpack('I', f.read(4))[0]

        ThumbnailTableOffset = struct.unpack('I', f.read(4))[0]

        f.read(16) ## GUID

        generationCount = struct.unpack('I', f.read(4))[0]

        for i in range(generationCount):
            f.read(4)
            f.read(4)

        f.read(10)

        nameLen = struct.unpack('I', f.read(4))[0]

        name = f.read(nameLen).decode('utf-8').rstrip('\x00')

        f.read(10)

        nameLen = struct.unpack('I', f.read(4))[0]

        name = f.read(nameLen).decode('utf-8').rstrip('\x00')

        f.read(4)
        f.read(4)
        f.read(4)

        numAdditionalCookePackages = struct.unpack('I', f.read(4))[0]

        for i in range(numAdditionalCookePackages):
            nameLen = struct.unpack('I', f.read(4))[0]
            name = f.read(nameLen).decode('utf-8').rstrip('\x00')

        assetRegenDataOffset = struct.unpack('I', f.read(4))[0]

        global bulkOffset
        bulkOffset = f.tell()

        bulkDataStartOffset = struct.unpack('q', f.read(8))[0]

        readExports(f, expotCount, exportOffset)

def readuexp(file, fileSize, tempFile):

    global materialCount
    finalOffset = offsets[-1] - fileSize

    with open(file, 'rb') as f, open(tempFile, 'wb') as o:
        ##assuming last export is the one we want
        o.write(f.read(finalOffset))
        
        print("Starting search for data at Offset: %s" % hex(f.tell()))
        
        ##dirty way of finding what we need
        maxMatCount = 255
        maxBytes = 500000
        currentBytes = 0
        startingPos = f.tell()
        while True:
            if currentBytes > maxBytes:
                result = input("Failed to find data within range %s - %s. Do you want to continue searching? (y/n): " % (hex(startingPos), hex(f.tell())))
                if result.lower() == 'n':
                    print("Cancelling...")
                    tempFile.close()
                    f.close()
                    os.remove(tempFile)
                    closeprogram()
                
                if result.lower() == 'y':
                    maxBytes += 500000

            checkedBytes = f.read(3)
            currentBytes += 3

            if checkedBytes == b'\xff\xff\xff':
                
                if f.read(1) != b'\xff':
                    f.seek(-1, 1)
                else:
                    currentBytes += 1
                    continue

                f.seek(-8, 1)
                materialCount = struct.unpack('i', f.read(4))[0]

                if materialCount > 0 and materialCount < maxMatCount:
                    break
                else:
                    f.seek(4, 1)
            else:
                currentBytes -= 2
                f.seek(-2, 1)

        print("Found data at Offset: %s" % hex(f.tell()))
        endingPos = f.tell()

        f.seek(startingPos)
        o.write(f.read(endingPos - startingPos))
        print("Found %d materials" % materialCount)

        for i in range(materialCount):
            o.write(f.read(40))
            o.write(b'\x00\x00\x00\x00')

        o.write(f.read())
        o.close()
        f.close()

    with open(file, 'wb') as f, open(tempFile, 'rb') as o:
        f.write(o.read())
        f.close()
        o.close()
    
    os.remove(tempFile)

def cleanuasset(file):
    print("Starting Asset Cleaning...")

    finalSize = sizes[-1] + (4*materialCount)

    with open(file, 'r+b') as f:
        f.seek(FinalSizeOffset)
        f.write(finalSize.to_bytes(8, 'little'))
        f.flush()
        
        f.seek(bulkOffset)
        bulkStartOffset = struct.unpack('q', f.read(8))[0]
        f.seek(-8, 1)
        fixedOffset = bulkStartOffset + (4*materialCount)
        f.write(fixedOffset.to_bytes(8, 'little'))
        f.close()

    print("Asset Cleaning Complete!")
    closeprogram()

def createbackups(uassetFile, uexpFile, dirPath):
    shutil.copy(uassetFile, uassetFile + ".bak")
    shutil.copy(uexpFile, uexpFile + ".bak")
    

def main():
    uassetFile = askopenfilename(title="Select UEXP File", filetypes=[("Unreal Engine Asset File", "*.uasset")])

    if not uassetFile:
        print("No file selected. Cancelling...")
        closeprogram()
        
    dirPath = os.path.dirname(os.path.abspath(uassetFile))
    uexpFile = os.path.join(dirPath, os.path.basename(uassetFile).replace(".uasset", ".uexp"))
    tempFile = os.path.join(dirPath, "temp")

    if not os.path.exists(uexpFile):
        print("No UEXP file found. Cancelling...")
        closeprogram()

    if MAKE_BACKUPS:
        createbackups(uassetFile, uexpFile, dirPath)

    readuasset(uassetFile)
    readuexp(uexpFile, os.path.getsize(uassetFile), tempFile)
    cleanuasset(uassetFile)

main()