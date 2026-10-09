#!/usr/bin/env python3
"""Choose about 900 more buildings from tools/harvest/candidates.json for architecture students.

Scores favour modern and contemporary work, architects students study, and fame (Wikipedia
language editions); generic transit stations, stadiums and hotels score low; older buildings
are kept to a few precedents. Each architect is capped and each region has a target share.
Writes tools/harvest/selected.json and a readable tools/harvest/selected.txt for review.
"""
import json, math, re, sys, unicodedata
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CAND = ROOT / 'tools' / 'harvest' / 'candidates.json'
OUT = ROOT / 'tools' / 'harvest' / 'selected.json'
TXT = ROOT / 'tools' / 'harvest' / 'selected.txt'
TARGET = 1400  # overselect; the curation pass keeps about 900
COUNTRY_CAP = {'United States': 190, 'Germany': 85, 'France': 75, 'United Kingdom': 75, 'Japan': 105, "People's Republic of China": 70, 'Spain': 60, 'Italy': 60, 'Russia': 35}

STARS = '''Le Corbusier|Ludwig Mies van der Rohe|Mies van der Rohe|Frank Lloyd Wright|Alvar Aalto|Louis Kahn|Oscar Niemeyer|Kenzō Tange|Kenzo Tange|Tadao Ando|Zaha Hadid|Zaha Hadid Architects|Frank Gehry|Rem Koolhaas|Office for Metropolitan Architecture|OMA|Herzog & de Meuron|Renzo Piano|Renzo Piano Building Workshop|Norman Foster|Foster and Partners|Foster + Partners|Richard Rogers|Rogers Stirk Harbour + Partners|SANAA|Kazuyo Sejima|Ryue Nishizawa|Toyo Ito|Toyō Itō|Sou Fujimoto|Kengo Kuma|Shigeru Ban|Jean Nouvel|Peter Zumthor|Álvaro Siza|Álvaro Siza Vieira|Eduardo Souto de Moura|Rafael Moneo|Carlo Scarpa|Aldo Rossi|Luis Barragán|Lina Bo Bardi|Paulo Mendes da Rocha|Balkrishna Doshi|B. V. Doshi|Charles Correa|Geoffrey Bawa|Laurie Baker|Hassan Fathy|Diébédo Francis Kéré|Francis Kéré|David Adjaye|Glenn Murcutt|Jørn Utzon|Arne Jacobsen|Sverre Fehn|Snøhetta|Bjarke Ingels|Bjarke Ingels Group|BIG|MVRDV|UNStudio|Ben van Berkel|Daniel Libeskind|Steven Holl|Santiago Calatrava|I. M. Pei|Eero Saarinen|Marcel Breuer|Walter Gropius|Philip Johnson|Paul Rudolph|Kisho Kurokawa|Arata Isozaki|Fumihiko Maki|Kunio Maekawa|Antoni Gaudí|Adolf Loos|Otto Wagner|Josef Hoffmann|Erich Mendelsohn|Hans Scharoun|Gottfried Böhm|Frei Otto|Günter Behnisch|Egon Eiermann|James Stirling|Denys Lasdun|Alison and Peter Smithson|Ernő Goldfinger|Moshe Safdie|Richard Meier|Robert Venturi|Denise Scott Brown|Michael Graves|Mario Botta|Jean Prouvé|Auguste Perret|Pier Luigi Nervi|Giuseppe Terragni|Gio Ponti|Eladio Dieste|Félix Candela|Vilanova Artigas|Lúcio Costa|Affonso Eduardo Reidy|Clorindo Testa|Ricardo Legorreta|Alejandro Aravena|Wang Shu|Ma Yansong|MAD Architects|Raj Rewal|Achyut Kanvinde|Sedad Hakkı Eldem|Rifat Chadirji|WOHA|Henning Larsen|Lacaton & Vassal|David Chipperfield|Peter Eisenman|Coop Himmelb(l)au|Morphosis|Thom Mayne|Diller Scofidio + Renfro|Bernard Tschumi|Riken Yamamoto|Itsuko Hasegawa|Junya Ishigami|Harry Seidler|Alvaro Siza|Rudolf Steiner|Hector Guimard|Victor Horta|Henry van de Velde|Charles Rennie Mackintosh|Eliel Saarinen|Gunnar Asplund|Sigurd Lewerentz|Erik Gunnar Asplund|Kay Fisker|Hendrik Petrus Berlage|Willem Marinus Dudok|J. J. P. Oud|Gerrit Rietveld|Johannes Duiker|Aldo van Eyck|Herman Hertzberger|Bruno Taut|Peter Behrens|Hans Poelzig|Konstantin Melnikov|Moisei Ginzburg|Ivan Leonidov|Vladimir Tatlin|Le Corbusier and Pierre Jeanneret|Pierre Chareau|Robert Mallet-Stevens|Eileen Gray|Richard Neutra|Rudolph Schindler|Rudolph M. Schindler|Charles and Ray Eames|Craig Ellwood|Pierre Koenig|John Lautner|Bruce Goff|Buckminster Fuller|R. Buckminster Fuller|Kevin Roche|Gordon Bunshaft|Skidmore, Owings & Merrill|SOM|Minoru Yamasaki|Bertrand Goldberg|Fazlur Rahman Khan|Ludwig Hilberseimer|Eero Saarinen and Associates|Marcel Breuer and Associates|Josep Lluís Sert|Antonio Bonet|Amancio Williams|Mathias Goeritz|Juan O'Gorman|Rogelio Salmona|Carlos Raúl Villanueva|Oscar Niemeyer and Lúcio Costa|Roberto Burle Marx|Smiljan Radić|Teodoro González de León|Abraham Zabludovsky|Enric Miralles|Miralles Tagliabue EMBT|RCR Arquitectes|Rafael Aranda|Carme Pigem|Ramón Vilalta|Josep Maria Jujol|Ricardo Bofill|José Antonio Coderch|Alejandro de la Sota|Francisco Javier Sáenz de Oiza|Miguel Fisac|Fernando Távora|Gonçalo Byrne|João Luís Carrilho da Graça|Kenzo Tange Associates|Kiyonori Kikutake|Yoshio Taniguchi|Kazuo Shinohara|Takamitsu Azuma|Shin Takamatsu|Hiroshi Hara|Atelier Bow-Wow|Akihisa Hirata|Go Hasegawa|Terunobu Fujimori|Jun Aoki|Kengo Kuma and Associates|Toyo Ito & Associates|Wang Shu and Lu Wenyu|Amateur Architecture Studio|Liu Jiakun|Li Xiaodong|Zhang Ke|Neri&Hu|Kerez|Christian Kerez|Valerio Olgiati|Mario Cucinella|Massimiliano Fuksas|Stefano Boeri|Gae Aulenti|Ignazio Gardella|BBPR|Luigi Moretti|Paolo Portoghesi|Carlo Mollino|Alvar Aalto and Aino Aalto|Reima Pietilä|Juha Leiviskä|Heikki Siren|Kaija Siren|JKMM|ALA Architects|Lahdelma & Mahlamäki|Wenche Selmer|Sverre Fehn and Geir Grung|Jan Gezelius|Peter Celsing|Ralph Erskine|3XN|Dorte Mandrup|Henning Larsen Architects|Lundgaard & Tranberg|COBE|Herzog & de Meuron Architekten|Gigon/Guyer|Diener & Diener|Mecanoo|Neutelings Riedijk Architecten|OMA/Rem Koolhaas|Rem Koolhaas and OMA|Toyo Ito and Associates|Kazuyo Sejima and Ryue Nishizawa|Alvaro Siza and Eduardo Souto de Moura|Tatiana Bilbao|Rozana Montiel|Mauricio Rocha|Frida Escobedo|Anupama Kundoo|Bijoy Jain|Studio Mumbai|Sanjay Puri|Kéré Architecture|Mariam Kamara|Kunlé Adeyemi|NLÉ|Demas Nwoko|Sean Godsell|Lyons|Denton Corker Marshall|John Wardle|Kerry Hill|Ken Yeang|Vo Trong Nghia|Bunyad Bostanci|Emre Arolat|Turgut Cansever|Kamran Diba|Hossein Amanat|Nader Ardalan|Hassan Fathy|Rasem Badran|Abdel-Wahed El-Wakil|Elie Azagury|Jean-François Zevaco|Pancho Guedes|Amancio d'Alpoim Miranda Guedes|Mies'''
STARS = {s.strip().lower() for s in STARS.split('|') if s.strip()}

