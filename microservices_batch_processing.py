#!/usr/bin/env python

import glob, os, subprocess, datetime, time, sys, csv, ast


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
4. Check mediainfo metadata against image / audio file standards
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
    # select dir of files to process
    file_dir_input = ''
    # while there is no file dir path selected
    while '\\' not in file_dir_input:
        # the directory you want to work with
        file_dir_input = input('CONTENT FILE DIRECTORY:\nPaste the *FULL* path to the folder directory \nthat you would like to process:\n> ')
    # add '\\?\' to make universal path\
    #   (combat character limit for long paths)
    file_dir = '\\\\?\\%s' % file_dir_input

    # select dir for outfile
    inventory_dir_input = ''
    # while there is no inventory outfile path selected
    while '\\' not in inventory_dir_input:
        # the directory you want to work with
        inventory_dir = input('\nINVENTORY DIRECTORY:\nPaste the *FULL* path to the folder directory \nthat you would like to save the inventory in:\n> ')
    # add '\\?\' to make universal path (combat character limit for long paths)
    inventory_dir = '\\\\?\\%s' % file_dir_input

    # select checksum algorithm
    # existing checksum options that you can pick from
    checksum_options = ['SHA1', 'MD5', 'SHA256']
    checksum_type = (input('\nCHECKSUM SELECTION:\nSelect your checksum type!\nOptions are [MD5], [SHA1], or [SHA256].\nNOTE: If you do not select a valid option, default is set to [MD5].\n> '))\
        .upper().replace('[', '').replace(']', '')
    if checksum_type not in checksum_options:
        # if you didn't select a valid checksum, it'll go MD5.
        print('Not a valid choice. Defaulting to MD5 checksums.')
        checksum_type = 'MD5'

    # choose whether to include or exclude files based on ext
    file_type_include_exclude = ''
    while file_type_include_exclude == '':
        # file type on exclusionary or inclusionary basis
        include_true_exclude_false = True
        file_type_include_exclude = input('\nFILE TYPE INCLUDE / EXCLUDE:\nWould you like to [I]NCLUDE certain file types\nor [E]XCLUDE certain file types?\nNOTE: If you do not select to include or exclude,\ndefault is set to INCLUDE all files.\n> ')\
            .upper().replace('[', '').replace(']', '')
        if file_type_include_exclude == "E":
            include_true_exclude_false = False
        elif file_type_include_exclude not in ("I", "E"):
            print('Not a valid choice. Defaulting to INCLUDE.')

        # file types that you'd like to process
        file_type_string = ' '
        while file_type_string == ' ':
            file_type_string = input('\nFILE TYPE SELECTION:\nList file types that you would like to process separated by a space\n(ex "pdf jpg xml docx")\nNOTE: If you do not input a file type, every file in the folder\nwill be processed.\n> ')
            if (include_true_exclude_false == False) and (file_type_string == ''):
                print("ERROR, you can't exclude all files... Let's try that again...\n")
    # separate file types from one string into a list
    file_types = file_type_string.split()
    
    return file_dir, inventory_dir, checksum_type, include_true_exclude_false,\
        file_types, file_type_string

