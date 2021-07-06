import re
import tqdm
import json
import sys
from difflib import SequenceMatcher
from subprocess import run,PIPE
import io
from io import StringIO
import argparse
TAG_RE = re.compile(r'<.*?>')
PROTECTED_RE = re.compile(r'<!--.*?-->|<style.*?>.*?</style>|<script.*?>.*?</script>|<head.*?>.*?</head>')
SINGLE_RE = re.compile(r'<[^/<>]*>[^<>]*</[^/<>]*>')
ENCLOSED_RE = re.compile(r'^<[^/<>]*>.*</[^/<>]*>$')
WORD_RE = re.compile(
    r'([^ \n\r\t,.&;/#=<>()-]+|(?:[ \n\r\t]|&nbsp;)+|[,.&;/#=<>()-])'
)
#WS_RE = re.compile(r'^([ \n\r\t]|&nbsp;)+$')
WS_RE = re.compile(r'([ \n\r\t]|&nbsp;)+')
GIT_DIFF_LINE_GETTER = re.compile(r'@@[^@]*@@')


class get_context(Exception):
    def __init__(self,message,front_rule,back_rule) -> None:
        self.front_rule = front_rule
        self.back_rule = back_rule
        super().__init__(message)
        
    

class log(object):
    LOG_LEVEL_QUIET = -1 #no console output
    LOG_LEVEL_MINIMAL = 1 #only requested output (will not alert for any errors)
    LOG_LEVEL_ERROR = 2 #show errors 
    LOG_LEVEL_PROGRESS = 3 #progress bars and requested output(ie the resulting file)
    LOG_LEVEL_DEBUG = 4 #show all output (will be messy)
    INSTANCE = None
    def __init__(self,log_level = LOG_LEVEL_DEBUG) -> None:
        super().__init__()
        self.log_level = log_level
        self.progress_bar = None
        log.INSTANCE = self
    def log(self,message,level):
        if(level <= self.log_level):
            print(message)
    
    def debug(self,messege):
        self.log(message,4)
    def error(self,messege):
        self.log(messege,2)
    def show(self,message):
        self.log(message,1)
    

    def start_bar(self,name,total):
        if(self.log_level >= 3):
            self.progress_bar = tqdm.tqdm(desc=name,total=total)
    def add_work(self,addition):
        if(self.log_level >= 3):
            if(self.progress_bar):
                self.progress_bar.total += addition
                self.progress_bar.update(0)
    def complete_work(self,work):
        if(self.log_level >= 3):
            if(self.progress_bar):
                self.progress_bar.update(work)
    def stop_bar(self):
        if(self.log_level >= 3):
            self.progress_bar.close()
            self.progress_bar = None

LIST_ITEM = re.compile(r'</?li[^</>]*>')

class splitting_preferences():
    def __init__(self,preference_breaks=[], sub_breaks = [],modify_inside=[], tag_as_text = [], kept_tags = [],escape_rules = [],no_diff=[], sub_rules = None):
        self.sub_rules = sub_rules
        self.kept_tags_RE = kept_tags
        self.pref_breaks_RE = preference_breaks
        self.sub_breaks_RE = sub_breaks
        self.text_tags_RE = tag_as_text
        self.escape_rules = escape_rules
        self.modify_inside_RE = modify_inside
        self.no_diff_RE = no_diff
    def get_subrules(self):
        return self.sub_rules
    #breaking rules
    def prevent_breakup(self,html,pos):#return an RE match for a section that should not be broken apart such as <script> <style> as they can't be split like normal html
        return PROTECTED_RE.match(html,pos=pos)
        #return None
    def preference_breaks(self,html,pos):#return an RE match for a section that should be split this is done after white space and prevent breakup but before the text and general spliting
        for k in self.pref_breaks_RE:

            if(match := k.match(html,pos)):
                return match 
        return None
    def sub_breaks(self,html):#detects it text needs to be broken a second time
        for rule,theashold in self.sub_breaks_RE:
            if(rule.match(html)):
                return theashold
        return False
    def modify_inside(self,html):
        for k in self.modify_inside_RE:
            if(k.match(html)):
                return True
        return False

    def treat_tag_as_text(self,item): #treat tags as text
        for k in self.text_tags_RE:
            if(k.match(item)):
                return True
        return False
    
    def keep_tag_delete(self,item): #when deleting
        for k in self.kept_tags_RE:
            if(k.match(item)):
                return True
        return False
    
    def require_escape(self,text):
        for (rule,front,back) in self.escape_rules:
            m = rule.match(text)
            m = front.match(text)
            m = back.match(text)
            if(rule.match(text) ):
                if( not front.match(text)):
                    raise get_context("required conext",front,back)
                if(not back.match(text)):
                    raise get_context("required conext",front,back)
                        
        return False
    def require_escape_no_raise(self,text):
        for (rule,front,back) in self.escape_rules:
            m = rule.match(text)
            m = front.match(text)
            m = back.match(text)
            if(rule.match(text) and not front.match(text) and not back.match(text)):
                return (front,back)

    
    def no_diff(self,text):
        for rule in self.no_diff_RE:
            if(rule.match(text)):
                return True
        return False 

    