REGION = {}
for region, names in {
    'Europe': 'United Kingdom|Germany|France|Spain|Italy|Portugal|Netherlands|Belgium|Luxembourg|Switzerland|Austria|Denmark|Norway|Sweden|Finland|Iceland|Ireland|Poland|Czech Republic|Slovakia|Hungary|Slovenia|Croatia|Serbia|Bosnia and Herzegovina|Montenegro|North Macedonia|Albania|Greece|Bulgaria|Romania|Moldova|Ukraine|Belarus|Lithuania|Latvia|Estonia|Russia|Malta|Cyprus|Monaco|Liechtenstein|Vatican City|Kingdom of the Netherlands|Kosovo|San Marino|Andorra|Faroe Islands|Soviet Union|German Democratic Republic|West Germany|Yugoslavia|Czechoslovakia',
    'Americas': 'United States|Canada|Mexico|Brazil|Argentina|Chile|Uruguay|Peru|Colombia|Venezuela|Ecuador|Bolivia|Paraguay|Cuba|Puerto Rico|Panama|Costa Rica|Guatemala|Dominican Republic|Jamaica|Trinidad and Tobago|Honduras|El Salvador|Nicaragua|Haiti|Bahamas|Barbados|Bermuda',
    'East Asia': "Japan|People's Republic of China|China|South Korea|North Korea|Taiwan|Hong Kong|Macau|Mongolia",
    'South Asia': 'India|Pakistan|Bangladesh|Sri Lanka|Nepal|Bhutan|Maldives|Afghanistan',
    'Southeast Asia': 'Singapore|Malaysia|Indonesia|Thailand|Vietnam|Philippines|Cambodia|Laos|Myanmar|Brunei|East Timor',
    'Middle East': 'Turkey|Israel|Iran|Iraq|Saudi Arabia|United Arab Emirates|Qatar|Kuwait|Bahrain|Oman|Jordan|Lebanon|Syria|Yemen|State of Palestine|Egypt|Azerbaijan|Armenia|Georgia|Kazakhstan|Uzbekistan|Turkmenistan|Kyrgyzstan|Tajikistan',
    'Africa': 'Morocco|Algeria|Tunisia|Libya|Nigeria|Ghana|Senegal|Burkina Faso|Mali|Niger|Kenya|Tanzania|Uganda|Rwanda|Ethiopia|South Africa|Mozambique|Angola|Zimbabwe|Zambia|Botswana|Namibia|Madagascar|Ivory Coast|Cameroon|Democratic Republic of the Congo|Republic of the Congo|Gabon|Sudan|Eritrea|Benin|Togo|Malawi|Mauritius|Sierra Leone|Liberia|Guinea',
    'Oceania': 'Australia|New Zealand|Fiji|Papua New Guinea',
}.items():
    for n in names.split('|'):
        REGION[n] = region
