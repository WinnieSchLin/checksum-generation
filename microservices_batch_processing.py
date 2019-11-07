#!/usr/bin/env python

import glob, os, subprocess, datetime, time, sys, csv
import xml.etree.ElementTree as ET


# these are the directories I've been running it on locally, here for easy ref
#   S:\Departments\Digital Services\Internal\DigiPres\Checksum_Inventory_Generation\Contained_Test
#   S:\Departments\Digital Services\Internal\DigiPres\Checksum_Inventory_Generation\Inventories


'''
Winnie Schwaid-Lindner - checksum and inventory script.


1. Ask the root directory, inventory directory, hash algorithm, 
   and which file extensions to process on an inclusionary or exclusionary basis
2. Calculate the checksum using certUtil
3. Look into past inventories and see whether the checksum matches, 
   identify duplicate checksums, or whether the file is new to the directory
    * Append checksum to file name, if desired
4. Check mediainfo metadata against image and audio file standards
   (and, in the future, check to see whether it matches LSU's preferred file specs),
   to determine if file has unexpected or incorrect properties while still being 
   valid, or determine if the file is corrupted
5. Produce a csv inventory of all the file names for each directory
   with the fields:
    * Time stamp of file processed
    * Full file path
    * Directory that the file is in
    * File name (and previous file name, if checksum is appended to file name)
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
def take_inputs():
    file_dir_input = ''
    # while there is no path selected
    while '\\' not in file_dir_input:
        # the directory you want to work with
        file_dir_input = input('CONTENT FILE DIRECTORY:\n\
        Paste the *FULL* path to the folder directory \n\
        that you would like to process:\n> ')
    # add '\\?\' to make universal path\
    #   (combat character limit for long paths)
    file_dir = '\\\\?\\%s' % file_dir_input

    inventory_dir_input = ''
    # while there is no path selected
    while '\\' not in inventory_dir_input:
        # the directory you want to work with
        inventory_dir = input('\nINVENTORY DIRECTORY:\n\
        Paste the *FULL* path to the folder directory \n\
        that you would like to save the inventory in:\n> ')
    # add '\\?\' to make universal path (combat character limit for long paths)
    inventory_dir = '\\\\?\\%s' % file_dir_input

    # existing checksum options that you can pick from
    checksum_options = ['SHA1', 'MD5', 'SHA256']
    checksum_type = (input('\nCHECKSUM SELECTION:\n\
        Select your checksum type!\n\
        Options are [MD5], [SHA1], or [SHA256].\n\
        NOTE: If you do not select a valid option, \
        default is set to [MD5].\n> '))\
        .upper().replace('[', '').replace(']', '')
    if checksum_type not in checksum_options:
        # if you didn't select a valid checksum, it'll go MD5.
        print('Not a valid choice. Defaulting to MD5 checksums.')
        checksum_type = 'MD5'

    file_type_include_exclude = ''
    while file_type_include_exclude == '':
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

        # file types that you'd like to highlight
        file_type_string = ' '
        while file_type_string == ' ':
            file_type_string = input('\nFILE TYPE SELECTION:\n\
            List file types that you would like to process \
            separated by a space\n(ex "pdf jpg xml docx")\n\
            NOTE: If you do not input a file type, every file in the folder\n\
            will be processed.\n> ')
            if (include_true_exclude_false == False) and \
                (file_type_string == ''):
                print("ERROR, you can't exclude all files... \
                    Let's try that again...\n")
    # separate file types from one string into a list
    file_types = file_type_string.split()
    
    return file_dir, inventory_dir, checksum_type, include_true_exclude_false, \
        file_types, file_type_string

# see if there are existing inventories of the same directory
def check_for_inventories(file_dir, inventory_dir):
    latest_inventory = ''
    read_inventory = []
    first_inventory_of_dir = False
    set_first_dir = set()
    set_first_dir_names = set()
    set_matches = set()
    dict_first_dir = {}
    # making path for file name
    modified_path = (file_dir.replace('\\\\?\\', "").replace('\\', "'")\
        .replace(":", "'"))
    # see if previous inventory exists by accessing it, if it doesn't,
    #   continue on
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
    # if not the first inventory
    if first_inventory_of_dir == False:
        # read row by row
        for row in read_inventory:
            # if there's a full line
            #   (which would indicate that there's a file represented)
            if len(row) > 4:
                # add info to dict and 2 sets
                dict_first_dir[(row[1])] = row[4]
                set_first_dir.add((row[1], row[4]))
                set_first_dir_names.add((row[1]))
            else:
                # if there's a file that previously was listed as missing,
                #   this will catch it
                set_first_dir_names.add((row[1]))
    return modified_path, first_inventory_of_dir, read_inventory, \
        set_first_dir, dict_first_dir, set_first_dir_names, set_matches


#
def file_name_inventory(file_dir, include_true_exclude_false, file_type_string, file_types):
    file_name_acc = {}
    file_count_acc = 0
    not_selected_acc = set()
    # for each folder and file within that directory
    for root, dirs, files in os.walk(file_dir):
        for folder in dirs:
            dir_name = folder
            print('\n%s\nCURRENTLY PROCESSING:\n%s\\%s' % \
                (line_break, root, dir_name))
        for name in files:
            name_with_path = (os.path.join(root, name))
            try:
                # select file types to process
                if name.endswith(tuple(file_types)) == include_true_exclude_false \
                or file_type_string == '':
                    # reset file-specific variables for every file
                    # split the portions of the file name to separate the extension
                    file_count_acc +=1
                    file_name_acc[file_count_acc] = (name_with_path).replace('//', '////')
                else:
                    not_selected_acc.add((name_with_path))
            except:
                print('---WARNING, ERROR:\n   %s\n' % (name_with_path))
    total_to_do = len(file_name_acc)
    total_not_selected = len(not_selected_acc)
    with open('C:\\Users\\wschlin\\Documents\\File_Name_Acc.txt', 'w') as file_name_acc_file:
        # fills in accumulator
        file_name_acc_file.writelines('%s\n\n%s' % (str(file_name_acc), str(not_selected_acc)))
        
    # all done!
    file_name_acc_file.close()
    return file_name_acc, not_selected_acc, total_to_do, total_not_selected

def recursive_by_file(file_dir, include_true_exclude_false, file_type_string, \
    file_types, checksum_type, inventory_acc, first_inventory_of_dir, \
    read_inventory, set_first_dir, dict_first_dir, set_first_dir_names, \
    set_matches, file_name_acc, not_selected_acc, total_to_do, total_not_selected):
    # for each folder and file within that directory
    checkpoint = 0
    while checkpoint < total_to_do:
        checkpoint += 1
        name_with_path = file_name_acc[checkpoint]
        set_matches.add((name_with_path))
        time_stamp = time.strftime("%Y-%m-%d_%Hh%Mm%Ss")
        try:
            # reset file-specific variables for every file
            new_file = ''
            checksum_consistent = ''
            file_error = []
            file_error_count = 0

            # split the portions of the file name to separate the extension
            root, name = os.path.split(name_with_path)
            file_ext = os.path.splitext(name)[-1]
            new_file, checksum, checksum_consistent, file_error, \
                file_error_count, inventory_acc, set_matches = \
                checksums(name, name_with_path, checksum_type, \
                inventory_acc, first_inventory_of_dir, read_inventory, \
                new_file, checksum_consistent, file_error, \
                file_error_count, file_list, file_ext, \
                set_first_dir, dict_first_dir, set_first_dir_names, \
                set_matches)
            # find errors in mediainfo for images and audio
            mediainfo_extensions = ('jpg', 'jp2', 'tif', 'tiff', 'wav', 'mov')
            if name.lower().endswith(mediainfo_extensions):
                file_error_count, file_error = \
                    mediainfo(name, name_with_path, file_error_count, \
                    file_error)

            inventory_acc = accumulation(inventory_acc, time_stamp, \
                name_with_path, root, name, checksum, checksum_type, \
                new_file, checksum_consistent, file_error, file_error_count)
        except:
            inventory_acc += f"""{time_stamp}`{name_with_path}`{root}`{name}\
                    `"Error in Processing"\n"""
            print('---WARNING, ERROR IN PROCESSING:\n   %s\n' % (name_with_path))
        del file_name_acc[checkpoint]
        # determine which files were in previous inventory but not dir
    leftover_files = set_first_dir_names - (set_matches|not_selected_acc)

    return inventory_acc, leftover_files

def mediainfo(name, name_with_path, file_error_count, file_error):
    
    mediainfo_dict = {}
    desired_fields = ['FileExtension', 'InternetMediaType', 'Format/Extensions', 'Compression_Mode', 'SamplingRate']
    # look at mediainfo technical metadata of image files
    mediainfo_output_full = (subprocess.check_output(('MediaInfo \
        -f --Language=raw "' + name_with_path +'"'), \
        shell=True))
    mediainfo_full_format = (str(mediainfo_output_full).replace('  ', '').replace('\\r\\n', '\n').replace("['", "").replace("']", "").split('\n'))
    for output_line in mediainfo_full_format:
        try:
            field, value = (output_line.split(': ')).strip()
        except:
            field = (output_line.split(': ')[0]).strip()
            value = (output_line.split(': ')[-1]).strip()
        info_dict[field] = value
    mediainfo_dict = {}
    for desired in desired_fields_dict:
        try:
            mediainfo_dict[desired] = (info_dict[desired])
        except:
            mediainfo_dict[desired] = ''
            pass 

    if mediainfo_dict['FileExtension'] not in mediainfo_dict['Format/Extensions']:
        file_error_count += 1
        file_error.append('File extension not expected value.')
        print('---WARNING, IMAGE FILE EXTENSION NOT EXPECTED:\n   %s\n' % \
            (name_with_path))
    if mediainfo_dict['Compression_Mode'] is not ('lossless' or 'Lossless' or ''):
        file_error_count += 1
        file_error.append('Compression is not lossless.')
        print('---WARNING, FILE IS NOT LOSSLESS:\n   %s\n' % \
            (name_with_path))
    if (int(mediainfo_dict['SamplingRate']) <= int('44100')) and (mediainfo_dict['SamplingRate'] is not ''):
        file_error_count += 1
        file_error.append('Sampling rate is incorrect.')
        print('---WARNING, AUDIO SAMPLING RATE INCORRECT:\n   %s\n' % \
            (name_with_path))
    
    return file_error_count, file_error
#
'''
def recursive_by_file(file_dir, include_true_exclude_false, file_type_string, \
    file_types, checksum_type, inventory_acc, first_inventory_of_dir, \
    read_inventory, set_first_dir, dict_first_dir, set_first_dir_names, \
    set_matches):
    # for each folder and file within that directory
    for root, dirs, files in os.walk(file_dir):
        for folder in dirs:
            dir_name = folder
            print('\n%s\nCURRENTLY PROCESSING:\n%s\\%s' % \
                (line_break, root, dir_name))
        for name in files:
            name_with_path = (os.path.join(root, name))
            print('--%s' % name_with_path)
            set_matches.add((name_with_path))
            time_stamp = time.strftime("%Y-%m-%d_%Hh%Mm%Ss")
            try:
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
                    new_file, checksum, checksum_consistent, file_error, \
                        file_error_count, inventory_acc, set_matches = \
                        checksums(name, name_with_path, checksum_type, \
                        inventory_acc, first_inventory_of_dir, read_inventory, \
                        new_file, checksum_consistent, file_error, \
                        file_error_count, file_list, file_ext, \
                        set_first_dir, dict_first_dir, set_first_dir_names, \
                        set_matches)
                    # find errors in mediainfo for images and audio
                    file_error_count_images, file_error_images = 0, []
                    if name.lower().endswith(('jpg', 'jp2', 'tif', 'tiff')):
                        file_error_count_images, file_error_images = \
                            mediainfo_images(name, name_with_path, file_error_count, \
                            file_error)
                    file_error_count_audio, file_error_audio = 0, []
                    if name.lower().endswith(('wav')):
                        file_error_count_audio, file_error_audio = \
                            mediainfo_audio(name, name_with_path, file_error_count, \
                            file_error)
                    file_error_count = file_error_count_audio + \
                        file_error_count_images
                    #combine errors to single field
                    file_error = file_error_audio + file_error_images
                    inventory_acc = accumulation(inventory_acc, time_stamp, \
                        name_with_path, root, name, checksum, checksum_type, \
                        new_file, checksum_consistent, file_error, file_error_count)
                else:
                    time_stamp = time.strftime("%Y-%m-%d_%Hh%Mm%Ss")
                    #inventory_acc += ('"%s"`"%s"`"%s"`"%s"`"File extension not selected \
        #for processing"\n' % (time_stamp, name_with_path, root, name))
                    inventory_acc += f"""{time_stamp}`{name_with_path}`{root}`{name}\
                        `"File extension not selected for processing"\n"""
            except:
                inventory_acc += f"""{time_stamp}`{name_with_path}`{root}`{name}\
                        `"Error in Processing"\n"""
                print('---WARNING, ERROR IN PROCESSING:\n   %s\n' % (name_with_path))
        # determine which files were in previous inventory but not dir
        leftover_files = set_first_dir_names - set_matches

    return inventory_acc, leftover_files
