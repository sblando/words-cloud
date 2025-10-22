# 🌥️ words-cloud (base)

> **Status:** *Work-in-progress* — the IPM issue is still open / not finalized as of **Oct 21, 2025**.

Minimal CLI to generate **word clouds** from PDF articles.  
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