QUOTA = {'Europe': 500, 'Americas': 330, 'East Asia': 200, 'South Asia': 80, 'Southeast Asia': 70, 'Middle East': 100, 'Africa': 60, 'Oceania': 60}

MODERN_STYLES = re.compile(r'modern|brutal|high-tech|international style|deconstruct|neo-futur|futurist|contemporary|organic|expressionis|constructiv|functionalis|rationalis|neues bauen|metabol|parametric|postmodern|critical regionalism|bauhaus|minimalis|structural expressionism|neomodern', re.I)
TRANSIT = re.compile(r'station|metro|u-bahn|s-bahn|underground|subway|tram stop|bus station|interchange', re.I)
SPORT = re.compile(r'stadium|football|arena|ballpark|racecourse|race track|velodrome|ice hockey', re.I)
COMMERCE = re.compile(r'hotel|office building|shopping|department store|casino|bank building|retail|apartment building|condominium', re.I)
NOT_BUILDING = re.compile(r'statue|monument|memorial|city|municipality|human settlement|administrative|organization|company|business|district|neighbourhood|quarter|village|town|street|road|square|ship|vehicle|sculpture|fountain|cemetery|garden|airport|dam|power station|bridge', re.I)
OLD_GENERIC = re.compile(r'church|chapel|cathedral|basilica|castle|château|palace|palazzo|monastery|abbey|manor|fortress|temple|mosque|synagogue', re.I)


def fold(s):
    return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower()


def year(r):
    ys = [int(y) for y in (r.get('inception', []) + r.get('opened', [])) if isinstance(y, str) and y.lstrip('-').isdigit()]
    return min(ys) if ys else None


def existing():
    t = (ROOT / 'site' / 'data' / 'buildings.js').read_text()
    items = json.loads(t.split('window.BUILDINGS = ', 1)[1].rstrip().rstrip(';'))
    names = {fold(b['name']) for b in items}
    cats = {fold(b['commons'].split(':', 1)[-1]) for b in items if b.get('commons')}
    return names, cats


