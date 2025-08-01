import io, fitz, spacy, streamlit as st, pdfplumber
from docx import Document

nlp = spacy.load("en_core_web_sm")
EDU = ["university","college","institute","school","faculty","academy"]

def is_edu(t): return any(k in t.lower() for k in EDU)
def detect(txt):
    targets=set()
    for ent in nlp(txt).ents:
        if ent.label_=="PERSON" or is_edu(ent.text): targets.add(ent.text.strip())
    return list(targets)

def text_docx(b): return "\n".join(p.text for p in Document(io.BytesIO(b)).paragraphs)
def redact_docx(b,t):
    src,dst=Document(io.BytesIO(b)),Document(); out=io.BytesIO()
    for p in src.paragraphs:
        line=p.text
        for x in t: line=line.replace(x,"█"*len(x))
        dst.add_paragraph(line)
    dst.save(out); return out.getvalue()

def redact_pdf(b,t):
    pdf=fitz.open(stream=b,filetype="pdf")
    for pg in pdf:
        for x in t:
            for r in pg.search_for(x):
                pg.add_redact_annot(r,fill=(0,0,0))
        pg.apply_redactions()
    out=io.BytesIO(); pdf.save(out); return out.getvalue()

st.set_page_config(page_title="CV Anonymiser",layout="centered")
st.title("🕵️ CV Anonymiser")
st.markdown("Upload a **PDF** or **DOCX** CV – names and schools are black-boxed in the download.")

f=st.file_uploader("Upload",type=["pdf","docx"])
if f:
    ext,b=f.name.split(".")[-1].lower(),f.read()
    txt="\n".join(p.extract_text() or "" for p in pdfplumber.open(io.BytesIO(b)).pages) if ext=="pdf" else text_docx(b)
    targets=detect(txt)
    st.success(f"Detected {len(targets)} items"); st.write(targets)
    if st.button("Redact & download"):
        data=redact_pdf(b,targets) if ext=="pdf" else redact_docx(b,targets)
        st.download_button("Download",data,file_name=f"redacted_cv.{ext}")