'''
def checksums(name, name_with_path, checksum_type, inventory_acc, \
    first_inventory_of_dir, read_inventory, new_file, checksum_consistent, \
    file_error, file_error_count, file_list, file_ext, set_first_dir, \
    dict_first_dir, set_first_dir_names, set_matches):
    run_checksum = subprocess.check_output(('certUtil -hashfile "' + \
        name_with_path + '" ' + checksum_type), shell=True)
    # split the returned string by line
    checksum_split = str(run_checksum).split('\\r\\n')
    # take only the second line, which is the checksum
    checksum = checksum_split[1]
    new_file = 'Yes'
    if inventory_acc.count('"%s"' % (checksum)) > 0:
        # if they don't match, there's an error
        checksum_consistent += 'Duplicate checksum.'
        # print error in shell
        print('---WARNING, CHECKSUM APPEARS MORE THAN ONCE:\
            \n   %s\n' % (name_with_path))
    if name_with_path in set_first_dir_names:
        # it's not a new file
        new_file = ' '
        # if the checksums match
        if dict_first_dir[name_with_path] in checksum:
            # they are consistent
            checksum_consistent += ' '
        else:
            # if they don't match, there's an error
            checksum_consistent += 'Inconsistent checksum.'
            # print error in shell
            print('---WARNING, CHECKSUM DOES NOT MATCH:\n   %s\n' % \
                (name_with_path))
    else:
        new_file = 'First inventory of this directory'
        checksum_consistent += ' '
    return new_file, checksum, checksum_consistent, file_error, \
        file_error_count, inventory_acc, set_matches

def file_in_inv_not_dir(inventory_acc, leftover_files):
    for leftover in leftover_files:
        if (('`"%s"`"File is missing or cannot be accessed"\n' \
            % (leftover)) in inventory_acc) == False \
            and leftover not in ('FilePath', ""):
            time_stamp = time.strftime("%Y-%m-%d_%Hh%Mm%Ss")
            inventory_acc += ('"%s"`"%s"`"File is missing or cannot be accessed"\n'\
                 % (time_stamp, (leftover)))
            print('---WARNING, FILE IS MISSING OR CANNOT BE ACCESSED:\
                \n   %s\n' % (leftover))
    return inventory_acc



def accumulation(inventory_acc, time_stamp, name_with_path, root, name, \
    checksum, checksum_type, new_file, checksum_consistent, file_error, \
    file_error_count):
    if file_error != []:
        error_grouping = ("%s Error(s): %s" % (file_error_count, \
            (' '.join(file_error))))
    else:
        error_grouping = ''
    # an accumulator that adds all inventory information for the .csv    
    inventory_acc += ('"%s"`"%s"`"%s"`"%s"`"%s"`"%s"`"%s"`"%s"`"%s"\n' \
        % (time_stamp, name_with_path, root, name, checksum, \
        checksum_type, new_file, checksum_consistent, error_grouping))
    return inventory_acc

def write_file(inventory_dir, modified_path, inventory_acc):
    time_stamp = time.strftime("%Y-%m-%d_%Hh%Mm%Ss")
    # the file name for the generated inventory.
    #   this will start with two underscores for easy sorting 
    #   within the directory and also contain the directory's name 
    #   in its own file name in case the inventory becomes disassociated.
    inventory_name = (inventory_dir + '\\__Inventory_' + modified_path + \
        '___' + str(time_stamp) + '.csv')
    
    # creates new file for inventory
    with open(inventory_name, 'w+') as outfile:
        # fills in accumulator
        outfile.writelines(inventory_acc)
    # all done!
    outfile.close()
    # print that this inventory has been completed
    print('%s\nCOMPLETED:\nInventory saved as\n%s\n%s' % (('{:^}'.format('='*80)), \
        inventory_name, ('{:^}'.format('='*80))))


def main():
#    file_dir, inventory_dir, checksum_type, include_true_exclude_false, \
#        file_types, file_type_string = take_inputs()

    # hardcoding inputs for now, otherwise it's just annoying to do every time
    file_dir = '\\\\?\\S:\\Departments\\Digital Services\\Internal\\DigiPres\\Checksum_Inventory_Generation\\Contained_Test'
    inventory_dir = '\\\\?\\S:\\Departments\\Digital Services\\Internal\\DigiPres\\Checksum_Inventory_Generation\\Inventories'
    checksum_type = 'MD5'
    include_true_exclude_false = False
    file_type_string = 'tif jpg mov mp3 mp4 txt'
    file_types = file_type_string.split()
    modified_path, first_inventory_of_dir, read_inventory, set_first_dir, \
        dict_first_dir, set_first_dir_names, set_matches = \
        check_for_inventories(file_dir, inventory_dir)
    file_name_acc, not_selected_acc, total_to_do, total_not_selected = file_name_inventory(file_dir, include_true_exclude_false, file_type_string, file_types)
    inventory_acc_recursive, leftover_files = recursive_by_file(file_dir, \
        include_true_exclude_false, file_type_string, file_types, \
        checksum_type, inventory_acc, first_inventory_of_dir, read_inventory, \
        set_first_dir, dict_first_dir, set_first_dir_names, set_matches, file_name_acc, not_selected_acc, total_to_do, total_not_selected)
    inventory_acc_total = file_in_inv_not_dir(inventory_acc_recursive, \
        leftover_files)
    write_file(inventory_dir, modified_path, inventory_acc_total)


if __name__ == '__main__':
    # subprocess.Popen('cmd /u', shell=True)
    line_break = ('{:^}'.format('-'*80))
    inventory_acc = 'sep=`\nProcessingTimeStamp`FilePath`RootDirectory`FileName\
    `Checksum`ChecksumType`NewFile?`ChecksumMatchesPast?`FileCorrupt?\n'
    main()