def score(r):
    y = year(r)
    arch = [a for a in r.get('architect', []) if isinstance(a, str)]
    star = any(a.lower() in STARS for a in arch)
    inst = ' '.join(r.get('instance', []))
    styles = ' '.join(r.get('style', []))
    s = math.log2(max(2, r['sitelinks']))
    s += -4 if y < 1850 else -2 if y < 1900 else 1 if y < 1945 else 2.5 if y < 1990 else 3
    s += 5 if star else 0
    s += 1.5 if MODERN_STYLES.search(styles) else 0
    if TRANSIT.search(inst):
        s -= 3 if star else 7
    if SPORT.search(inst):
        s -= 2 if star else 6
    if re.search(r'skyscraper|tower block|high-rise', inst, re.I) and not star:
        s -= 2.5
    if COMMERCE.search(inst) and not star:
        s -= 3
    if OLD_GENERIC.search(inst) and y < 1945 and not star:
        s -= 2
    if 'destroyed' in inst or 'demolished' in inst or (r.get('state') and any('demolish' in x or 'destroyed' in x for x in r['state'])):
        s -= 8
    if any(a.startswith('Q') and a[1:].isdigit() for a in arch) and not star:
        s -= 1.5
    return s, star


def main():
    C = json.loads(CAND.read_text())
    have_names, have_cats = existing()
    pool = []
    for r in C:
        y = year(r)
        label = r.get('label') or ''
        if not y or y > 2026 or not label or not (r.get('image') or r.get('commons')):
            continue
        arch = [a for a in r.get('architect', []) if isinstance(a, str)]
        if not arch or arch == ['architectural ensemble']:
            continue
        inst = ' '.join(r.get('instance', []))
        if NOT_BUILDING.search(inst) and not re.search(r'building|house|museum|church|library|hall|tower|pavilion|school|university|theatre|theater|chapel|villa|centre|center', inst, re.I):
            continue
        if fold(label) in have_names or fold((r.get('commons') or [''])[0]) in have_cats:
            continue
        country = (r.get('country') or ['?'])[0]
        region = REGION.get(country)
        if not region:
            continue
        s, star = score(r)
        pool.append({**r, 'year': y, 'region': region, 'score': round(s, 2), 'star': star})
    pool.sort(key=lambda r: -r['score'])
    per_arch, per_region, per_country, chosen, seen_cats = Counter(), Counter(), Counter(), [], set()
    old = 0
    for r in pool:
        if len(chosen) >= TARGET:
            break
        arch = r['architect'][0]
        cap = 7 if r['star'] else 3
        country = (r.get('country') or ['?'])[0]
        if per_arch[arch] >= cap or per_region[r['region']] >= QUOTA[r['region']] or per_country[country] >= COUNTRY_CAP.get(country, 60):
            continue
        per_country[country] += 1
        if r['year'] < 1900:
            if old >= 45:
                continue
            old += 1
        cat = (r.get('commons') or [None])[0]
        if cat and cat in seen_cats:
            continue
        seen_cats.add(cat)
        per_arch[arch] += 1
        per_region[r['region']] += 1
        chosen.append(r)
    # fill any shortfall from the best of what is left, ignoring region quotas
    for r in pool:
        if len(chosen) >= TARGET:
            break
        if r in chosen or per_arch[r['architect'][0]] >= (7 if r['star'] else 3) or r['year'] < 1900:
            continue
        per_arch[r['architect'][0]] += 1
        chosen.append(r)
    chosen.sort(key=lambda r: (r['region'], r['year']))
    OUT.write_text(json.dumps(chosen, ensure_ascii=False, indent=0))
    lines = [f"{r['qid']:>10} {r['score']:5.1f} {'*' if r['star'] else ' '} {r['year']} {r['region'][:9]:9} {(r.get('country') or ['?'])[0][:14]:14} | {r['label']} — {', '.join(r['architect'][:2])} | {', '.join(r.get('instance', [])[:2])}" for r in chosen]
    TXT.write_text('\n'.join(lines) + '\n')
    print(len(chosen), Counter(r['region'] for r in chosen), 'stars', sum(r['star'] for r in chosen), 'pre-1900', sum(r['year'] < 1900 for r in chosen))


if __name__ == '__main__':
    sys.exit(main())
