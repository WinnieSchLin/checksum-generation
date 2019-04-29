# Checksums & Checksums in File Names 

*Knowledge about the collection:*  
It will inform us about the health of the digital collection, storage system and materials themselves - we will be able to tell if checksums are changing and where, and will be able to tell whether there are systemic issues with our storage (corruption), but will also help establish a provenance, as we will be able to see the history of changing checksums every time the file is edited, either intentionally or unintentionally. In addition, the checksum provides a unique value in case we choose a more flexible or broad naming convention strategy, and this will ensure that there won’t accidentally be a duplicate file name generated (for example, if our naming convention called this email ‘Schwaid-Lindner_EmailToScott_2019-03-21.txt’, then we would be in trouble if I sent you more than one email per day. In addition, adding checksums can be added retroactively to files that have been created under a multitude of previous naming conventions, enabling us to gain a very basic level of knowledge and control without having to delve into the context of the file itself, which would be a bit time consuming.
 
*Recovery and Preparing for Data Loss:*  
By having checksums, we will be in a better place to rebound from an inevitable data loss. For example, let’s say a file has accidentally been deleted. Currently, because the backup tapes are written over every few weeks, if you don’t realize that the file is missing before the tapes are rewritten to become a duplicate of the current system (which the file has been deleted from), the file would be permanently lost. Running the script on a set schedule (for example, weekly), will let us know if a file has become problematic or disappears before the backups tapes are erased, and, once we have more significant backups, this would set up a paper trail where you would be able to determine exactly when you would need to recover from, and also what specific files you need to search for.
 
Although it’s certainly been established by many people before me that checksums in general are vital for file management, the incorporation of them into the file name allows for simple and unified storage of this information in the case of data loss that isn’t the file, but is the database, for example. As there are many different database and metadata management systems being used by different units, having the checksum stored with the file is helpful for monitoring the movement of the file, like if a file is copied to a new directory, or shuffled between people in a workflow – it’s an easy way to check without opening each and every file. Eventually it would be great to have content stored in packages with their own corresponding metadata files, but as we’re a little far off from getting that ironed out, this is a great way to do something with our current resources.
 
In addition, because we don’t have a solid grasp on what files are and where they’re stored, this will help aid in the inevitable accident where someone thinks they’re typing in a different window and accidentally renames a file (which you can’t ctrl-z undo, for what it’s worth). By running the checksums on the files, we can see the matchup of what the file used to be called, and that way it’s just a matter of seconds to reverse that accident.
 
*Low risk, low effort, high payout:*  
One of the main benefits to adding a checksum to the end of the file name is that it’s low risk, and low effort. Adding a checksum to the end of file names will not take a huge amount of time, will not take up any additional storage space, and will not require any specialized system or independent computer (checksums can be run on any machine by whomever). Furthermore, just because the checksum is added doesn’t mean it needs to be checked every day, so even if you’re concerned about the expenditure of the electricity being used to process the checksums as an expense, it’s easy to prioritize which files are monitored more closely and should have hashes generated on a different schedule depending on a number of factors, such as root directory or file type. So basically it’s something that doesn’t require a significant expenditure on any level (that I’ve thought of so far, at least), but will prove incredibly valuable in the case of data loss.
 
There are many programs to generate checksums, but I’ve written a script that will insert the checksums into the file name and generate an inventory on a directory-by-directory basis.
In general, the script will:
1. Ask the root directory, inventory directory, hash algorithm, 
   and which file extensions to process on an inclusionary or exclusionary basis
2. Calculate the checksum using certUtil
3. Look into past inventories and see whether the checksum matches, 
   identify duplicate checksums, or whether the file is new to the directory
    * Append checksum to file name, if desired
4. Check mediainfo metadata against image and audio file standards
   (and, in the future LSU's preferred file specs), to determine if file
   has unexpected or incorrect properties while still being valid
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


