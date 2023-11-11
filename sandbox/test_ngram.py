#%%
import json
import re
from pathlib import Path
from tqdm import tqdm
from dotenv import load_dotenv
HERE = Path(__file__).resolve().parent
HERE_ = str(HERE).replace(HERE.stem, '')
HERE = Path(HERE_)
load_dotenv(HERE / ".env", override=True)
from collections import defaultdict

import math
from operator import itemgetter
from fdparsedoc.parsedoctypes import DocText
import nltk
from nltk.corpus import wordnet
from nltk.corpus import stopwords

# Initialize NLTK (download WordNet if not already downloaded)
nltk.download('wordnet')
stop_words = set(stopwords.words('english'))

#%%
def ngramgen(text, n):
    words = text.split()
    for i in range(len(words)-n):
        yield " ".join(words[i:i+n])

#%%
## some words are hanging, happens because structure of PDFs is not similar.
## This function tries to rejoin incomplete english words
def check_word_grammar(pos, item):
    item_clean = re.sub(r'[\n.,()]', '', item.lower())
    item_clean = item_clean.replace("’s", '')
    if item_clean not in stop_words:
        synsets = wordnet.synsets(item_clean)
        if synsets and len(item_clean) > 1:
            pass
        else:
            ## check if it does not contain numbers/digits
            pattern = r'\d'
            if not re.search(pattern, item_clean):
                complete = combinations[pos] + combinations[pos+1]
                synsets = wordnet.synsets(complete)
                if synsets:
                    combinations[pos] = complete
                    combinations.pop(pos+1)
                    print(complete, pos)
                else:
                    complete = combinations[pos-1] + combinations[pos]
                    synsets = wordnet.synsets(complete)
                    if synsets:
                        combinations[pos] = complete
                        combinations.pop(pos-1)
                        print(complete, pos)
        return item
    
#%%
## loading the pdf file
datapath_folder = Path(r"D:/Profession/Fab Inc Dropbox/Fab Inc Other/_Organised bank/Resources/IEFG/Donors_Partners/firelightfoundation")#Path(r"D:\Fab_data\web_data\Global-Proficiency-Framework-Reading.pdf")
pdf_docs_path  = datapath_folder.glob('*.pdf')
pdf_docs = []
for doc in pdf_docs_path:
    pdf_docs.append(doc)
doc = DocText.from_file(pdf_docs[15])
chunks = list(doc.chunks(chunksize=4000))

#%%
## removing whitespaces and just cleaning the text
## saving the pages into an iterable list
concatenated_pages = [] 
text = [concatenated_pages.append(doc.pages[i]) for i in range(len(doc.pages))]

new_doc = ' '.join(concatenated_pages) # joining the pages into one continuous string.
new_combinations = ' '.join(new_doc.split()) # splitting by space(s) and only joining by one space
combinations = new_combinations.split()
all_sentences = new_combinations.split('.')

#%%
## convert each word to lower case and remove special characters included with the word
combinations = [(re.sub(r'[\n.,()?!:]', '', item.lower())) for item in combinations]

# some words are incomplete. Checking for them and trying to do a quick simple completion
gen = [check_word_grammar(index, item) for index,item in enumerate(combinations)]
corrected_doc = ' '.join(combinations)
test_text = corrected_doc
doc_text = nltk.word_tokenize(test_text)

input_text = [word for word in doc_text if word.lower() not in stop_words]
input_text = ' '.join(input_text)
total_words = len(combinations)
total_sentences = len(all_sentences)
#%%
counter = defaultdict(lambda: defaultdict(lambda: 0))

#%%
n_max = 4

for n in range(1, n_max+1):
    for ng in ngramgen(test_text, n):
        counter[n][ng] += 1
    counter[n] = {
        key: val 
        for key, val in sorted(
            counter[n].items(), key=lambda x: x[1], reverse=True
        )
    }
