#!/usr/bin/env python

'''
Winnie Schwaid-Lindner - v.01 of file renaming and inventory script.

1. Ask the root directory, hash algorithm, and which file types to process before calculating an individual file's checksum according to the submitted parameters.
2. Calculate the checksum
3. Append the checksum to the file name
4. Produce an inventory of all the file names in each directory with the fields:
    * Time stamp of file processed
    * Full file path
    * Directory that the file is in
    * Original file name
    * New file name which includes the checksum
    * Notes whether the file is being processed by the script for the first time (Boolean value)
    * Notes whether the most recently generated checksum matches a past generated checksum (compares checksum to file name, this is also Boolean)

'''

import os, subprocess, datetime, time, sys, imghdr
from pydub import AudioSegment

#'G:\Snakes\Test_Documents\Contained_Test'
#'G:\Snakes\Test_Documents\Contained_Test\This_is_a_folder'




file_dir = ''
while '\\' not in file_dir:
    file_dir = input('Paste the *FULL* path to the folder directory that you would like to process:\n> ') # the directory you want to work with

today = datetime.date.today()
checksum_options = ['SHA1', 'MD5', 'SHA256']
checksum_type = (input('Select your checksum type! Options are "MD5", "SHA1", or "SHA256". Default is set to "MD5".\n> ')).upper()
if checksum_type not in checksum_options: # if you didn't select a valid checksum, it'll go MD5.
    print('Your choice is not on the list. Defaulting to MD5 checksums.')
    checksum_type = 'MD5'

file_type_string = input('List file types that you would like to process separated by a space (ex "pdf jpg xml docx")\nNOTE: If you do not input a file type, every file in the folder will be processed.\n> ')
file_types = file_type_string.split() # separate file types from one string into a list           
 
for root, dirs, files in os.walk(file_dir): # for each folder and file within that directory
    inventory_acc = 'sep=`\nProcessingTimeStamp`FilePath`RootDirectory`OrigFileName`ChecksumFileName`Checksum`NewFile?`ChecksumMatchesPast?`FileCorrupt?\n' # reset for every dir
    for name in files:
        if name.endswith(tuple(file_types)) or file_type_string == '': # select file types to process
            new_file = '' # reset for every file
            checksum_consistent = '' # reset for every file
            name_without_checksum = '' # reset for every file
            file_name_with_checksum = '' # reset for every file
            file_corrupt = ''
      
    
            if 'SHA1' not in name and 'MD5' not in name and 'SHA256' not in name and (name.startswith('__') == False): # make sure that the file name does not already have a checksum generated
                new_file = 'YES'
                old_name_with_path = (os.path.join(root, name)) # the complete file name including the path
                file_list = name.split('.') # split the portions of the file name to separate the extension
                file_ext = file_list[-1:] # the file extension only without the period (ex 'jpg')
                name_without_ext = '.'.join(map(str, file_list[:-1])) # the name of the file only without the extension (ex 'cute_dogs'), joined so that if a file name includes a '.' it's ok
                name_without_checksum = name
                run_checksum = subprocess.check_output(('certUtil -hashfile "' + old_name_with_path + '" ' + checksum_type), shell=True) # get the checksum using certUtil CLI, this is MD5 but this can be changed
                checksum_split = run_checksum.decode().split('\r\n') # split the returned string by line
                checksum = checksum_split[1] # take only the second line, which is the checksum
                file_name_with_checksum = (name_without_ext + '___' + checksum_type.upper() + '_' + checksum + '.' + str(file_ext)[2:-2]) # create a completed new filename
                name_with_path = (os.path.join(root, file_name_with_checksum)) # new file name including path
                os.rename(old_name_with_path, name_with_path) # rename old file name to new, which includes checksum
            else:
                name_with_path = (os.path.join(root, name))
                old_file_name_split = name.split('___') # split the portions of the file name to separate the original file name
                file_list = name.split('.') # split the portions of the file name to separate the extension
                file_ext = file_list[-1]
                file_name_parts = [old_file_name_split[0], file_list[-1]]
                name_without_checksum = '.'.join(map(str, file_name_parts))
                file_name_with_checksum = name
                run_checksum = subprocess.check_output(('certUtil -hashfile "' + name_with_path + '" ' + checksum_type), shell=True)
                checksum_split = run_checksum.decode().split('\r\n') # split the returned string by line
                checksum = checksum_split[1] # take only the second line, which is the checksum
                if checksum not in name:
                    checksum_consistent = 'CHECKSUM DOES NOT MATCH FILE NAME'

            if name.endswith("mp3") or name.endswith("wav") or name.endswith("dsd"):
                file_corrupt = ''
                try:
                    sound = AudioSegment.from_file(name_with_path)
                    loudness = sound.dBFS
                except:
                    exc = sys.exc_info()[:-1]
                    file_corrupt = 'ERROR'
                    print(file_corrupt, name_with_path, exc)
         #problems start here       
            if name.endswith("jpg") or name.endswith("tiff") or name.endswith("pdf"):
                e = ''
                try:
                    img = imghdr.what(name_with_path)
                    if img == None:
                        file_corrupt = 'ERROR'
                    print(file_corrupt, name_with_path, 'img == None')
                except:
                    exc = sys.exc_info()
                    file_corrupt = 'ERROR'
                    print(file_corrupt, name_with_path, exc)

            time_stamp = time.strftime("%Y-%m-%d_%Hh%Mm%Ss")
            inventory_acc += ('"%s"`"%s"`"%s"`"%s"`"%s"`"%s"`"%s"`"%s"`"%s"\n' % (time_stamp, name_with_path, root, name_without_checksum, file_name_with_checksum, checksum, new_file, checksum_consistent, file_corrupt)) # an accumulator that adds all inventory information for the .csv
    time_stamp = time.strftime("%Y-%m-%d_%Hh%Mm%Ss")
    local_folder = str(root.split('\\')[-1]) # identifying most local directory
    inventory_name = (str(root) + '\\__' + local_folder + '__Inventory_' + str(time_stamp) + '.csv') # the file name for the generated inventory. This will start with two underscores for easy sorting within the directory and also contain the directory's name in its own file name in case the inventory becomes disassociated.
    with open(inventory_name, 'w+') as outfile: # creates new file for inventory
        outfile.writelines(inventory_acc) # fills in accumulator
    outfile.close() # all done!
    print(root, 'inventory completed')