class html_splitter(object):
    def __init__(self, html_string, spliting_preferences = splitting_preferences()):
        self.html_string = html_string
        self.pos = 0
        self.end_reached = False
        self.splitting_preferences = spliting_preferences
    def __iter__(self):
        return self
    def __next__(self):
        if self.end_reached:
            raise StopIteration
        while match := WS_RE.match(self.html_string,pos=self.pos):#starting with white space (clear up all the white space we can see
            self.pos = match.end()
        if(match := self.splitting_preferences.prevent_breakup(self.html_string,self.pos)): #don't break protected sections
            self.pos = match.end()
            return match.group(0)
        if match := self.splitting_preferences.preference_breaks(self.html_string,self.pos): #don't break sections that are user defined as special
            self.pos = match.end()
            return match.group(0)
        if match := TAG_RE.match(self.html_string, pos=self.pos): #general break rules 
            self.pos = match.end()
            return match.group(0)
        match = TAG_RE.search(self.html_string, pos=self.pos) #are there remaining tags
        if not match:
            self.end_reached = True
            return self.html_string[self.pos:]
        val = self.html_string[self.pos:match.start()]
        self.pos = match.start()
        return val
    def next(self):
        return self.__next__()

class html_differ(SequenceMatcher):
    start_del = "<del>"
    stop_del = "</del>"
    start_ins = "<ins>"
    stop_ins = "</ins>"
    def __init__(self, source1,source2,splitting_preferences = splitting_preferences()) -> None:
        self.splitting_preferences = splitting_preferences
        SequenceMatcher.__init__(self, lambda x: x in [""," ","\t","\n"], source1, source2, False)
        
    def set_seqs(self,a,b,protect_small_tags_a = None, protect_small_tags_b = None):
        #split text by tags and and non-tags by words


        

        SequenceMatcher.set_seqs(self,
            sum([[k] if k.startswith('<') else WORD_RE.findall(k) for k in html_splitter(a,self.splitting_preferences)],[]),
            sum([[k] if k.startswith('<') else WORD_RE.findall(k) for k in html_splitter(b,self.splitting_preferences)],[])
        )
    def clean_delete(self,del_items):
        #return a clean set of delete tags that follow html rules
        end = ""
        text = []
        for item in del_items:
            if(self.splitting_preferences.modify_inside(item)):
                new_sub_items = sum([[k] if k.startswith('<') else WORD_RE.findall(k) for k in html_splitter(item)],[])
                end += self.clean_delete(new_sub_items)
            elif(item.startswith('<') and not self.splitting_preferences.treat_tag_as_text(item)):#insert the text wrapped in del tags treat small tags as text
                if(not all([WS_RE.match(i) for i in text])): #not all white space
                    end += html_differ.start_del+"".join(text)+html_differ.stop_del
                text = []
                if self.splitting_preferences.keep_tag_delete(item):
                    end += item
            else:
                text.append(item)
        if(text):
            end += html_differ.start_del+"".join(text)+html_differ.stop_del
        return end
    def clean_insert(self,ins_items):
        #return a clean set of insert tags that follow html rules
        end = ""
        text = []
        for item in ins_items:
            
            if(self.splitting_preferences.modify_inside(item)):
                new_sub_items = sum([[k] if k.startswith('<') else WORD_RE.findall(k) for k in html_splitter(item)],[])
                end += self.clean_insert(new_sub_items)
            elif(item.startswith('<') and not self.splitting_preferences.treat_tag_as_text(item)):#insert the text wrapped in ins check preferences for 
                if(not all([WS_RE.match(i) for i in text])): #not all white space
                    end += html_differ.start_ins+"".join(text)+html_differ.stop_ins
                text = []
                end += item #keep tags
            else:
                text.append(item)
        if(text and not all([WS_RE.match(i) for i in text])):
            end += html_differ.start_ins+"".join(text)+html_differ.stop_ins
        return end
    def white_space_change(self,origin,modified):
        #this is a white space change
        #same number of tag and text blocks 
        #all words are the same
        white_space_change = False
        if(len(origin)==len(modified)):
            white_space_change = True
            for o,m in zip(origin,modified):
                if all([WS_RE.match(o),WS_RE.match(m)]):#both are whitespace
                    continue
                if(o.startswith('<') and m.startswith('<') and not  self.splitting_preferences.treat_tag_as_text(m) and not self.splitting_preferences.treat_tag_as_text(o) and not self.splitting_preferences.modify_inside(m) and not self.splitting_preferences.modify_inside(o)):
                    continue
                if o==m:#are identical
                    pass
                else:
                    white_space_change = False
                    break
        return white_space_change
    def detect_sub_breaks(self,items):
        for item in items:
            if(self.splitting_preferences.sub_breaks(item)):
                return True
        return False
    def diff_html(self): 
        """use the sequence matcher to create the diffed html"""
        opcodes = self.get_opcodes()
        a = self.a
        b = self.b
        out = StringIO()
        #log.INSTANCE.add_work(len(opcodes))

        

        for tag, start_a, end_a, start_b, end_b in opcodes: #main loop

            if(self.splitting_preferences.no_diff("".join(b[start_b:end_b]))):
                out.write("".join(b[start_b:end_b]))
                continue
            
            if tag == 'equal':
                out.write("".join(a[start_a:end_a]))
            if tag == 'delete':
                out.write(self.clean_delete(a[start_a:end_a]))
            if tag == 'insert':
                out.write(self.clean_insert(b[start_b:end_b]))
            if tag == 'replace':
                #if (end_a-start_a) == 1 and (end_b-start_b) != 1 and self.use_preference==True : #seem like the complexity has increased diff this section without quick change
                #    d=html_differ("".join(a[start_a:end_a]),"".join(b[start_b:end_b]),use_preference = False).diff_html()
                #    out.write(d)
                if(self.splitting_preferences.get_subrules() != None and (self.detect_sub_breaks(a[start_a:end_a]) or self.detect_sub_breaks(b[start_b:end_b]))):
                    d=html_differ("".join(a[start_a:end_a]),"".join(b[start_b:end_b]),self.splitting_preferences.get_subrules())
                    
                    lower_html = d.diff_html()
                    r = d.ratio()
                    if(d.ratio() > self.splitting_preferences.sub_breaks("".join(a[start_a:end_a])) or d.ratio() > self.splitting_preferences.sub_breaks("".join(b[start_b:end_b]))):
                        out.write(lower_html)
                        continue


                if(not self.white_space_change(a[start_a:end_a],b[start_b:end_b])):
                    out.write(self.clean_delete(a[start_a:end_a]))
                    out.write(self.clean_insert(b[start_b:end_b]))
                    #print("white space")
                else:
                    #print("replace else")
                    #out.write(self.clean_delete(a[start_a:end_a]))
                    out.write(self.clean_insert(b[start_b:end_b]))
                    #out.write("".join(b[start_b:end_b]))
            #log.INSTANCE.complete_work(1)
        html = out.getvalue()
        out.close()
        return html

