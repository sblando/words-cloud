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

## 📊 Demo results

Below is a small demonstration using one article from the dataset.  
You can **download the CSV** and **view the generated word cloud**:

- **Top terms (CSV):**  
  [examples/article_01_top_terms.csv](https://github.com/sblando/words-cloud/blob/4d522c5416990a311b51d32927065cb59f60b5f5/examples/article_01_top_terms.csv)  
  <sub>Direct download (raw): https://raw.githubusercontent.com/sblando/words-cloud/4d522c5416990a311b51d32927065cb59f60b5f5/examples/article_01_top_terms.csv</sub>

- **Word cloud (PNG):**  
  [examples/article_01_wordcloud.png](https://github.com/sblando/words-cloud/blob/4d522c5416990a311b51d32927065cb59f60b5f5/examples/article_01_wordcloud.png)

### Preview

![Word cloud preview – article_01](https://github.com/sblando/words-cloud/blob/4d522c5416990a311b51d32927065cb59f60b5f5/examples/article_01_wordcloud.png)

> Reproduced with:
>
> ```bash
> python ./src/make_clouds.py --input ./data --output ./output --top 120 --stop study results figure table method methods
> ```
>
> Outputs were then copied from `./output/` to `./examples/`.
