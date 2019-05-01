#!/usr/bin/env python

import glob, os, subprocess, datetime, time, sys, csv


# these are the directories I've been running it on locally, here for easy ref
#   S:\Departments\Digital Services\Internal\DigiPres\Checksum_Inventory_Generation\Contained_Test
#   S:\Departments\Digital Services\Internal\DigiPres\Checksum_Inventory_Generation\Inventories


'''
Winnie Schwaid-Lindner - v.03 of file renaming and inventory script.


1. Ask the root directory, inventory directory, hash algorithm, 
   and which file extensions to process on an inclusionary or exclusionary basis
2. Calculate the checksum using certUtil
3. Look into past inventories and see whether the checksum matches, 
   identify duplicate checksums, or whether the file is new to the directory
4. Check mediainfo metadata against image and audio file standards
   (and, in the future LSU's preferred file specs), to determine if file
   has unexpected or incorrect properties while still being valid
5. Produce a csv inventory of all the file names for each directory
   with the fields:
    * Time stamp of file processed
    * Full file path
    * Directory that the file is in
    * File name
    * Checksum
    * Checksum algorithm
    * Whether the file is being processed by the script for the first time,
      which would indicate a new file (Boolean value)
    * Whether the most recently generated checksum matches the most recent
      past checksum if the file is not new
      (compares checksum to past inventory, this is also Boolean)
    * Tell whether the file is valid according to
      mediainfo metadata matching with expected metadata
'''
line_break = ('{:^}'.format('-'*80))
# do not reset
inventory_acc = 'sep=`\nProcessingTimeStamp`FilePath`RootDirectory`FileName\
`Checksum`ChecksumType`NewFile?`ChecksumMatchesPast?`FileCorrupt?\n'

def take_inputs():
    file_dir_input = ''
    cant_process_zero_files_silly = ''
    while '\\' not in file_dir_input:
        # the directory you want to work with
        file_dir_input = input('CONTENT FILE DIRECTORY:\n\
        Paste the *FULL* path to the folder directory \n\
        that you would like to process:\n> ')
    file_dir = '\\\\?\\%s' % file_dir_input

    inventory_dir = ''
    while '\\' not in inventory_dir:
        # the directory you want to work with
        inventory_dir = input('\nINVENTORY DIRECTORY:\n\
        Paste the *FULL* path to the folder directory \n\
        that you would like to save the inventory in:\n> ')

    checksum_options = ['SHA1', 'MD5', 'SHA256']
    checksum_type = (input('\nCHECKSUM SELECTION:\n\
        Select your checksum type!\n\
        Options are [MD5], [SHA1], or [SHA256].\n\
        NOTE: If you do not select a valid option, default is set to [MD5].\n> '))\
        .upper().replace('[', '').replace(']', '')
    if checksum_type not in checksum_options:
        # if you didn't select a valid checksum, it'll go MD5.
        print('Not a valid choice. Defaulting to MD5 checksums.')
        checksum_type = 'MD5'
    while cant_process_zero_files_silly == '':
        # file type on exclusionary or inclusionary basis
        include_true_exclude_false = True
        file_type_include_exclude = input('\nFILE TYPE INCLUDE / EXCLUDE:\n\
        Would you like to [I]NCLUDE certain file types\n\
        or [E]XCLUDE certain file types?\n\
        NOTE: If you do not select to include or exclude,\n\
        default is set to INCLUDE all files.\n> ')\
        .upper().replace('[', '').replace(']', '')
        if file_type_include_exclude == "E":
            include_true_exclude_false = False
        elif file_type_include_exclude not in ("I", "E"):
            print('Not a valid choice. Defaulting to INCLUDE.')

        file_type_string = input('\nFILE TYPE SELECTION:\n\
        List file types that you would like to process separated by a space\n\
        (ex "pdf jpg xml docx")\n\
        NOTE: If you do not input a file type, every file in the folder\n\
        will be processed.\n> ')
        if (include_true_exclude_false == False) and (file_type_string == ''):
            print("ERROR, you can't exclude all files... \
    Let's try that again...\n")
        else:
            cant_process_zero_files_silly = "aw yis"
    # separate file types from one string into a list
    file_types = file_type_string.split()
    return file_dir, inventory_dir, checksum_type, include_true_exclude_false, file_types, file_type_string


def check_for_inventories(file_dir, inventory_dir):
    latest_inventory = ''
    read_inventory = []
    first_inventory_of_dir = False



    # making path for file name
    modified_path = (file_dir.replace('\\\\?\\', "").replace('\\', "'").replace(":", "'"))
    # see if previous inventory exists by accessing it, if it doesn't,
    #   don't throw error
    try:
        latest_inventory = str(max(glob.iglob(inventory_dir + \
                            '\\__Inventory_' + modified_path + '__*.csv')\
                            ,key=os.path.getmtime))
    except (OSError, ValueError): 
        # this is the first inventory done for this dir
        first_inventory_of_dir = True
    # if it exists, open it, turn it into a list
    if latest_inventory != '':
        with open(latest_inventory) as old_inventory:
            read_inventory = list(csv.reader(old_inventory, delimiter='`'))
        # indicate it's not the first inventory
        first_inventory_of_dir = False
    else:
        # this is the first inventory done for this dir
        first_inventory_of_dir = True
    return modified_path, first_inventory_of_dir, read_inventory