# %%
context = []
for level in range(1, len(counter)+1):
    keywords_freq = counter[level]
    for keyword in keywords_freq.keys():
        split_keyword = keyword.split()
        status = False
        for word in split_keyword:
            word = re.sub(r'[\n.,()-]', '', word.lower())
            if word not in stop_words:
                continue
            else:
                status = True
        if not status:
            context.append(re.sub(r'[\n.,()-]', '', keyword.lower()))
    

# %%
## just a trial/test
## removing digits
context_clean = [con for con in context if not re.search(r'\d', con)]
recounter = defaultdict(lambda: defaultdict(lambda: 0))
for con in context_clean:
    dish = 0
    for page in concatenated_pages:
        if con in page:
            dish += 1
    recounter[con] = dish

# %%
edit_combinations = [(re.sub(r'[\n.,()!?/\@|#]', '', combo.lower())) for combo in combinations if not re.search(r'\d', combo)]
#%%
word_list_counter = []
def calculate_frequencies(word):
    global word_list_counter
    pages_found = 0
    sentences_found = 0
    ## word frequency
    if word not in stop_words and word:
        word_counter = edit_combinations.count(word)
        word_dict = {
            word: word_counter / total_words * 100
        }
        word_list_counter.append(word_dict)
    
        ## page frequency
        for page in concatenated_pages:
            if word in page.lower():
                pages_found += 1

        page_dict = {
            word: pages_found / len(concatenated_pages)
        }

        ## sentence frequency
        for sentence in all_sentences:
            if word in sentence.lower():
                sentences_found += 1
        
        sentence_dict = {
            word: sentences_found / len(all_sentences)
        }
        combined_freq = list(word_dict.values())[0] + list(page_dict.values())[0] + list(sentence_dict.values())[0]
        return {word:combined_freq*100}
        
redit_combinations = list(set(edit_combinations))
test = [calculate_frequencies(word) for word in redit_combinations]
test = [item for item in test if item is not None]
#%%
data_freq = sorted(test, key=lambda x: list(x.values())[0], reverse=True)
filtered_data = [item for item in data_freq if len(list(item.keys())[0]) >= 3]
# %%
## function to use TF-IDF
## calculating TF for each word
# Step 3: Calculate TF for each word
tf_score = {}

for word in tqdm(edit_combinations):
    word = word.strip()
    word = re.sub(r'[\n.,()]', '', word.lower())
    if word.lower() not in stop_words:
        if word in tf_score:
            tf_score[word] += 1
        else:
            tf_score[word] = 1

print(tf_score)
# %%
# Dividing by total_word_length for each dictionary element
tf_score.update((x, y/int(total_words)) for x, y in tf_score.items())

print(tf_score)
# %%
# Check if a word is there in sentence list
def check_sent(word, sentences): 
    cnt = 0

    for sent in sentences:

        usesent = (

            " ".join(sent.split())

            .replace(".", "")

            .replace(")", "")

            .replace("(", "")

            .lower()

        )

        cnt += word in usesent

    return cnt


#%%
# Step 4: Calculate IDF for each word
idf_score = {}

for word in tqdm(edit_combinations):
    word = re.sub(r'[\n.,()?:]', '', word.lower())
    if word not in stop_words:
        if word not in idf_score:
            idf_score[word] = check_sent(word, all_sentences)

#%%
# Performing a log and divide
idf_score.update((x, math.log(int(total_sentences)/y)) for x, y in idf_score.items() if y>0)

print(idf_score)

#%%
# Step 5: Calculating TF*IDF
tf_idf_score = {key: tf_score[key] * idf_score.get(key, 0) for key in tf_score.keys()} 
print(tf_idf_score)

#%%
# Get top N important words in the document
def get_top_n(dict_elem, n):
    result = dict(sorted(dict_elem.items(), key = itemgetter(1), reverse = True)[:n]) 
    return result

print(get_top_n(tf_idf_score, 5))
target = get_top_n(tf_idf_score, 20)
# %%
