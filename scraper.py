import scraperwiki
import lxml.html
import re
from urllib2 import urlopen

BASE_URL = 'http://bridgehunter.com/'
SLUG_REGEX = re.compile('^[A-Za-z_]\w{0,64}$')
RIVER_REGEX = re.compile('<a href="/category/waterway/(.*)/"')
BRIDGE_REGEX = re.compile("<div class=\"x\"><a href=\"/(.*)/\" class=\"name\">")

try:
    import unidecode
    def slugify(verbose_name):
        slug = re.sub(r'\W+','_',unidecode.unidecode(verbose_name).lower())
        if not SLUG_REGEX.match(slug):
            slug = '_'+slug
        return slug 
except:
    def slugify(verbose_name):
        slug = re.sub(r'\W+','_',verbose_name.lower())
        if not SLUG_REGEX.match(slug):
            slug = '_'+slug
        return slug 


def bridges_in_county(state, county):
    '''
    Return list of bridge IDs in a given country.
    '''
    url = '%s%s/%s/' % (BASE_URL, state, county)
    root = lxml.html.fromstring(scraperwiki.scrape(url))

    return [link.attrib['href'].split('/')[-2] for link in root.cssselect('div.x a.name')]

def rivers():
    url = '%scategory/waterway/' % BASE_URL
    return RIVER_REGEX.findall(urlopen(url).read())

def bridges_on_river(river):
    url = '%scategory/waterway/%s/' % (BASE_URL, river)
    return [dict(river=river, state=bridge.split('/')[0], county=bridge.split('/')[1], bridge=bridge.split('/')[2]) for bridge in BRIDGE_REGEX.findall(urlopen(url).read())]

def counties_in_state(state):
    '''
    Return list of counties in a state.
    '''
    url = '%s%s/' % (BASE_URL, state)
    root = lxml.html.fromstring(scraperwiki.scrape(url))

    return [link.attrib['href'].split('/')[-2] for link in root.cssselect('map area')]

def bridge_data(state, county, bridge):
    '''
    Return dictionary of bridge data.
    '''
    url = '%s%s/%s/%s/' % (BASE_URL, state, county, bridge)
    try:
        root = lxml.html.fromstring(scraperwiki.scrape(url))
    except:
        return None

    name = list(root.cssselect('h1'))[0].text

    data = dict(name = name)

    for field in root.cssselect('div.section dl'):
        key = None
        for subfield in field:
            if subfield.tag == 'dt':
                key = slugify(unicode(subfield.xpath('string()')))
            elif key is not None:
                data[key] = unicode(subfield.xpath('string()'))

    data['state'] = state
    data['county'] = county
    data['bridge'] = bridge
    return data


for river in rivers():
    for row in bridges_on_river(river):
        state = row['state']
        county = row['county']
        bridge = row['bridge']
        try:
            data = bridge_data(state, county, bridge)
            data['river'] = river
            if data is not None:
                scraperwiki.sqlite.save(unique_keys=['state', 'county', 'bridge'], data=data)

        except scraperwiki.sqlite.SqliteError, e:
            print str(e)