# determine whether there are existing inventories of the same directory
def check_for_inventories(file_dir, inventory_dir):
    latest_inventory = ''
    read_inventory = []
    first_inventory_of_dir = False
    set_first_dir = set()
    set_first_dir_names = set()
    set_matches = set()
    dict_first_dir = {}
    # modify path for file name to account for invalid characters
    modified_path = (file_dir.replace('\\\\?\\', "").replace('\\', "'").replace(":", "'"))
    # see if previous inventory exists by accessing it.
    #   if it doesn't, don't attempt to compare inventories
    try:
        latest_inventory = str(max(glob.iglob(inventory_dir + '\\__Inventory_' + modified_path + '__*.csv'),key=os.path.getmtime))
    except (OSError, ValueError): 
        # this is the first inventory done for this dir
        first_inventory_of_dir = True
    # if it exists, open it, turn it into a list
    if latest_inventory != '':
        with open(latest_inventory, 'r', encoding='utf-8') as old_inventory:
            read_inventory = list(csv.reader(old_inventory, delimiter='`'))
        # indicate it's not the first inventory
        first_inventory_of_dir = False
    else:
        # this is the first inventory done for this dir
        first_inventory_of_dir = True
    # if not the first inventory of this dir
    if first_inventory_of_dir == False:
        # read row by row
        for row in read_inventory:
            # if there's a full line
            #   (which would indicate that there's a file represented)
            if len(row) > 4:
                # add info to dict and 2 sets
                dict_first_dir[(row[1])] = row[5]
                set_first_dir.add((row[1], row[5]))
                set_first_dir_names.add((row[1]))
            else:
                # if there's a file that previously was listed as missing,
                #   this will catch it
                set_first_dir_names.add((row[1]))
    return modified_path, first_inventory_of_dir, read_inventory, set_first_dir, dict_first_dir, set_first_dir_names, set_matches


# determine which files to process based on previous inputs
#   create outfile with these files
def file_name_inventory(file_dir, include_true_exclude_false, file_type_string, file_types):
    time_stamp = time.strftime("%Y-%m-%d_%Hh%Mm%Ss")
    file_name_acc = {}
    file_count_acc = 0
    file_name_acc_as_string = ''
    not_selected_acc = set()
    not_selected_as_string = ''
    # for each folder and file within that directory
    print('%s\nDETERMINING FILES TO PROCESS IN\n%s\nSTARTED AT: %s\n%s' % (('{:^}'.format('='*80)), file_dir, time_stamp, ('{:^}'.format('='*80))))
    for root, dirs, files in os.walk(file_dir):
        for folder in dirs:
            dir_name = folder
        for name in files:
            name_with_path = (os.path.join(root, name))
            try:
                # select & acc file types to process based on previous input
                if name.lower().endswith(tuple(file_types)) == include_true_exclude_false or file_type_string == '' and '._' not in name:
                    file_count_acc +=1
                    file_name_acc[file_count_acc] = (name_with_path)
                    file_name_acc_as_string += ('%s: %s\n' % (file_count_acc, name_with_path))
                # if not selected, acc to separate variable
                else:
                    not_selected_acc.add((name_with_path))
                    not_selected_as_string += ('%s\n' % name_with_path)
            except:
                print('---WARNING, ERROR DETERMINING FILES TO PROCESS:\n   %s' % (name_with_path))
                not_selected_acc.add((name_with_path))
                not_selected_as_string += ('%s\n' % name_with_path)
                pass
    total_to_do = len(file_name_acc)
    total_not_selected = len(not_selected_acc)
    # create file with file names.
    #   this is used as a record, backup, and checkpoint source
    with open('S:\\Departments\\Digital Services\\Internal\\DigiPres\\Checksum_Inventory_Generation\\Inventories\\File_Name_Acc.txt', 'w', encoding='utf-8') as file_name_acc_file:
        # fills in accumulator
        file_name_acc_file.writelines('%s\n\n%s\n\n%s' % (file_name_acc_as_string, ('='*80), not_selected_as_string))
        
    # all done!
    file_name_acc_file.close()
    print('%s\nFINISHED DETERMINING FILES AT: %s\n%s' % (('{:^}'.format('='*80)), time_stamp, ('{:^}'.format('='*80))))
    return file_name_acc, not_selected_acc, total_to_do, total_not_selected

