import urllib.request
import requests
import bibtexparser
from bibtexparser.bparser import BibTexParser
from bibtexparser.bibdatabase import BibDatabase
'''https://gist.github.com/dhimmel/719fc5e3a21dd2779d9fe69bf41e6ba6'''
def shorten(doi, cache={}, verbose=False):
    """
    Get the shortDOI for a DOI. Providing a cache dictionary will prevent
    multiple API requests for the same DOI.
    """
    if doi in cache:
        return cache[doi]
    quoted_doi = urllib.request.quote(doi)
    url = 'http://shortdoi.org/{}?format=json'.format(quoted_doi)
    try:
        response = requests.get(url).json()
        short_doi = response['ShortDOI']
    except Exception as e:
        if verbose:
            print(doi, 'failed with', e)
        return None
    cache[doi] = short_doi
    return short_doi

def get_bibtext(doi, cache={}):
    """
    Use DOI Content Negotioation (http://crosscite.org/cn/) to retrieve a string
    with the bibtex entry.
    """
    if doi in cache:
        return cache[doi]
    url = 'https://doi.org/' + urllib.request.quote(doi)
    header = {
        'Accept': 'application/x-bibtex',
    }
    response = requests.get(url, headers=header)
    bibtext = response.text
    if bibtext:
        cache[doi] = bibtext
    return bibtext

def get_bibtex_entry(doi, bibtext_cache={}, shortdoi_cache={}):
    """
    Return a bibtexparser entry for a DOI
    """
    bibtext = get_bibtext(doi, cache = bibtext_cache)
    if not bibtext:
        return None

    short_doi = shorten(doi, cache = shortdoi_cache)
    parser = BibTexParser()
    parser.ignore_nonstandard_types = False
    bibdb = bibtexparser.loads(bibtext, parser)
    entry, = bibdb.entries
    quoted_doi = urllib.request.quote(doi)
    entry['link'] = 'https://doi.org/{}'.format(quoted_doi)
    if 'author' in entry:
        entry['author'] = ' and '.join(entry['author'].rstrip(';').split('; '))
    entry['ID'] = short_doi[3:]
    return entry

def entries_to_str(entries):
    """
    Pass a list of bibtexparser entries and return a bibtex formatted string.
    """
    db = BibDatabase()
    db.entries = entries
    return bibtexparser.dumps(db)

import habanero, os, shutil
from pprint import pprint

def process_cr_result(res, paper_title, src, dst):
    print('\tCrossRef found', len(res['message']['items']), 'results.')
    print('\t\t', paper_title)

    bool_found_in_first_crossref_query = False
    mymatches = []
    for index, item in enumerate(res['message']['items']):

        crossref_title = item['title'][0]
        crossref_title = crossref_title.replace('-', ' ')
        crossref_title = crossref_title.replace('/', ' ')
        crossref_title = crossref_title.replace(':', ' ')
        crossref_title = crossref_title.replace(',', ' ')
        crossref_title = crossref_title.replace('"', ' ')
        crossref_title = crossref_title.lower()
        words = crossref_title.split()

        number_of_matches = len([word for word in words if word in paper_title])

        print('\t\t', crossref_title, '(words:', len(words), number_of_matches, 'matches)' )

        # if paper_title in item['title'][0]:
        if abs(len(words) - number_of_matches) < 3:
            mymatches.append(item)
            if len(words) != number_of_matches:
                print('\twhich is a close but not exact match exists:')
                # print('\t', paper_title)
                # print('\t', words)
                # print('\t', bibtex)
                # print()
                # shutil.copy(src, dst)
                continue # 题目没完全对上
            else:
                bibtex_dict = get_bibtex_entry(item['DOI'])
                if bibtex_dict is None:
                    print('[Error] You need to manuall add bibtex for this paper:', item['DOI'], paper_title)
                try:
                    bibtex_dict['CitedBy'] = str(habanero.counts.citation_count(doi=item['DOI']))
                except Exception as e:
                    print('[Error] CB:', habanero.counts.citation_count(doi=item['DOI']))

                bibtex = entries_to_str([bibtex_dict])
                f.write(bibtex + '\n')
                bool_found_in_first_crossref_query = True
                print('\tDone.')

                if len(mymatches) > 1:
                    print('Here is the list of the close matches:')
                    for el in mymatches:
                        print(el)
                break # the first one should be the most relervant for most cases
        else:
            continue # 题目对不上
    return bool_found_in_first_crossref_query

def process_paper_title(paper_title):
    paper_title = paper_title.replace('-', ' ')
    paper_title = paper_title.replace('"', ' ')
    paper_title = paper_title.lower()
    return paper_title

if __name__ == '__main__':

    pdf_saved_folder = r'D:\horyc\Downloads\Documents\IEEExplore'
    dst = './auto-references/'
    if not os.path.exists(dst):
        os.mkdir(dst)

    f = open('auto-references.bib', 'w')

    cr = habanero.Crossref() # https://habanero.readthedocs.io/en/latest/modules/crossref.html
    count = 0
    for root, dirs, files in os.walk(pdf_saved_folder):
        for name in files:
            if '.pdf' not in name:
                continue

            src = os.path.join(root, name)
            # print(src)

            # 搜要用IEEExpolore给你的名字去搜
            res = cr.works( query = name[:-4].replace('_', ' '), select = ["DOI", "title"], limit = 100)
            paper_title = process_paper_title( name[:-4].replace('_', ' ') )
            print('\n-----', count); count+=1
            bool_found_in_first_crossref_query = process_cr_result(res, paper_title, src, dst)

            if not bool_found_in_first_crossref_query:
                # res = cr.works( query = name[:-4].replace('_', ' '), select = ["DOI", "title"], limit = 100)
                # paper_title = process_paper_title( name[:-4].replace('_', ' ') )
                # if not (process_cr_result(res, paper_title)):
                print('=========================')
                print(res['message']['items'])
                raise Exception(f'Not found by Crossref: {src}')
    f.close()
