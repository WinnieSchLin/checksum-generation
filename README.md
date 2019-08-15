# Checksum, file readability, and inventory generation 

There are many programs to generate checksums and this isn't an attempt to reinvent the wheel, although part of it probably does. It will generate an inventory (on a directory-by-directory basis, a single inventory for all files, or both), and also has the ability to insert the checksum directly into the file name (if it's desired). Mostly, it was created to form a single inventory that would also use mediainfo to read the file and determine whether the output matches expected values, as we have many files upwards of 20 years old, and are unsure whether they're usable and/or corrupted.

In general, the script will:
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

*Future updates*
* Have mediainfo only run once and parse output instead of running a separate command 
  for each field (hopefully this'll cut down on some time)
* Output inventory every X number of files, so that losing network connection will not 
  result in lost work
* Determine how to have script restart from last saved inventory in case of failure
* Write input options for inventory generation
* Give option for alternative for certUtil