def git_diff(commit_a,commit_b,file_path,context = 1):
    """function to grab changes and line numbers"""
    out = run(['git','--no-pager','diff','--minimal',f'--unified={context}',commit_a,commit_b,'--',file_path],stdout=PIPE).stdout.decode("utf-8")
    def clean_line_numbers(line_numbers):
        line_pairs = line_numbers.replace('@@','').strip().split()
        return {
            "start_a":int(line_pairs[0].split(",")[0].replace("-","")),
            "length_a":int(line_pairs[0].split(",")[1]),
            "start_b":int(line_pairs[1].split(",")[0].replace("+","")),
            "length_b":int(line_pairs[1].split(",")[1]),
        }

    return list(map(clean_line_numbers,GIT_DIFF_LINE_GETTER.findall(out)[::]))

def git_read_file(commit_a,file_path):
    """function to grab file data from past commits"""
    out = run(['git','--no-pager','show',f"{commit_a}:{file_path}"],stdout=PIPE).stdout.decode("utf-8")
    return out.split("\n")

def process_patch(file_a,file_b,patch,spliting_preferences,min_start_a=0,min_start_b=0):

    text_a = "".join(file_a[patch["start_a"]:patch["start_a"]+patch["length_a"]])
    text_b = "".join(file_b[patch["start_b"]:patch["start_b"]+patch["length_b"]])

    try:

        #make sure the context is large enough 
        if(min_start_a < patch["start_a"] and min_start_b < patch["start_b"]):
            spliting_preferences.require_escape(text_a)
            spliting_preferences.require_escape(text_b)
        diff = html_differ(text_a,text_b,splitting_preferences=spliting_preferences)
        end = diff.diff_html() 
        return {"new_text":end,"patch":patch}
    except get_context as con_req:
        while ( not con_req.front_rule.match("".join(file_b[patch["start_b"]:patch["start_b"]+patch["length_b"]])) 
            or not con_req.front_rule.match("".join(file_a[patch["start_a"]:patch["start_a"]+patch["length_a"]])) ) \
            and (patch["start_a"]>min_start_a and patch["start_b"]>min_start_b):

            patch["start_a"] -= 1
            patch["length_a"] += 1
            patch["start_b"] -= 1
            patch["length_b"] += 1
        while not con_req.back_rule.match("".join(file_a[patch["start_a"]:patch["start_a"]+patch["length_a"]])):
            patch["length_a"] += 1
        while not con_req.back_rule.match("".join(file_b[patch["start_b"]:patch["start_b"]+patch["length_b"]])):
            patch["length_b"] += 1
        
        return process_patch(file_a,file_b,patch,spliting_preferences,min_start_a = min_start_a,min_start_b=min_start_b)