def recursively_do_everything(file_dir, inventory_dir, checksum_type, include_true_exclude_false, file_types, file_type_string, modified_path, first_inventory_of_dir, read_inventory):
        # for each folder and file within that directory
    for root, dirs, files in os.walk(file_dir):
        for folder in dirs:
            dir_name = folder
            print('%s\nCURRENTLY PROCESSING:\n%s\\%s\n' % (line_break, root, dir_name))

        for name in files:
            name_with_path = (os.path.join(root, name))
            # select file types to process
            if name.endswith(tuple(file_types)) == include_true_exclude_false \
            or file_type_string == '':
                # reset file-specific variables for every file
                new_file = ''
                checksum_consistent = ''
                file_error = []
                file_error_count = 0
                # split the portions of the file name to separate the extension
                file_list = name.split('.')
                file_ext = file_list[-1]
                run_checksum = subprocess.check_output(('certUtil -hashfile "' \
                                                        + name_with_path + '" ' \
                                                        + checksum_type), \
                                                    shell=True)
                # split the returned string by line
                checksum_split = run_checksum.decode().split('\r\n')
                # take only the second line, which is the checksum
                checksum = checksum_split[1]
                time_stamp = time.strftime("%Y-%m-%d_%Hh%Mm%Ss")
                new_file = 'Yes'

                if inventory_acc.count('"%s"' % (checksum)) > 0:
                    # if they don't match, there's an error
                    checksum_consistent += 'Duplicate checksum.'
                    # print error in shell
                    print('---WARNING, CHECKSUM APPEARS MORE THAN ONCE:\n\
    %s\n' % (name_with_path))

                # if not the first inventory
                if first_inventory_of_dir == False:
                    # read row by row
                    for row in read_inventory:
                        # if the file name is in the row
                        if name in row[1]:
                            # it's not a new file
                            new_file = ' '
                            # if the checksums match
                            if checksum in str(row[4]):
                                # they are consistent
                                checksum_consistent += ' ' 
                            else:
                                # if they don't match, there's an error
                                checksum_consistent += 'Inconsistent checksum.'
                                # print error in shell
                                print('---WARNING, \
    CHECKSUM DOES NOT MATCH:\n   %s\n' % (row[1]))
                        # if there's a file in the inventory that's not
                        #   in the directory, show error
                        if (os.path.isfile(row[1]) == False \
                            or os.access(row[1], os.R_OK) == False) \
                            and (row[1] != 'FilePath') and (row[1] != ''):
                            if (('`"%s"`"File is missing or cannot be accessed"\n' \
                                % (row[1])) in inventory_acc) == False:
                                inventory_acc += ('"%s"`"%s"`"File is missing \
    or cannot be accessed"\n' % (time_stamp, (row[1])))
                                print('---WARNING, \
    FILE IS MISSING OR CAN NOT BE ACCESSED:\n   %s\n' \
                                    % (row[1]))
                else:
                    new_file = 'First inventory of this directory'
                    checksum_consistent += ' '

                # look at mediainfo technical metadata of image files
                if name.lower().endswith("jpg") or name.lower().endswith("tif") \
                or name.lower().endswith("tiff"):
                    file_extension = (subprocess.check_output(('MediaInfo \
                    --Output=General;%FileExtension% "' + name_with_path +'"'), \
                                                            shell=True))
                    internet_media_type = (subprocess.check_output('MediaInfo \
                    --Output=General;%InternetMediaType% "' + name_with_path +'"', \
                                                                shell=True))                                                             
                    extensions_usually_used = (subprocess.check_output('MediaInfo \
                    --Output=General;%Format/Extensions% "' + name_with_path +'"', \
                                                                    shell=True))                                                                 
                    compression_mode = (subprocess.check_output('MediaInfo \
                    --Output=Image;%Compression_Mode% "' + name_with_path +'"', \
                                                            shell=True))                                                          
                    internet_media_type_formatted = (str(internet_media_type)\
                                                    .split('/'))[0].strip("\\b'")
                    file_extension_formatted = (str(file_extension)).replace("b'", "")\
                    .replace("\\r\\n'", "")
                    extensions_usually_used_formatted = \
                                                    (str(extensions_usually_used))\
                                .replace("b'", "")\
                            .replace("\\r\\n'", "")
                    compression_mode_formatted = (str(compression_mode))\
                                                .lower().strip().replace("b'", "")\
                                                .replace("\\r\\n'", "")
                    if internet_media_type_formatted != \
                    'image':
                        file_error_count += 1
                        file_error.append("File should be an image but isn't.")
                        print('---WARNING, \
    IMAGE FILE IS NOT IMAGE:\n   %s\n' % (name_with_path))
                    if file_extension_formatted\
                    not in extensions_usually_used_formatted:
                        file_error_count += 1
                        file_error.append('File extension not expected value.')
                        print('---WARNING, \
    IMAGE FILE EXTENSION NOT EXPECTED:\n   %s\n' % (name_with_path))
                    if compression_mode_formatted\
                    != 'lossless':
                        file_error_count += 1
                        file_error.append('Compression is not lossless.')
                        print('---WARNING, \
    IMAGE FILE IS NOT LOSSLESS:\n   %s\n' % (name_with_path))


                #look at mediainfo technical metadata of wav files
                if name.lower().endswith("wav"):
                    file_extension = (subprocess.check_output(('MediaInfo \
                    --Output=General;%FileExtension% "' + name_with_path +'"'), \
                                                            shell=True))
                    internet_media_type = (subprocess.check_output('MediaInfo \
                    --Output=General;%InternetMediaType% "' + name_with_path +'"', \
                                                                shell=True))                                                             
                    extensions_usually_used = (subprocess.check_output('MediaInfo \
                    --Output=General;%Format/Extensions% "' + name_with_path +'"', \
                                                                    shell=True))                                                                 
                    sampling_rate = (subprocess.check_output('MediaInfo \
                    --Output=Audio;%SamplingRate% "' + name_with_path +'"', \
                                                            shell=True))                                                          
                    internet_media_type_formatted = (str(internet_media_type)\
                                                    .split('/'))[0].strip("\\b'")
                    file_extension_formatted = (str(file_extension)).replace("b'", "")\
                    .replace("\\r\\n'", "")
                    extensions_usually_used_formatted = \
                                                    (str(extensions_usually_used))\
                                .replace("b'", "")\
                            .replace("\\r\\n'", "")
                    sampling_rate_formatted = (str(sampling_rate))\
                                                .lower().strip().replace("b'", "")\
                                                .replace("\\r\\n'", "")
                    if internet_media_type_formatted != \
                    'audio':
                        file_error_count += 1
                        file_error.append("File should be a audio but isn't.")
                        print('---WARNING, \
    AUDIO FILE IS NOT AUDIO:\n   %s\n' % (name_with_path))
                    if file_extension_formatted\
                    not in extensions_usually_used_formatted:
                        file_error_count += 1
                        file_error.append('File extension not expected value.')
                        print('---WARNING, \
    AUDIO FILE EXTENSION NOT EXPECTED:\n   %s\n' % (name_with_path))
                    if sampling_rate_formatted\
                    != '44100':
                        file_error_count += 1
                        file_error.append('Sampling rate is incorrect.')
                        print('---WARNING, \
    AUDIO SAMPLING RATE INCORRECT:\n   %s\n' % (name_with_path))
                if file_error != []:
                    error_grouping = ("%s Error(s): %s" % \
                                    (file_error_count, \
                                    (' '.join(file_error))))
                else:
                    error_grouping = ''
                # an accumulator that adds all inventory information for the .csv    
                inventory_acc += ('"%s"`"%s"`"%s"`"%s"`"%s"`"%s"`"%s"`"%s"`"%s"\n' \
                                % (time_stamp, name_with_path, root, name, \
                                    checksum, checksum_type, new_file, \
                                    checksum_consistent, error_grouping))


            else:
                time_stamp = time.strftime("%Y-%m-%d_%Hh%Mm%Ss")
                inventory_acc += ('"%s"`"%s"`"%s"`"%s"`"File extension not selected \
    for processing"\n' % (time_stamp, name_with_path, root, name))
    return inventory_acc


