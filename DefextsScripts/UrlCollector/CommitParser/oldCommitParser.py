import subprocess
import os
import shutil
import stat
import signal


LINE_SEPARATOR = "-----------"
CLONE_GIT_COMMAND_REPOSITORY_A = "git clone " 

TEMP_FILEPATH = "" # The directory the project should be downloaded to
SCRIPT_FILEPATH = ""
SCRIPT_OUTPUT_NAME = "commits_"

GIT_LOG_COMMAND_A = "git --git-dir="
GIT_LOG_COMMAND_B = "log --all --pretty=format:\"%H\" --relative-date --no-merges --grep=\"fix\" --grep=\"remove\" --grep=\"error\" --grep=\"repair\" --grep=\"issue\" --grep=\"problem\" --grep=\"resolve\"--grep=\"solve\" -i"

HIDDEN_GIT_FOLDER = "/.git"

GIT_LINUX_COUNT_COMMAND = "--name-only | wc -l"


class TimedOutExc ( Exception ):
    output = "Function took too long to complete!"
    pass


def deadline ( timeout, *args ):
  def decorate ( f ):
    def handler ( signum, frame ):
        raise TimedOutExc()

    def new_f ( *args ):

      signal.signal( signal.SIGALRM, handler )
      signal.alarm( timeout )
      return f( *args )
      signa.alarm( 0 )

    new_f.__name__ = f.__name__
    return new_f
  return decorate

 
def main ():
    global SCRIPT_FILEPATH
    global TEMP_FILEPATH
    global SCRIPT_OUTPUT_NAME

    # function main - variables
    proceedAnswer = None
    
    # Get user input to project file file
    while ( ( proceedAnswer != "yes" ) and ( proceedAnswer != "y" ) ):
        commitFilePath = input( "Input a file containing a link to a git repository:\t" ).strip()
        SCRIPT_FILEPATH = input( "Input empty folder to hold script data:\t" ).strip()
        TEMP_FILEPATH = SCRIPT_FILEPATH + "/temp"
        proceedAnswer = input( "Provided filepath is \"" + commitFilePath + "\". This will be downloaded in \"" + TEMP_FILEPATH + "\". Do you wish to proceed?:\t" )
        if ( not os.path.isfile( commitFilePath ) ):
            print( "Input filepath(s) do not point to existing files / folders! Try again!" )
            proceedAnswer = None
        else:
            print( LINE_SEPARATOR + "\n" )
            print( "Proceeding with program..." )
        print( "\n" )

    SCRIPT_OUTPUT_NAME += input( "Input output filename suffix (" + SCRIPT_OUTPUT_NAME + "<suffix>) :\t" )

    # Output content of project list file
    with open( commitFilePath, 'r' ) as projectFile:
        projectList = projectFile.read().splitlines()
        print( "Number of projects found:\t" + str( len( projectList ) ) )
        
        listFileContents( commitFilePath, projectList )
        
        print( LINE_SEPARATOR )

        if( os.path.exists( TEMP_FILEPATH ) ):
            print( "Emptying default script temp directory" )
            subprocess.call( "rm -rf " + TEMP_FILEPATH, shell=True ) # Ensures directory is empty
        else:
            print( "Creating script temp directory" )

        os.makedirs( TEMP_FILEPATH )

        for project in projectList:
            print( LINE_SEPARATOR )
            
            try:
                cloneProject( project ) # clones the project into a temp folder
                processCommits( project )
            except Exception as e:
                print( "Error processing:\t" + project )
                print( e )
            
            resetTempFolder()

# Script functions
def listFileContents ( commitFilePath, projectList ):
    print( "Listing contents of " + commitFilePath )
    print( LINE_SEPARATOR )
    
    for project in projectList:
            print( project )


@deadline( 120 )
def cloneProject ( s ):
        return subprocess.call( CLONE_GIT_COMMAND_REPOSITORY_A + s + " \"" + TEMP_FILEPATH + "\"", shell=True )