# this is the meat of the recursive file processing
def recursive_by_file(file_dir, include_true_exclude_false, file_type_string, file_types, checksum_type, inventory_acc, first_inventory_of_dir, read_inventory, set_first_dir, dict_first_dir, set_first_dir_names, set_matches, file_name_acc, not_selected_acc, total_to_do, total_not_selected, inventory_dir, modified_path, checkpoint_inventory_name, previous_checksums):
    checkpoint = 0
    old_root = ''
    # while there are still files left unprocessed
    while checkpoint < total_to_do:
        # when checkpoint accumulator reaches a multiple of 10000, update outfile
        if (checkpoint % 10000 == 0) or (checkpoint == 0):
            checkpoint_save(checkpoint, checkpoint_inventory_name, inventory_acc)
            inventory_acc = ''
        checkpoint += 1
        # os.walk order is consistent: checkpoint == file_name_acc
        name_with_path = file_name_acc[checkpoint]
        set_matches.add((name_with_path))
        time_stamp = time.strftime("%Y-%m-%d_%Hh%Mm%Ss")
        processing_progress = ''
        processing_error = ' '
        try:
            # reset file-specific variables for every file
            new_file = ''
            checksum_consistent = ''
            file_error = []
            file_error_count = 0
            
            # processing_progress to indicate point of failure if script fails
            processing_progress = 'IDENTIFYING FILE NAME AND DIRECTORY'
            # split the portions of the file name to separate the extension
            root, name = os.path.split(name_with_path)
            # indicate dir being processed
            if str(root) != str(old_root):
                print('\n%s\nCURRENTLY PROCESSING:\n%s' % (line_break, root))
            old_root = str(root)

            file_ext = os.path.splitext(name)[-1]
            checksum = ' '
            processing_progress = 'CALCULATING CHECKSUM'
            new_file, checksum, checksum_consistent, file_error, file_error_count, inventory_acc, set_matches = checksums(name, name_with_path, checksum_type, inventory_acc, first_inventory_of_dir, read_inventory, new_file, checksum_consistent, file_error, file_error_count, file_ext, set_first_dir, dict_first_dir, set_first_dir_names, set_matches, previous_checksums)

            # find errors in mediainfo for images and audio
            # included extensions currently set to media files
            mediainfo_extensions = ('jpg', 'jp2', 'tif', 'tiff', 'wav', 'mov')
            if name.lower().endswith(mediainfo_extensions):
                processing_progress = 'RUNNING MEDIAINFO'
                file_error_count, file_error = mediainfo(name, name_with_path, file_error_count, file_error)
            processing_progress = 'ADDING TO INVENTORY'
        
        # indicate (human readable) point of error
        except:
            processing_error = ('Error in processing while %s' % (processing_progress.lower()))
            print('---WARNING, ERROR IN PROCESSING WHILE %s:\n   %s' % (processing_progress, name_with_path))
            # if error, save current work
            checkpoint_save(checkpoint, checkpoint_inventory_name, inventory_acc)
        # accumulate file information for csv
        inventory_acc = accumulation(inventory_acc, time_stamp, name_with_path, root, name, processing_error, checksum, checksum_type, new_file, checksum_consistent, file_error, file_error_count, checkpoint)
        # delete file out of dict
        del file_name_acc[checkpoint]
    # after all files have been processed, save.
    checkpoint_save(checkpoint, checkpoint_inventory_name, inventory_acc)

    # determine which files were in previous inventory but not dir
    leftover_files = set_first_dir_names - (set_matches|not_selected_acc)

    return inventory_acc, leftover_files, checkpoint

# saves information to outfile
def checkpoint_save(checkpoint, checkpoint_inventory_name, inventory_acc):
    # creates/appends+ file for temp inventory
    with open(checkpoint_inventory_name, 'a+', encoding='utf-8') as temp_outfile:
        # fills in accumulator
        temp_outfile.writelines(inventory_acc)
        # [[maybe put not selected files here too, copy to sep variable, reset to set(). this way i can still add everything together to compare difference in files from previous inventory in case of failure]]
        temp_outfile.writelines(not_selected_inventory_acc)
    # reset inventory_acc and not_selected_inventory_acc
    inventory_acc = ''
    not_selected_inventory_acc = ''
    # creates/appends+ file for all previous checksums,
    #   allowing to compare against checksums in all dirs
    with open("\\\\?\\C:\\Users\\wschlin\\Desktop\\previous-checksums.txt", 'a+', encoding='utf-8') as previous_checksums_file:
        previous_checksums_file.writelines(str(new_checksums))
    previous_checksums.update(new_checksums)
    new_checksums = {}

    
    print('\n%s\nCHECKPOINT REACHED:\nInventory saved after %s files as\n%s\n%s' % (('{:^}'.format('='*80)), checkpoint, checkpoint_inventory_name, ('{:^}'.format('='*80))))

