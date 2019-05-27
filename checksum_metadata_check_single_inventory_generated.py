#!/usr/bin/env python

import glob, os, subprocess, datetime, time, sys, csv


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
    * Whether there are any duplicate checksums
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


def run_mediainfo(filepath):
    # run mediainfo stuff
    # subprocess.check_output('mediainfo -f %s ' %) 
    # return mediainfo_output    


def parse_mediainfo_output(output, file_path):
    # list_fields_we_care_about
    # set(filetype, field, expected_value)
    # get mediainfo's thoughts on file type ("internet_media_type")
    # iterate through fields we care about
        # make a set of mediainfo output set(filetype, field_we_care_about, expected_value)

        # compare .endswith() to mediainfo output
        # 
    # 
    # if output.filekind == "audio":
    #     errors = check_audio_errors(output)
    if output.filekind == "image":
        return file_extension, internet_media_type, extensions_usually_used, compression_mode


def mediainfo_images(name, name_with_path, file_error_count, file_error):
    # look at mediainfo technical metadata of image files
    file_error_count_images = 0
    file_error_images = []
    # file_extension = (subprocess.check_output(('MediaInfo \
    #     --Output=General;%FileExtension% "' + name_with_path +'"'), \
    #     shell=True))
    # internet_media_type = (subprocess.check_output('MediaInfo \
    #     --Output=General;%InternetMediaType% "' + name_with_path +'"', \
    #     shell=True))                                                             
    # extensions_usually_used = (subprocess.check_output('MediaInfo \
    #     --Output=General;%Format/Extensions% "' + name_with_path +'"', \
    #     shell=True))                                                                 
    # compression_mode = (subprocess.check_output('MediaInfo \
    #     --Output=Image;%Compression_Mode% "' + name_with_path +'"', \
    #     shell=True))       
    mediainfo_output = run_mediainfo(filepath)
    file_extension, internet_media_type, extensions_usually_used, compression_mode = parse_mediainfo_output(mediainfo_output)
    internet_media_type_formatted = (str(internet_media_type)\
        .split('/'))[0].strip("\\b'")
    file_extension_formatted = (str(file_extension)).replace("b'", "")\
        .replace("\\r\\n'", "")
    extensions_usually_used_formatted = \
        (str(extensions_usually_used)).replace("b'", "")\
        .replace("\\r\\n'", "")
    compression_mode_formatted = (str(compression_mode))\
        .lower().strip().replace("b'", "").replace("\\r\\n'", "")
    if internet_media_type_formatted != 'image':
        file_error_count_images += 1
        file_error_images.append("File should be an image but isn't.")
        print('---WARNING, IMAGE FILE IS NOT IMAGE:\n   %s\n' % \
            (name_with_path))
    if file_extension_formatted not in extensions_usually_used_formatted:
        file_error_count_images += 1
        file_error_images.append('File extension not expected value.')
        print('---WARNING, IMAGE FILE EXTENSION NOT EXPECTED:\n   %s\n' % \
            (name_with_path))
    if compression_mode_formatted != 'lossless':
        file_error_count_images += 1
        file_error_images.append('Compression is not lossless.')
        print('---WARNING, IMAGE FILE IS NOT LOSSLESS:\n   %s\n' % \
            (name_with_path))
    return file_error_count_images, file_error_images

def mediainfo_audio(name, name_with_path, file_error_count, file_error):
    #look at mediainfo technical metadata of wav files
    file_error_count_audio = 0
    file_error_audio = []
    file_error_count_audio = 0
    file_error_audio = []
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
    extensions_usually_used_formatted = (str(extensions_usually_used))\
        .replace("b'", "").replace("\\r\\n'", "")
    sampling_rate_formatted = (str(sampling_rate))\
        .lower().strip().replace("b'", "").replace("\\r\\n'", "")
    if internet_media_type_formatted != 'audio':
        file_error_count_audio += 1
        file_error_audio.append("File should be a audio but isn't.")
        print('---WARNING, AUDIO FILE IS NOT AUDIO:\n   %s\n' % \
            (name_with_path))
    if file_extension_formatted not in extensions_usually_used_formatted:
        file_error_count_audio += 1
        file_error_audio.append('File extension not expected value.')
        print('---WARNING, AUDIO FILE EXTENSION NOT EXPECTED:\n   %s\n' % \
            (name_with_path))
    if sampling_rate_formatted != '44100':
        file_error_count_audio += 1
        file_error_audio.append('Sampling rate is incorrect.')
        print('---WARNING, AUDIO SAMPLING RATE INCORRECT:\n   %s\n' % \
            (name_with_path))
    return file_error_count_audio, file_error_audio
    
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
    file_dir = '\\\\?\\R:\\Projects\\Glacier-ReadyForUpload\\FPoC2013'
    inventory_dir = '\\\\?\\S:\\Departments\\Digital Services\\Internal\\DigiPres\\Checksum_Inventory_Generation\\Inventories'
    checksum_type = 'MD5'
    include_true_exclude_false = False
    file_type_string = 'docx xlsx'
    file_types = file_type_string.split()
    modified_path, first_inventory_of_dir, read_inventory, set_first_dir, \
        dict_first_dir, set_first_dir_names, set_matches = \
        check_for_inventories(file_dir, inventory_dir)
    inventory_acc_recursive, leftover_files = recursive_by_file(file_dir, \
        include_true_exclude_false, file_type_string, file_types, \
        checksum_type, inventory_acc, first_inventory_of_dir, read_inventory, \
        set_first_dir, dict_first_dir, set_first_dir_names, set_matches)
    inventory_acc_total = file_in_inv_not_dir(inventory_acc_recursive, \
        leftover_files)
    write_file(inventory_dir, modified_path, inventory_acc_total)


if __name__ == '__main__':
    # subprocess.Popen('cmd /u', shell=True)
    line_break = ('{:^}'.format('-'*80))
    inventory_acc = 'sep=`\nProcessingTimeStamp`FilePath`RootDirectory`FileName\
    `Checksum`ChecksumType`NewFile?`ChecksumMatchesPast?`FileCorrupt?\n'
    main()


#
'''
these are the directories I've been running it on locally, here for easy ref

file_dir = '\\\\?\\S:\\Departments\\Digital Services\\Internal\\DigiPres\\Checksum_Inventory_Generation\\Contained_Test'
inventory_dir = '\\\\?\\S:\\Departments\\Digital Services\\Internal\\DigiPres\\Checksum_Inventory_Generation\\Inventories'
checksum_type = 'MD5'
include_true_exclude_false = True
file_type_string = ''

    file_dir = '\\\\?\\R:\\Projects\\Glacier-ReadyForUpload\\FPoC2013'
    inventory_dir = '\\\\?\\S:\\Departments\\Digital Services\\Internal\\DigiPres\\Checksum_Inventory_Generation\\Inventories'
    checksum_type = 'MD5'
    include_true_exclude_false = False
    file_type_string = 'docx xlsx'
    
\\\\?\\S:\\Departments\\Digital Services\\Internal\\DigiPres\\Checksum_Inventory_Generation\\Contained_Test

\\\\?\\S:\\Departments\\Digital Services\\Internal\\DigiPres\\Checksum_Inventory_Generation\\Inventories

# below is the original work, pre-refactoring. This is here for reference, and will be removed later:

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
'''