def process_file(patch_list,file_a,file_b,split_pref):
    """take in both files and a patch list of line numbers and create the html changes for each one"""
    replacements = {}
    end_a = 0
    end_b = 0
    log.INSTANCE.start_bar("computing patches",len(patch_list))
    for i,patch in enumerate(patch_list):#for each patch make and run a html diff store change requests in the replacements


        if(patch["start_a"] + patch["length_a"] < end_a or patch["start_b"] + patch["length_b"] < end_b):
            log.INSTANCE.complete_work(1)
            continue
        while patch["start_a"] < end_a and patch["start_b"] < end_b:
            patch["start_a"] += 1
            patch["length_a"] -= 1
            patch["start_b"] += 1
            patch["length_b"] -= 1
        
        if(patch["length_b"]<=0 or patch["length_a"]<=0):
            log.INSTANCE.complete_work(1)
            continue

        result = process_patch(file_a,file_b,patch,split_pref,min_start_a=end_a,min_start_b=end_b)
        log.INSTANCE.complete_work(1)
        
        for i in range(result["patch"]["start_a"]+1,result["patch"]["start_a"]+result["patch"]["length_a"]):
            replacements[i] = ""
        replacements[result["patch"]["start_a"]] = result["new_text"]
        end_a = result["patch"]["start_a"]+result["patch"]["length_a"]
        end_b = result["patch"]["start_b"]+result["patch"]["length_b"]
        
            
    log.INSTANCE.stop_bar()
    def do_replacement(pack):#simple function to replace the lines in the original
        line_number,line = pack
        return replacements.get(line_number,line)
    
    return list(map(do_replacement,[(i,line) for i,line in enumerate(file_a)]))


def preference_breaks_from_json(json_dict):
    if(json_dict != {} ):
        end = [re.compile(f'<{tag}[^/<>]*>.*?</{tag}[^/<>]*>') for tag in json_dict.get("break_tags",[])] + preference_breaks_from_json(json_dict.get("sub_rules",{}))
        return end
    return []
def preference_sub_breaks_from_json(json_dict):
    if(json_dict != {} ):
        rules = []
        for key,value in json_dict.get("sub_break_tags",{}).items():
            rules.append(
                (
                    re.compile(f'<{key}[^/<>]*>.*?</{key}[^/<>]*>') , value
                )
            )
        rules += preference_sub_breaks_from_json(json_dict.get("sub_rules",{}))
        return rules
    return []
