# 🌥️ words-cloud 

> **Status:** *Work-in-progress* — the IPM issue is still open / not finalized as of **Oct 21, 2025**.

Generates CSVs and PNG word clouds (unigrams and optionally bigrams) from **PDF/TXT/DOCX** files.

Tested on **12 PDFs from _Information Processing & Management_, vol. 63 (2026) 104440** (single issue).

## Dataset (source)
Issue landing page (ScienceDirect): 
https://www.sciencedirect.com/journal/information-processing-and-management/vol/63/issue/2/part/PB  
*Note: the issue is still in progress; contents may change.*

### File normalization
The PDF filenames were normalized to a consistent sequence before processing, using this command (run inside the folder that contains the PDFs).  
It renames files to:
- `article_01.pdf`  
- `article_02.pdf`  
- …

```powershell
$idx = 1
Get-ChildItem -Filter *.pdf | Sort-Object Name | ForEach-Object {
  Rename-Item $_ -NewName ("article_{0:D2}{1}" -f $idx++, $_.Extension)
}
```

### Create & activate a virtual environment

**Windows (PowerShell)**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```
````
pip install -U pip
pip install -r requirements.txt
# or:
pip install pandas matplotlib wordcloud pdfminer.six python-docx Unidecode
````

### run command used

```
python .\src\make_clouds.py --input .\data --output .\output --top 120 --stop study results figure table method methods
```