# run mediainfo on designated files
def mediainfo(name, name_with_path, file_error_count, file_error):
    info_dict = {}
    mediainfo_dict = {}
    desired_fields = ['FileExtension', 'InternetMediaType', 'Format/Extensions', 'Compression_Mode', 'SamplingRate']
    # look at mediainfo technical metadata of image files
    mediainfo_output_full = (subprocess.check_output(('MediaInfo -f --Language=raw "' + name_with_path +'"'), shell=True))
    # format output
    mediainfo_full_format = (str(mediainfo_output_full).replace('  ', '').replace('\\r\\n', '\n').replace("['", "").replace("']", "").split('\n'))
    # format each line into a field and value
    #   (unfortunately yes, this is the most efficent way to do this)
    for output_line in mediainfo_full_format:
        try:
            field, value = (output_line.split(': ')).strip()
        except:
            field = (output_line.split(': ')[0]).strip()
            value = (output_line.split(': ')[-1]).strip()
        info_dict[field] = value
    # add previously specified desired fields and associated values to dict
    for desired in desired_fields:
        try:
            mediainfo_dict[desired] = (info_dict[desired])
        except:
            mediainfo_dict[desired] = ''
            pass 

    # validate mediainfo data based on expected values
    # validate file extension
    if (mediainfo_dict['FileExtension']).lower() not in mediainfo_dict['Format/Extensions']:
        file_error_count += 1
        file_error.append('File extension not expected value.')
        print('---WARNING, IMAGE FILE EXTENSION NOT EXPECTED:\n   %s' % (name_with_path))
    '''
    # validate lossless compression [[not currently in use]]
    if mediainfo_dict['Compression_Mode'] is not ('lossless' or 'Lossless' or ''):
        file_error_count += 1
        file_error.append('Compression is not lossless.')
        print('---WARNING, FILE IS NOT LOSSLESS:\n   %s' % (name_with_path))
    '''
    # validate audio sampling rate
    if mediainfo_dict['SamplingRate'] is not '':
        if (int(mediainfo_dict['SamplingRate']) <= int('44100')):
            file_error_count += 1
            file_error.append('Sampling rate is incorrect.')
            print('---WARNING, AUDIO SAMPLING RATE INCORRECT:\n   %s' % (name_with_path))
    
    return file_error_count, file_error

# run checksums
def checksums(name, name_with_path, checksum_type, inventory_acc, first_inventory_of_dir, read_inventory, new_file, checksum_consistent, file_error, file_error_count, file_ext, set_first_dir, dict_first_dir, set_first_dir_names, set_matches, previous_checksums):
    file_found_error = ''
    checksum = ''
    try:
        run_checksum = subprocess.check_output(('certUtil -hashfile "' + name_with_path + '" ' + checksum_type), shell=True)
    # if error, save and wait for human input (rudimentary "pause", basically)
    except:
        checkpoint_save(checkpoint, checkpoint_inventory_name, inventory_acc)
        file_found_error = input("You have lost network connectivity. Press enter to continue processing")
        pass
    # split the returned checksum string by line
    checksum_split = str(run_checksum).split('\\r\\n')
    # take only the second line (which is the checksum)
    checksum = checksum_split[1]

    new_file = ' '
    if ((inventory_acc.count('"%s"' % (checksum)) > 0) and checksum is not '') or checksum in previous_checksums or checksum in new_checksums:
        # if checksum appears more than once
        checksum_consistent += 'Duplicate checksum.'
        # print error in shell
        print('---WARNING, CHECKSUM APPEARS MORE THAN ONCE:\n   %s' % (name_with_path))
    else:
        new_checksums[checksum] = name_with_path
    # if the file has been processed previously
    if name_with_path in set_first_dir_names:
        new_file = ' '
        # if the checksums match
        if dict_first_dir[name_with_path] in checksum:
            # they are consistent
            checksum_consistent += ' '
        else:
            # if the checksums don't match, there's an error
            checksum_consistent += 'Inconsistent checksum.'
            # print error in shell
            print('---WARNING, CHECKSUM DOES NOT MATCH:\n   %s' % (name_with_path))
    else:
        new_file = 'First inventory of this file'
        checksum_consistent += ' '
    return new_file, checksum, checksum_consistent, file_error, file_error_count, inventory_acc, set_matches

