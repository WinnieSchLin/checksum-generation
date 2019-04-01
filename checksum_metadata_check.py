'''
Winnie Schwaid-Lindner - v.01 of file renaming and inventory script.

1. Ask the root directory, inventory directory, hash algorithm, and which file types to process before calculating an individual file's checksum according to the submitted parameters.
2. Check to see if image files are valid type
3. Check mediainfo metadata against image file standards, if applicable
4. Calculate the checksum
5. Look into past inventories and see whether the checksum matches or if the file is new
6. Determine whether the file is valid and decodable
7. In future - will compare mediainfo metadata fields to predicted file specs to determine if file is corrupted while still openable.
8. Produce a csv inventory of all the file names in each directory with the fields:
    * Time stamp of file processed
    * Full file path
    * Directory that the file is in
    * File name
    * Checksum
    * Checksum algorithm
    * Whether the file is being processed by the script for the first time, which would indicate a new file (Boolean value)
    * Whether the most recently generated checksum matches a past generated checksum if the file is not new (compares checksum to past inventory, this is also Boolean)
    * Whether the file is valid according to type
    * In future - tell whether the file is valid according to mediainfo metadata matching with expected metadata
'''
import glob, os, subprocess, datetime, time, sys, imghdr, csv, os.path

# G:\Snakes\Test_Documents\Contained_Test
# G:\Snakes\Test_Documents\Inventories

file_dir = ''
while '\\' not in file_dir:
    file_dir = input('CONTENT FILE DIRECTORY:\nPaste the *FULL* path to the folder directory that you would like to process:\n> ') # the directory you want to work with

inventory_dir = ''
while '\\' not in inventory_dir:
    inventory_dir = input('INVENTORY DIRECTORY:\nPaste the *FULL* path to the folder directory that you would like to save the inventory in:\n> ') # the directory you want to work with

today = datetime.date.today()
checksum_options = ['SHA1', 'MD5', 'SHA256']
checksum_type = (input('Select your checksum type! Options are "MD5", "SHA1", or "SHA256". Default is set to "MD5".\n> ')).upper()
if checksum_type not in checksum_options: # if you didn't select a valid checksum, it'll go MD5.
    print('Your choice is not on the list. Defaulting to MD5 checksums.')
    checksum_type = 'MD5'

file_type_string = input('List file types that you would like to process separated by a space (ex "pdf jpg xml docx")\nNOTE: If you do not input a file type, every file in the folder will be processed.\n> ')
file_types = file_type_string.split() # separate file types from one string into a list           
latest_inventory = ''
read_inventory = []
first_inventory_of_dir = False

for root, dirs, files in os.walk(file_dir): # for each folder and file within that directory
    for folder in dirs:
        dir_name = folder
        print('currently processing', dir_name)
    inventory_acc = 'sep=`\nProcessingTimeStamp`FilePath`RootDirectory`FileName`Checksum`ChecksumType`NewFile?`ChecksumMatchesPast?`FileCorrupt?\n' # reset for every dir
    modified_path = (root.replace('\\', "'").replace(":", "'")) # making path for file name
    try:
        latest_inventory = str(max(glob.iglob(inventory_dir + '\\__Inventory_' + modified_path + '__*.csv'),key=os.path.getmtime))
    except (OSError, ValueError):
        stop_this = ''
    if latest_inventory != '':
        old_inventory = open(latest_inventory)
        read_inventory = list(csv.reader(old_inventory, delimiter='`'))
        first_inventory_of_dir = False
    else:
        first_inventory_of_dir = True
        
    for name in files:
        if name.endswith(tuple(file_types)) or file_type_string == '': # select file types to process
            new_file = '' # reset for every file
            checksum_consistent = '' # reset for every file
            name_without_checksum = '' # reset for every file
            file_error = ''
            name_with_path = (os.path.join(root, name))
            file_list = name.split('.') # split the portions of the file name to separate the extension
            file_ext = file_list[-1]
            file_name_parts = [file_list[0:-1], file_ext]
            name_without_checksum = '.'.join(map(str, file_name_parts))
            file_name_with_checksum = name
            run_checksum = subprocess.check_output(('certUtil -hashfile "' + name_with_path + '" ' + checksum_type), shell=True)
            checksum_split = run_checksum.decode().split('\r\n') # split the returned string by line
            checksum = checksum_split[1] # take only the second line, which is the checksum
            time_stamp = time.strftime("%Y-%m-%d_%Hh%Mm%Ss")
            new_file = 'Yes'
            
            if first_inventory_of_dir == False:
                for row in read_inventory:
                    if name in row[1]:
                        new_file = ' '
                        if checksum in str(row[4]):
                            checksum_consistent = ' '
                        else:
                            checksum_consistent = 'ERROR'
                            print('---WARNING, CHECKSUM DOES NOT MATCH:\n %s---\n' % (row[1]))
                    if (os.path.isfile(row[1]) == False or os.access(row[1], os.R_OK) == False) and (row[1] != 'FilePath') and (row[1] != ''): # this keeps saying files don't exist. whyyyy?
                        if (('`"%s"`"FILE IS MISSING OR CAN NOT BE ACCESSED"\n' % (row[1])) in inventory_acc) == False:
                            inventory_acc += ('"%s"`"%s"`"FILE IS MISSING OR CAN NOT BE ACCESSED"\n' % (time_stamp, (row[1])))
                            print('---WARNING, FILE IS MISSING OR CAN NOT BE ACCESSED:\n %s---\n' % (row[1]))
            else:
                new_file = 'FIRST INVENTORY OF DIR'
                checksum_consistent = ' '
            if name.endswith("jpg") or name.endswith("tif") or name.endswith("pdf"):
                e = ''
                try:
                    img = imghdr.what(name_with_path)
                    if img == None:
                        file_error = 'ERROR'
                    #print(file_error, name_with_path, 'img == None')
                except:
                    exc = sys.exc_info()
                    file_error = 'ERROR'
                    #print(file_error, name_with_path, exc)
            else:
                file_error = ' '
        inventory_acc += ('"%s"`"%s"`"%s"`"%s"`"%s"`"%s"`"%s"`"%s"`"%s"\n' % (time_stamp, name_with_path, root, name, checksum, checksum_type, new_file, checksum_consistent, file_error)) # an accumulator that adds all inventory information for the .csv
    time_stamp = time.strftime("%Y-%m-%d_%Hh%Mm%Ss")
    inventory_name = (inventory_dir + '\\__Inventory_' + modified_path + '___' + str(time_stamp) + '.csv') # the file name for the generated inventory. This will start with two underscores for easy sorting within the directory and also contain the directory's name in its own file name in case the inventory becomes disassociated.
    old_inventory.close()
    with open(inventory_name, 'w+') as outfile: # creates new file for inventory
        outfile.writelines(inventory_acc) # fills in accumulator
    outfile.close() # all done!
    print('%s inventory completed,\n saved as %s\n' % (root, inventory_name))