# For a given project, filters out commits which modify too many files or
# contain too many insertions / deletions
def filterCommits ():

    global TEMP_FILEPATH
    global SCRIPT_FILEPATH
    
    FILE_TYPE = []
    FILE_TYPE.append( ".kt" )
    FILE_TYPE.append( ".java" )
    FILE_TYPE.append( ".scala" )
    BUFFER_DATA_NAME = "buffer"
    potentialCommits = []
    
    MIN_CHANGED_FILES = 1
    MAX_CHANGED_FILES = 2000 # Maximum amount of files which should be changed
    MAX_MODIFICATIONS = 6  # Maximum of insertions / deletions across files
    
    with open( TEMP_FILEPATH + "/" + BUFFER_DATA_NAME, 'w+' ) as commitFile:
        subprocess.check_call( GIT_LOG_COMMAND_A + "\"" + TEMP_FILEPATH + HIDDEN_GIT_FOLDER + "\" " + GIT_LOG_COMMAND_B , stdout=commitFile, shell=True )
    
        with open( TEMP_FILEPATH + "/" + BUFFER_DATA_NAME, 'r' ) as commitFile:
            commitList = commitFile.read().split( "\n" )
        
            print( "Commits found: " + str( len( commitList ) ) )

            extraCountCommand = GIT_LINUX_COUNT_COMMAND
            previousCommitSymbol = '^'

            # Get what is different from one commit and its next commit
            for x in range( 0 , len( commitList ) - 1 ):
                                    
                changedFiles = subprocess.check_output( "git --work-tree=\"" + TEMP_FILEPATH + "\" --git-dir=\"" + TEMP_FILEPATH + HIDDEN_GIT_FOLDER + "\" diff " + commitList[ x ] + previousCommitSymbol + " " + commitList[ x ] + " " + extraCountCommand, shell=True )
                changedFiles = cleanByteSequence( changedFiles )
            
                # Print commit and how many files it changed
                print( commitList[ x ] + " \tchanged " + changedFiles + " files" )

                # Verified commits are added to a variable to be passed on.
                # Based on the initial git log command, potential candidates
                # are those with one of the following keywords bug, fix, solve,
                # resolve, error, fault, issue, test
                if( int( changedFiles ) >= MIN_CHANGED_FILES and int( changedFiles ) <= MAX_CHANGED_FILES ): # Filter out commits which change too many files or not enough files
                    try:
                        rawFileModifications = cleanByteSequence( subprocess.check_output( "git --work-tree=\"" + TEMP_FILEPATH + "\" --git-dir=\"" + TEMP_FILEPATH + HIDDEN_GIT_FOLDER + "\" diff --numstat " + commitList[ x ] + previousCommitSymbol + " " + commitList[ x ], shell=True ) )
                        FileModifications = rawFileModifications.split( "\n" ) # Split modifications based on newlines
                        
                        sourceCodeFound = False
                        testCodeFound = False
                        quitFilter = False
                        
                        cumulativeModifications = 0
                        for line in FileModifications: # Filter out commits which have too many additions / deletions across its
                                                       # files
                            temp = line.split( "\t" ) # Split data based on tabs (should always have 3 entries per line)
                            languageSpecificFilesFound = False
                            
                            if( len( temp ) == 3 ):
                                if ( ( not "src/main/" in temp[ 2 ] ) and ( not "src/test/" in temp[ 2 ] ) ):
                                    quitFilter = True

                                for file_extension in FILE_TYPE:
                                    if( quitFilter == False ):
                                        if( temp[ 2 ].endswith( file_extension ) ): # Ensures modified code is the appropriate type of file (.java for Java, .kt
                                                                                # for
                                                                                                                                                               # Kotlin,
                                                                                                                                                                                                                                              # etc...)
                                            languageSpecificFilesFound = True
                            
                                            if ( "src/main/" in temp[ 2 ] ):
                                                    if ( sourceCodeFound == False ): # Rough attempt to ensure modified code is within source directory
                                                        cumulativeModifications += int( temp[ 0 ] ) + int( temp[ 1 ] )
                                                        sourceCodeFound = True
                                                    elif ( sourceCodeFound == True ): # Indicates ultiple source files are modified; not allowed
                                                        quitFilter = True         
                                            if ( int( changedFiles ) == 1 or ( "src/test/" in temp[ 2 ] ) ):
                                                testCodeFound = True
                                if( languageSpecificFilesFound == False ):
                                    quitFilter = True

                        if( quitFilter == False ):
                            if( sourceCodeFound and testCodeFound ):
                                if ( ( cumulativeModifications <= MAX_MODIFICATIONS ) and ( cumulativeModifications > 0 ) ):
                                    potentialCommits.append( ( commitList[ x ], changedFiles ) ) # At this point, the commit has passed all the filter tests
                    except Exception as e:
                        print( "ERRRRRORRRRRR:\t" + e ) # Error message here if necessary
    
    return potentialCommits

def cleanByteSequence ( b ):
    return b.decode( "utf-8" ).strip() # Convert the byte sequence into a string and strip any white space characters

# Remove the script's temp folder containing the project repository
def resetTempFolder ():
    global TEMP_FILEPATH
    
    subprocess.call( "rm -rf " + TEMP_FILEPATH, shell=True )
    subprocess.call( "mkdir " + TEMP_FILEPATH, shell=True )
    

    
def processCommits ( s ):
    global TEMP_FILEPATH
    global SCRIPT_FILEPATH

    repositoryURL = s.split( ".git" )[ 0 ]

    print( "Listing commits for project " + s )

    # Get potential commits from current repository
    passableCommits = filterCommits()
    
    # Save commits into local file
    with open( SCRIPT_FILEPATH + "/" + SCRIPT_OUTPUT_NAME, 'a+' ) as outputFile:
        
        if( len( passableCommits ) > 0 ):
            outputFile.write( LINE_SEPARATOR + " " + repositoryURL + " " + LINE_SEPARATOR )
            outputFile.write( "\r\n" )
        
            for entry in passableCommits:
                hash = entry[ 0 ]
                changedFiles = entry[ 1 ]
                outputFile.write( repositoryURL + "/commit/" + hash + "\t" ) # Commit url
                outputFile.write( repositoryURL + "\t" ) # Project url
                outputFile.write( hash + "\t" ) # Project commit hash
                outputFile.write( changedFiles + "\t" ) # Number of files changed in the commit
                outputFile.write( "\r\n" )

# Script entry point
main()