# if the file is in a previous inventory but no longer in dir
def file_in_inv_not_dir(inventory_acc, leftover_files):
    inventory_acc_total = ''
    for leftover in leftover_files:
        if (('`"%s"`"File is missing or cannot be accessed"\n' % (leftover)) in inventory_acc) == False and leftover not in ('FilePath', ""):
            time_stamp = time.strftime("%Y-%m-%d_%Hh%Mm%Ss")
            inventory_acc_total += ('"%s"`"%s"`"File is missing or cannot be accessed"\n'% (time_stamp, (leftover)))
            print('---WARNING, FILE IS MISSING OR CANNOT BE ACCESSED:\n   %s' % (leftover))
    return inventory_acc_total


# accumulate all inventory information
def accumulation(inventory_acc, time_stamp, name_with_path, root, name, processing_error, checksum, checksum_type, new_file, checksum_consistent, file_error, file_error_count, checkpoint):
    if file_error != []:
        error_grouping = ("%s Error(s): %s" % (file_error_count, (' '.join(file_error))))
    else:
        error_grouping = ''
    # character ` is used for csv separation as
    #    an arbitrary char to account for , and . appearing in file names
    inventory_acc += ('"%s"`"%s"`"%s"`"%s"`"%s"`"%s"`"%s"`"%s"`"%s"`"%s"`"%s"\n' % (time_stamp, name_with_path, root, name, processing_error, checksum, checksum_type, new_file, checksum_consistent, error_grouping, checkpoint))
    return inventory_acc

'''
# this was just used for testing. currently saving but will be gone for longterm use
def write_file(inventory_dir, modified_path, checkpoint_inventory_name, start_time_stamp):
    # the file name for the generated inventory
    #   this will start with two underscores for easy sorting 
    #   within the directory and also contain the directory's name 
    #   in its own file name in case the inventory becomes disassociated.
    inventory_name = (('%s\\__Inventory_%s___%s.csv')% (inventory_dir, modified_path, str(start_time_stamp)))
    print('inventory name:\n%s\n\n' % inventory_name)
    print('mod path:\n%s\n\n' % modified_path)

    # creates new file for inventory
    with open(inventory_name, 'w+', encoding='utf-8') as outfile:
        # fills in accumulator
        outfile.writelines(inventory_acc)
    # all done!
    outfile.close()

    print('checkpoint inventory name:\n%s\n\n' % checkpoint_inventory_name)
    print('inventory name:\n%s\n\n' % inventory_name)
    os.rename(checkpoint_inventory_name, inventory_name)
'''

# csv accumulator for files that have not been selected for processing
def not_selected_inventory(not_selected_acc):
    not_selected_inventory_acc = ''
    for name_with_path in not_selected_acc:
        time_stamp = time.strftime("%Y-%m-%d_%Hh%Mm%Ss")
        root, name = os.path.split(name_with_path)
        not_selected_inventory_acc += ('"%s"`"%s"`"%s"`"%s"`"Not selected"``\n' % (time_stamp, name_with_path, root, name))
    return not_selected_inventory_acc


