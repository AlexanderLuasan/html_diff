from re import split
from html_diff import preference_from_json,process_patch
import json



def test_patch(initial,change,goal,patch,preferences):
    initial = [i.strip() for i in initial]
    change = [i.strip() for i in change]
    goal = [i.strip() for i in goal]
    new_patch = process_patch(initial,change,patch,preferences)
    for i in range(new_patch["patch"]["start_a"]+1,new_patch["patch"]["start_a"]+new_patch["patch"]["length_a"]):
        initial[i]=""
    initial[new_patch["patch"]["start_a"]] = new_patch["new_text"]
    print("".join(initial))
    print("".join(goal))
    if("".join(initial) == "".join(goal)):
        return True
    else:
        return False
tests = []

def P_patch_1(preferences):
    initial = '''<p>the initial text</p>'''.split("\n")
    change = '''<p>the changed text</p>'''.split("\n")
    goal = '''<p>the <del>initial</del><ins>changed</ins> text</p>'''.split("\n")
    patch = {'start_a':0,'start_b':0,'length_a':len(initial),'length_b':len(change)} 
    return test_patch(initial,change,goal,patch,preferences)
tests.append(P_patch_1)

def P_patch_2(preferences):
    initial = '''<p>the initial text</p>'''.split("\n")
    change = '''<p>the text</p>'''.split("\n")
    goal = '''<p>the <del>initial </del>text</p>'''.split("\n")
    patch = {'start_a':0,'start_b':0,'length_a':len(initial),'length_b':len(change)} 
    return test_patch(initial,change,goal,patch,preferences)
tests.append(P_patch_2)

def P_patch_3(preferences):
    initial = '''<p>the initial text</p>'''.split("\n")
    change = '''<p>complete rewrite</p>'''.split("\n")
    goal = '''<p><del>the initial text</del><ins>complete rewrite</ins></p>'''.split("\n")
    patch = {'start_a':0,'start_b':0,'length_a':len(initial),'length_b':len(change)} 
    return test_patch(initial,change,goal,patch,preferences)
tests.append(P_patch_3)

def P_patch_4(preferences):
    initial = '''<p>the initial text</p>'''.split("\n")
    change = '''<p>the initial text</p>'''.split("\n")
    goal = '''<p>the initial text</p>'''.split("\n")
    patch = {'start_a':0,'start_b':0,'length_a':len(initial),'length_b':len(change)} 
    return test_patch(initial,change,goal,patch,preferences)
tests.append(P_patch_4)

def li_patch_1(preferences):
    initial = '''<ul>
            <li>item 1</li>
            <li>item two</li>
            </ul>'''.split("\n")
    change = '''<ul>
            <li>item 1</li>
            <li>item two</li>
            <li>item 3</li>
            </ul>'''.split("\n")
    goal = '''<ul>
            <li>item 1</li>
            <li>item two</li>
            <li><ins>item 3</ins></li>
            </ul>'''.split("\n")
    patch = {'start_a':0,'start_b':0,'length_a':len(initial),'length_b':len(change)} 
    return test_patch(initial,change,goal,patch,preferences)
tests.append(li_patch_1)

def li_patch_2(preferences):
    initial = '''<ul>
            <li>item 1</li>
            <li>item two</li>
            <li>item 3</li>
            </ul>'''.split("\n")
    change = '''<ul>
            <li>item 1</li>
            <li>item two</li>
            </ul>'''.split("\n")
    goal = '''<ul>
            <li>item 1</li>
            <li>item two</li>
            <li><del>item 3</del></li>
            </ul>'''.split("\n")
    patch = {'start_a':0,'start_b':0,'length_a':len(initial),'length_b':len(change)} 
    return test_patch(initial,change,goal,patch,preferences)
tests.append(li_patch_2)

def li_patch_3(preferences):
    initial = '''<ul>
            <li>item 1</li>
            <li>item two</li>
            <li>item 3</li>
            </ul>'''.split("\n")
    change = '''<ul>
            <li>item 1</li>
            <li>item two</li>
            </ul>'''.split("\n")
    goal = '''<ul>
            <li>item 1</li>
            <li>item two</li>
            <li><del>item 3</del></li>
            </ul>'''.split("\n")
    patch = {'start_a':0,'start_b':0,'length_a':len(initial),'length_b':len(change)} 
    return test_patch(initial,change,goal,patch,preferences)
tests.append(li_patch_3)


def li_patch_4(preferences):
    initial = '''<ul>
            <li>item 1</li>
            <li>item two</li>
            <li>item 3</li>
            </ul>'''.split("\n")
    change = '''<ul>
            <li>item 1</li>
            <li>new second thing</li>
            <li>item 3</li>
            </ul>'''.split("\n")
    goal = '''<ul>
            <li>item 1</li>
            <li><del>item two</del></li>
            <li><ins>new second thing</ins></li>
            <li>item 3</li>
            </ul>'''.split("\n")
    patch = {'start_a':0,'start_b':0,'length_a':len(initial),'length_b':len(change)} 
    return test_patch(initial,change,goal,patch,preferences)
