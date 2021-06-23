This is a python script for diffing html documents. It is designed to be used with git to produce inline html diffs for html document tracked by a git repository. Provided rule set is not exhaustive.

install
The script requires a version of python 3.7 - 3.9
you will also need to install tqdm with either 
    pip install tqdm or pip install -r requirements.txt

usage
The command line tool uses commit identifiers to determine the versions of the html document to use. 
Make sure to use this tool in the root of the git repository


from_commit    the pervious commit of the file
to_commit      the pervious commit of the file
file           the path to the html file to diff
outfile        optional location of output file for the diffed html defaults to the console 

example usage

python html_diff.py 71ee350eb ebcc0a6ba7 index.html diff.html

This will create a inline diff of the index.html file between the commits of 71ee350... to ebcc0a6.... this will be saved to diff.html
to find git commits you can use the git log function
if the commit are inputted backwards it will compute the reverse changes (how to revert to the pervious version)

log level
use the --log argument to set the logged output
--log [log level]

a log level of 4 or more will show all output (default)
a log level of zero or less will not show any output except for the diffed html if no output file is given
a log level of at least 3 will show a progress bar
a log level of at least 2 will show any errors detected


preference file
provided rule set is not exhaustive

use the --pref argument to set the preference for the diff
The preference file is a json file used to control how the inline diff is processed

the preference file is a recursive set of rules for when to break up html tags. below is an explanation for each rule

break_tags are used to keep tags together if the tag is in this list all contents within the tag will be kept together
sub_break_tags are checked when a replacement is found when diffing if the tag is in the list and the percent difference is more than the threshold the tag will be broken by the sub rule set
modify_inside is used to correct for matching w3 standards <ins> tags are not allowed to be children of <ul> but can be used a child of <li> if in this list the html diff will but <ins> or <del> tags inside the element instead of outside
text_tags tags set as text tags will be counted as text in most cases meaning they will be replaced in blocks and of their contents will be kept together.
kept_tags, by default when deleting only text is kept this can break the structure of the html. tags within this list will always be kept even if deleted.
no_diff tags within the no diff rule won't be diffed only the new version will be kept
context_escapes sometimes the diff script attempts to diff just a single row of a table. This can be a problem as without the context of the full table it can be difficult to know how it changed. Context escapes are key list pairs that ensure whenever a item in the list is found that the open and close of the key tag exists in the context.
sub_rules in the event the the first set of rules is fails to diff the rules in the sub rules will take effect. sub rules are also include in the parent rules set so rules higher in the tree are abandoned faster