def main():
# hardcoded inputs for now, otherwise it's just annoying to do every time
    # file_dir, inventory_dir, checksum_type, include_true_exclude_false, file_types, file_type_string = take_inputs()
    start_time_stamp = time.strftime("%Y-%m-%d_%Hh%Mm%Ss")
    #file_dir = '\\\\?\\S:\\Departments\\Digital Services\\Internal\\DigiPres\\Checksum_Inventory_Generation\\Contained_Test'
    #file_dir = '\\\\?\\R:\\Projects\\Glacier-ReadyForUpload\\FPoC2013'
    file_dir = '\\\\?\\R:\\Newspapers'
    inventory_dir = '\\\\?\\S:\\Departments\\Digital Services\\Internal\\DigiPres\\Checksum_Inventory_Generation\\Inventories'
    checksum_type = 'MD5'
    include_true_exclude_false = True
    #file_type_string = ''
    file_type_string = 'jp2 jpg tif png mp3 gif jpe wav mp4 mov hdr svg vob m4v mpg'
    file_types = file_type_string.split()
    
    # get previous checksums from all previous inventories
    new_checksums = {}
    with open("\\\\?\\S:\\Departments\\Digital Services\\Internal\\DigiPres\\Checksum_Inventory_Generation\\Inventories\\previous_checksums.txt", 'r+', encoding='utf-8') as previous_checksums_file:
        previous_checksums = ast.literal_eval(previous_checksums_file.read())

    # check for previous inventories of dir, return info
    modified_path, first_inventory_of_dir, read_inventory, set_first_dir, dict_first_dir, set_first_dir_names, set_matches = check_for_inventories(file_dir, inventory_dir)

    # create inventory names
    checkpoint_inventory_name = ('%s\\__Inventory_%s___TEMPINVENTORY.csv' % (inventory_dir, modified_path))
    inventory_name = (('%s\\__Inventory_%s___%s.csv')% (inventory_dir, modified_path, str(start_time_stamp)))

    # create inventory of all file names that will be processed
    file_name_acc, not_selected_acc, total_to_do, total_not_selected = file_name_inventory(file_dir, include_true_exclude_false, file_type_string, file_types)

    # process files, return inventory
    inventory_acc_recursive, leftover_files, checkpoint = recursive_by_file(file_dir, include_true_exclude_false, file_type_string, file_types, checksum_type, inventory_acc, first_inventory_of_dir, read_inventory, set_first_dir, dict_first_dir, set_first_dir_names, set_matches, file_name_acc, not_selected_acc, total_to_do, total_not_selected, inventory_dir, modified_path, checkpoint_inventory_name, previous_checksums)
    
    # manage files not included for processing
    inventory_acc_not_included = file_in_inv_not_dir(inventory_acc_recursive, leftover_files)
    not_selected_inventory_acc = not_selected_inventory(not_selected_acc)
    inventory_acc_not_processed = inventory_acc_not_included + not_selected_inventory_acc
    not_processed_acc_total = inventory_acc_not_processed.count('\n') + checkpoint
    checkpoint_save(not_processed_acc_total, checkpoint_inventory_name, inventory_acc_total)
    
    # finish inventory
    os.rename(checkpoint_inventory_name, inventory_name)
    time_stamp = time.strftime("%Y-%m-%d_%Hh%Mm%Ss")
    print('\n%s\nCOMPLETED:\nInventory saved as\n%s\nCOMPLETED AT: %s\n%s' % (('{:^}'.format('='*80)), inventory_name, time_stamp, ('{:^}'.format('='*80))))


if __name__ == '__main__':
    # subprocess.Popen('cmd /u', shell=True)
    line_break = ('{:^}'.format('-'*80))
    inventory_acc = 'sep=`\nProcessingTimeStamp`FilePath`RootDirectory`FileName``Checksum`ChecksumType`NewFile?`ChecksumMatchesPast?`FileCorrupt?`FileNumber\n'
    main()