def write_file(inventory_dir, modified_path, inventory_acc):
    time_stamp = time.strftime("%Y-%m-%d_%Hh%Mm%Ss")
    # the file name for the generated inventory.
    #   This will start with two underscores for easy sorting within the directory
    #   and also contain the directory's name in its own file name
    #   in case the inventory becomes disassociated.
    inventory_name = (inventory_dir + '\\__Inventory_' + modified_path + \
                    '___' + str(time_stamp) + '.csv')
    
    # creates new file for inventory
    with open(inventory_name, 'w+') as outfile:
        # fills in accumulator
        outfile.writelines(inventory_acc)
    # all done!
    outfile.close()
    # print that this inventory has been completed
    print('%s\nCOMPLETED:\nInventory saved as\n%s' \
        % (('{:^}'.format('='*80)),inventory_name))


def main():
    file_dir, inventory_dir, checksum_type, include_true_exclude_false, file_types, file_type_string = take_inputs()
    modified_path, first_inventory_of_dir, read_inventory = check_for_inventories(file_dir, inventory_dir)
    inventory_acc = recursively_do_everything(file_dir, inventory_dir, checksum_type, include_true_exclude_false, file_types, file_type_string, modified_path, first_inventory_of_dir, read_inventory)
    write_file(inventory_dir, modified_path, inventory_acc)


if __name__ == '__main__':
    main()