import PyPDF2
import spacy

def pdf_to_string(pdf_path):
    text = ""
    with open(pdf_path, 'rb') as pdf_file:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        num_pages = len(pdf_reader.pages)
        for page_number in range(num_pages):
            page = pdf_reader.pages[page_number]
            text += page.extract_text()
    return text

def compress_outline(outline):
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(outline)

    ranges = []
    delta = 100 #how far to go away from the inital date
    for ent in doc.ents:
        if ent.label_ == 'DATE':
            print(ent.text, ent.start_char, ent.end_char, ent.label_)
            lft = max(0,ent.start_char-delta)
            rit = min(ent.end_char+delta, len(outline)-1)
            while outline[lft] != '.' and lft > 0:
                lft-=1
            while outline[rit] != '.' and rit < len(outline):
                rit+=1
            ranges.append((lft,rit))

    set = {0}
    for i in ranges:
        for j in range (i[0],i[1]):
            set.add(j)

    s =""
    for i in set:
        s+=outline[i]
    return s
