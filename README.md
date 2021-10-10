# Rerank
The goal is to develop “telescoping” model, which here is Rochhio's Method aimed at improving the precision of results using pseudo-relevance feedback. We will use data collection and queries from TREC COVID track. We have used TF-IDF values as term weight, with many other optimizations and details stated in `/Algorithmic_Details.pdf`. For more details about the problem statement see `/assignment2.pdf`.
 

## Libraries Needed
* BeautifulSoup4, install via `pip install beautifulsoup4`
* Python 3.7 is recommended

## Instructions
1)`rocchio_rerank.sh [query-file] [top-100-file] [collection-dir] [output-file]` to rerank the results where,  
* `query-file` : file containing the queries in the same xml form as the training
queries released for example `/covid19-topics.xml`
* `top-100-file` : a file containing the top100 documents in the same format as
train and dev top100 files given, which need to be reranked for example `/t40-top-100.txt`
* `collection-dir`: directory containing the full document collection. Specifically, it will have metadata.csv, a subdirectory named document parses which in turn contains subdirectories pdf json and pmc json. See [link](https://github.com/allenai/cord19/blob/master/README.md) for more information.
* `output-file`: is the name of the file in which you want your results.  

2)`python evaluate.py [ground-truth-file] [output-file]` to evaluate the nDCG and MAP metric, where
* `ground-truth-file` : file containting actual relevance of some documents for each query, for example in `t40-qrels.txt`
* `output-file` : file containing results from previous command