import pandas as pd
import shutil
import html5lib
import requests
from bs4 import BeautifulSoup
import re
import time

def from_xls_html(infile, outfile):
    shutil.copy(infile, 'changed.html')
    shutil.copy('changed.html','txt_output.txt')
    time.sleep(2)

    encoding="latin-1"
    with open('txt_output.txt','r', encoding=encoding) as f:
        txt = f.read()

    # Modify the text to ensure the data display in html page

    txt = str(txt).replace('<style> .text { mso-number-format:\@; } </script>','')

    # Add head and body if it is not there in HTML text

    txt_with_head = '<html><head></head><body>'+txt+'</body></html>'

    # Save the file as HTML

    with open('./output.html','w') as f:
        f.write(txt_with_head)

    # Use beautiful soup to read

    url = "./output.html"
    with open(url) as f:
        soup = BeautifulSoup(f.read(), features="lxml")
        my_table = soup.find("table",attrs={'border': '1'})

    df = pd.read_html(str(my_table))[0]
    df.to_csv(outfile, index = None, header=True)