tests.append(li_patch_4)

def li_patch_5(preferences):
    initial = '''<ul>
            <li>item 1</li>
            <li>item two</li>
            <li>item 3</li>
            </ul>'''.split("\n")
    change = '''<ul>
            <li>item zero</li>
            <li>item 1</li>
            <li>item two</li>
            <li>item 3</li>
            <li>item four</li>
            </ul>'''.split("\n")
    goal = '''<ul>
            <li><ins>item zero</ins></li>
            <li>item 1</li>
            <li>item two</li>
            <li>item 3</li>
            <li><ins>item four</ins></li>
            </ul>'''.split("\n")
    patch = {'start_a':0,'start_b':0,'length_a':len(initial),'length_b':len(change)} 
    return test_patch(initial,change,goal,patch,preferences)
tests.append(li_patch_5)



def table_patch_1(preferences):
    initial = '''<table>
    <thead>
        <tr><td>first name</td><td>last name</td></tr>
    </thead>
    <tbody>
        <tr><td>mya</td><td>Greer</td></tr>
        <tr><td>Melvin</td><td>Lara</td></tr>
        <tr><td>Tristan</td><td>Summers</td></tr>
        <tr><td>Jose</td><td>Porter</td></tr>
        <tr><td>Annabelle</td><td>Fleming</td></tr>
        <tr><td>Marco</td><td>Joseph</td></tr>
    <tbody>
    </table>'''.split("\n")
    change = '''<table>
    <thead>
        <tr><td>first name</td><td>last name</td></tr>
    </thead>
    <tbody>
        <tr><td>mya</td><td>Greer</td></tr>
        <tr><td>Tristan</td><td>Summers</td></tr>
        <tr><td>Jose</td><td>Porter</td></tr>
        <tr><td>Annabelle</td><td>Fleming</td></tr>
        <tr><td>Marco</td><td>Joseph</td></tr>
    <tbody>
    </table>'''.split("\n")
    goal = '''<table>
    <thead>
        <tr><td>first name</td><td>last name</td></tr>
    </thead>
    <tbody>
        <tr><td>mya</td><td>Greer</td></tr>
        <tr><td><del>Melvin</del></td><td><del>Lara</del></td></tr>
        <tr><td>Tristan</td><td>Summers</td></tr>
        <tr><td>Jose</td><td>Porter</td></tr>
        <tr><td>Annabelle</td><td>Fleming</td></tr>
        <tr><td>Marco</td><td>Joseph</td></tr>
    <tbody>
    </table>'''.split("\n")
    patch = {'start_a':0,'start_b':0,'length_a':len(initial),'length_b':len(change)} 
    return test_patch(initial,change,goal,patch,preferences)
tests.append(table_patch_1)

def table_patch_2(preferences):
    initial = '''<table>
    <thead>
        <tr><td>first name</td><td>last name</td></tr>
    </thead>
    <tbody>
        <tr><td>mya</td><td>Greer</td></tr>
        <tr><td>Melvin</td><td>Lara</td></tr>
        <tr><td>Tristan</td><td>Summers</td></tr>
        <tr><td>Jose</td><td>Porter</td></tr>
        <tr><td>Annabelle</td><td>Fleming</td></tr>
        <tr><td>Marco</td><td>Joseph</td></tr>
    <tbody>
    </table>'''.split("\n")
    change = '''<table>
    <thead>
        <tr><td>first name</td><td>last name</td></tr>
    </thead>
    <tbody>
        <tr><td>mya</td><td>Greer</td></tr>
        <tr><td>Melvin</td><td>Lara</td></tr>
        <tr><td>Tristan</td><td>Springs</td></tr>
        <tr><td>Jose</td><td>Porter</td></tr>
        <tr><td>Annabelle</td><td>Fleming</td></tr>
        <tr><td>Marco</td><td>Joseph</td></tr>
    <tbody>
    </table>'''.split("\n")
    goal = '''<table>
    <thead>
        <tr><td>first name</td><td>last name</td></tr>
    </thead>
    <tbody>
        <tr><td>mya</td><td>Greer</td></tr>
        <tr><td>Melvin</td><td>Lara</td></tr>
        <tr><td>Tristan</td><td><del>Summers</del><ins>Springs</ins></td></tr>
        <tr><td>Jose</td><td>Porter</td></tr>
        <tr><td>Annabelle</td><td>Fleming</td></tr>
        <tr><td>Marco</td><td>Joseph</td></tr>
    <tbody>
    </table>'''.split("\n")
    patch = {'start_a':0,'start_b':0,'length_a':len(initial),'length_b':len(change)} 
    return test_patch(initial,change,goal,patch,preferences)
tests.append(table_patch_2)


if __name__ == "__main__":
    print("testing")
    split_pref=None
    with open('pref.json') as f:
        split_pref=preference_from_json(json.load(f))

    table_patch_1(split_pref)

    for test in tests:

        print(test.__name__,test(split_pref))
    
