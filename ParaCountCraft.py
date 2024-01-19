import panflute as pf
import re
import os

count = 0
chapter = 0
reset_at_chapter = False
chapter_sep = "."
enclosing_chars = ["[", "]"]
label_prefix = "rz"
extra_char_prefix = ".rz:"
metadata_key = "letter.settings.rz"

def check_metadata(doc):
    global metadata_key
    return doc.get_metadata(metadata_key, False)

def output_preamble(doc):
    preamble = r'% + ParaCountCraft preamble + %' + '\n'
    preamble += r'\usepackage{hyperref}%' + '\n'
    preamble += r'\usepackage{marginnote}%' + '\n'
    preamble += r'\usepackage{color}%' + '\n'
    preamble += r'\definecolor{rzgray}{rgb}{0.70, 0.70, 0.70}%' + '\n'
    preamble += r'\newcommand{\randziffer}[2]{%' + '\n'
    preamble += r'\marginnote{\textcolor{rzgray}{\scriptsize #1}}[#2\baselineskip]%' + '\n'
    preamble += r'}%' + '\n'
    preamble += r'% - ParaCountCraft preamble - %' + '\n'
    doc.metadata['ParaCountCraft-Preamble'] = pf.MetaInlines(pf.RawInline(preamble, format='latex'))

    return doc

def process_element(elem, userid_pattern, extra_char_pattern):
    results = []
    found_user_id = found_extra_char = False

    if isinstance(elem, pf.Str):
        if not found_user_id:
            # Extrahiere die benutzerdefinierte ID
            userid_match = userid_pattern.search(elem.text)
            if userid_match:
                elem.text = ""  # Setze den Text auf einen leeren String
                results.append(('user_id', userid_match.group(1)))
                found_user_id = True

        if not found_extra_char:
            # Extrahiere das extra Zeichen
            extra_char_match = extra_char_pattern.search(elem.text)
            if extra_char_match:
                elem.text = ""  # Setze den Text auf einen leeren String
                results.append(('extra_char', extra_char_match.group(1)))
                found_extra_char = True

    elif isinstance(elem, list):
        for subelem in elem:
            if not found_user_id or not found_extra_char:
                sub_results = process_element(subelem, userid_pattern, extra_char_pattern)
                if sub_results:
                    results.extend(sub_results)
                    # Überprüfen, ob beide Werte gefunden wurden
                    for r in sub_results:
                        if r[0] == 'user_id':
                            found_user_id = True
                        elif r[0] == 'extra_char':
                            found_extra_char = True

    elif hasattr(elem, 'content'):
        for index, subelem in enumerate(elem.content):
            if not found_user_id or not found_extra_char:
                sub_results = process_element(subelem, userid_pattern, extra_char_pattern)
                if sub_results:
                    elem.content[index] = subelem
                    results.extend(sub_results)
                    # Überprüfen, ob beide Werte gefunden wurden
                    for r in sub_results:
                        if r[0] == 'user_id':
                            found_user_id = True
                        elif r[0] == 'extra_char':
                            found_extra_char = True

    if found_user_id and found_extra_char:
        # Wenn beide gefunden wurden, brich die Suche ab
        return results

    return results if results else None

def count_para(elem, doc):
    global count, chapter
    parent = elem.parent

    # Kapitel zurücksetzen, wenn nötig
    if isinstance(elem, pf.Header) and elem.level == 1 and 'unnumbered' not in elem.classes and reset_at_chapter:
        chapter += 1
        if reset_at_chapter is True:
            count = 0

    if (isinstance(elem, pf.Para) or isinstance(elem, pf.OrderedList) or isinstance(elem, pf.BulletList)) and not (len(elem.content) > 0 and isinstance(elem.content[0], pf.Image)) and not isinstance(parent, pf.Note):
        userid_pattern = re.compile(f'{{#{label_prefix}:(\\d+)}}')
        extra_char_pattern = re.compile(f'{{{extra_char_prefix}(\\w+)}}')

        user_id, extra_char = None, None
        for e in elem.content:
            results = process_element(e, userid_pattern, extra_char_pattern)
            if results:
                for result in results:
                    if result[0] == 'user_id' and user_id is None:
                        user_id = result[1]
                    elif result[0] == 'extra_char' and extra_char is None:
                        extra_char = result[1]

                    if user_id is not None and extra_char is not None:
                        # Sobald beide gefunden wurden, kann die Schleife verlassen werden
                        break

        
        if extra_char is None:
            count += 1

        #write_to_file(f"Char: {extra_char}; User ID: {user_id}", "C:\\Users\\maxim\\Working\\debug.txt")

        # Erstelle die id für den Absatz
        id = f"{count}{extra_char}" if extra_char else count
        id = f"{chapter}{chapter_sep}{count}{extra_char}" if reset_at_chapter else id
        label = f"{user_id}" if user_id else id

        if isinstance(elem, pf.Para):
            baselineskip = "-0.1"
        elif isinstance(elem, (pf.BulletList, pf.OrderedList)):
            baselineskip = "-0.2"
        # Füge die Randziffer mit LaTeX am Anfang des Absatzes ein
        text_content = f"\\randziffer{{{enclosing_chars[0]}{id}{enclosing_chars[1]}}}{{{baselineskip}}}"
        text_content = f"\leavevmode\\hypertarget{{{label_prefix}:{label}}}{{\\label{{{label_prefix}:{label}}}{{{text_content}}}}}"
        if isinstance(elem, pf.Para):
            elem.content.insert(0, pf.RawInline(text_content, format='tex'))
        elif isinstance(elem, (pf.BulletList, pf.OrderedList)):
            inster_in_plain_elem(elem, text_content)

def inster_in_plain_elem(elem, text_content):
    if isinstance(elem, pf.Plain):
        elem.content.insert(0, pf.RawInline(text_content, format='tex'))
        return True  # Signalisiert, dass das RawInline eingefügt wurde

    # Rekursiver Aufruf für alle Unterelemente, falls vorhanden
    elif hasattr(elem, 'content'):
        for subelem in elem.content:
            inserted = inster_in_plain_elem(subelem, text_content)
            if inserted:
                return True  # Beendet die Funktion, sobald das RawInline eingefügt wurde

    return False  # Signalisiert, dass das RawInline noch nicht eingefügt wurde

def write_to_file(content, file_path):
    with open(file_path, 'a', encoding='utf-8') as file:
        file.write(content + '\n')

def main(doc=None):
    doc = pf.load()
    if not check_metadata(doc):
        pf.dump(doc)
    else:
        doc = pf.run_filter(count_para, doc=doc)
        doc = output_preamble(doc)
        pf.dump(doc)

if __name__ == "__main__":
    main()