def preference_sub_modify_inside_json(json_dict):
    if(json_dict != {} ):
        return [re.compile(f'<{tag}[^/<>]*>.*?</{tag}[^/<>]*>') for tag in json_dict.get("modify_inside",[])] + preference_sub_modify_inside_json(json_dict.get("sub_rules",{}))
    return []

def preference_text_tags_from_json(json_dict):
    if(json_dict != {} ):
        return [re.compile(f'<{tag}[^/<>]*>.*?</{tag}[^/<>]*>') for tag in json_dict.get("text_tags",[])]  + preference_text_tags_from_json(json_dict.get("sub_rules",{}))
    return []
def preference_kept_tags_from_json(json_dict):
    if(json_dict != {} ):
        return [re.compile(f'</?{tag}[^/<>]*>') for tag in json_dict.get("kept_tags",[])]+ preference_kept_tags_from_json(json_dict.get("sub_rules",{}))
    return []
def preference_no_diff_from_json(json_dict):
    if(json_dict != {} ):
        return [re.compile(f'<{tag}[^/<>]*>.*?</{tag}[^/<>]*>') for tag in json_dict.get("no_diff",[])]+preference_no_diff_from_json(json_dict.get("sub_rules",{}))
    return []

def preference_escape_rules(json_dict):
    if(json_dict != {} ):
        all_rules = []
        for key,values in json_dict.get("context_escapes",{}).items():
            front = re.compile(f"^.*<{key}[^<>/]*?>.*")
            back = re.compile(f".*</{key}[^<>/]*?>.*$")
            for v in values:
                rule = re.compile(f".*</?{v}[^<>/]*>.*")
                all_rules.append((rule,front,back))
        all_rules += preference_escape_rules(json_dict.get("sub_rules",{}))
        return all_rules
    return []

def preference_from_json(json_dict):

    return splitting_preferences(
        preference_breaks=preference_breaks_from_json(json_dict),
        sub_breaks=preference_sub_breaks_from_json(json_dict),
        modify_inside=preference_sub_modify_inside_json(json_dict),
        tag_as_text=preference_text_tags_from_json(json_dict),
        kept_tags=preference_kept_tags_from_json(json_dict),
        escape_rules=preference_escape_rules(json_dict),
        no_diff = preference_no_diff_from_json(json_dict),
        sub_rules=preference_from_json(json_dict["sub_rules"]) if "sub_rules" in json_dict.keys() else splitting_preferences()
    )


if __name__ == "__main__":
    
    split_pref = preference_breaks_from_json({})

    #with open('pref.json') as f:
    #    split_pref=preference_from_json(json.load(f))

    
    parser = argparse.ArgumentParser(description = "Produces difference documents for html files in a git repository" )

    parser.add_argument('from_commit',type=str,nargs=1,help='the pervious commit of the file')
    parser.add_argument('to_commit',type=str,nargs=1,help='the pervious commit of the file')
    parser.add_argument('file',type = str,nargs=1,help='the path to the html file to diff')
    parser.add_argument('outfile', nargs='?', type=argparse.FileType('w'), default=sys.stdout,help="optional location of output file for the diffed html defaults to the console")
    parser.add_argument('--pref',nargs='?', type=argparse.FileType('r'),help = "path to preference file")
    parser.add_argument('--log',type=int,nargs='?',default=4,help="set the level of log output")
    args = parser.parse_args()
    log(args.log)
    commit_a = args.from_commit[0]#"71ee350eb8806aa27c63829ef2141259c3c9538a"
    commit_b = args.to_commit[0]#"3dbec14a113f0be7cb9db471768d2751d3bb9dca"
    file_name = args.file[0]#"html/index.html"

    if(args.pref):
        split_pref=preference_from_json(json.load(args.pref))

    

    line_nums = git_diff(commit_a,commit_b,file_name)
    file_a = git_read_file(commit_a,file_name)
    file_b = git_read_file(commit_b,file_name)

    
    result = process_file(line_nums,file_a,file_b,split_pref)
  
    args.outfile.reconfigure(encoding = 'utf-8')
    
    for line in result:
        args.outfile.write(line)
    