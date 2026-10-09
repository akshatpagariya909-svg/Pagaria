#!/usr/bin/env python3
"""The student-focused 100, as data. Edit the rows below, then run:

  python3 tools/students_list.py     # writes site/data/buildings.js (keeps any images already fetched)

Each row: name, architect, place ("City, CC"), year, typology, movement, three concepts, "Study it for" line.
Concepts come from the CONCEPTS vocabulary so filters stay tidy.
"""
import json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'site' / 'data' / 'buildings.js'

CONCEPTS = [
    'Adaptive reuse', 'Axis', 'Brick', 'Brise-soleil', 'Cantilever', 'Circulation', 'Climate response', 'Cluster',
    'Colour', 'Community', 'Courtyard', 'Detail', 'Digital fabrication', 'Double height', 'Earth & local material',
    'Exposed concrete', 'Facade as skin', 'Free plan', 'Geometry', 'Incremental', 'Landscape', 'Light & shadow',
    'Light from above', 'Low cost', 'Megastructure', 'Modular', 'Monumentality', 'Parametric', 'Pilotis', 'Planting',
    'Prefabrication', 'Promenade', 'Public space', 'Reclaimed material', 'Section', 'Sculptural form', 'Steel & glass',
    'Stone', 'Structure as expression', 'Tensile structure', 'Timber', 'Vault', 'Void', 'Water', 'Human comfort',
]

ROWS = [
 # Modern masters
 ('Villa Savoye', 'Le Corbusier', 'Poissy, FR', '1931', 'House', 'Modernism', ['Pilotis', 'Free plan', 'Promenade'], "Le Corbusier's Five Points of Architecture in a single house."),
 ("Unité d'Habitation", 'Le Corbusier', 'Marseille, FR', '1952', 'Housing', 'Brutalism', ['Exposed concrete', 'Modular', 'Brise-soleil'], 'A vertical neighbourhood: interlocking duplex flats served by internal streets.'),
 ('Notre-Dame du Haut', 'Le Corbusier', 'Ronchamp, FR', '1955', 'Religious', 'Modernism', ['Sculptural form', 'Light & shadow', 'Exposed concrete'], 'Thick walls punched with deep, coloured windows that model the light.'),
 ('Sainte-Marie de La Tourette', 'Le Corbusier', 'Éveux, FR', '1960', 'Religious', 'Brutalism', ['Courtyard', 'Exposed concrete', 'Pilotis'], 'A monastery on a slope: cells, cloister and church around a courtyard.'),
 ('Palace of Assembly', 'Le Corbusier', 'Chandigarh, IN', '1962', 'Civic', 'Brutalism', ['Brise-soleil', 'Monumentality', 'Climate response'], 'A parliament built for the Punjab sun: portico, brise-soleil and a hyperboloid chamber.'),
 ("Mill Owners' Association Building", 'Le Corbusier', 'Ahmedabad, IN', '1954', 'Office & tower', 'Modernism', ['Brise-soleil', 'Promenade', 'Climate response'], 'Angled concrete fins and a ramp turn a small office into a lesson in shading.'),
 ('Barcelona Pavilion', 'Mies van der Rohe, Lilly Reich', 'Barcelona, ES', '1929', 'Pavilion', 'Modernism', ['Free plan', 'Steel & glass', 'Water'], 'Free-standing walls under a floating roof: space that flows instead of rooms.'),
 ('Villa Tugendhat', 'Mies van der Rohe', 'Brno, CZ', '1930', 'House', 'Modernism', ['Free plan', 'Steel & glass', 'Landscape'], 'The open plan in a family home, with glass walls that drop away to the garden.'),
 ('Farnsworth House', 'Mies van der Rohe', 'Plano, US', '1951', 'House', 'Modernism', ['Steel & glass', 'Free plan', 'Landscape'], 'A single glass room lifted above a floodplain on eight steel columns.'),
 ('S. R. Crown Hall', 'Mies van der Rohe', 'Chicago, US', '1956', 'Education', 'Modernism', ['Steel & glass', 'Structure as expression', 'Free plan'], 'A clear-span hall for architecture students, its roof hung from four exposed girders.'),
 ('Seagram Building', 'Mies van der Rohe', 'New York, US', '1958', 'Office & tower', 'Modernism', ['Steel & glass', 'Facade as skin', 'Public space'], 'Set back behind a plaza, with bronze mullions that express the frame.'),
 ('Neue Nationalgalerie', 'Mies van der Rohe', 'Berlin, DE', '1968', 'Museum', 'Modernism', ['Steel & glass', 'Structure as expression', 'Free plan'], 'One column-free glass hall under a steel roof resting on eight columns.'),
 ('Fallingwater', 'Frank Lloyd Wright', 'Mill Run, US', '1939', 'House', 'Modernism', ['Cantilever', 'Landscape', 'Water'], 'Concrete terraces cantilevered over a waterfall: building and site as one.'),
 ('Johnson Wax Headquarters', 'Frank Lloyd Wright', 'Racine, US', '1939', 'Office & tower', 'Modernism', ['Light from above', 'Structure as expression', 'Double height'], "A forest of slender 'lily pad' columns under a glowing glass-tube roof."),
 ('Solomon R. Guggenheim Museum', 'Frank Lloyd Wright', 'New York, US', '1959', 'Museum', 'Modernism', ['Promenade', 'Light from above', 'Sculptural form'], 'One continuous spiral ramp around a skylit atrium replaces floors and rooms.'),
 ('Bauhaus Dessau', 'Walter Gropius', 'Dessau, DE', '1926', 'Education', 'Modernism', ['Steel & glass', 'Facade as skin', 'Free plan'], 'A pinwheel plan, with a glass curtain wall wrapping the workshops.'),
 ('Rietveld Schröder House', 'Gerrit Rietveld', 'Utrecht, NL', '1924', 'House', 'Modernism', ['Free plan', 'Colour', 'Cantilever'], 'De Stijl in three dimensions: floating planes and sliding partitions.'),
 ('Paimio Sanatorium', 'Alvar Aalto', 'Paimio, FI', '1933', 'Health', 'Modernism', ['Human comfort', 'Light & shadow', 'Landscape'], 'Ceilings, basins and door handles all designed around patients lying in bed.'),
 ('Villa Mairea', 'Alvar Aalto', 'Noormarkku, FI', '1939', 'House', 'Modernism', ['Timber', 'Courtyard', 'Landscape'], 'Modernism softened with timber, a forest of poles and an L-shaped courtyard.'),
 ('Säynätsalo Town Hall', 'Alvar Aalto', 'Jyväskylä, FI', '1952', 'Civic', 'Modernism', ['Brick', 'Courtyard', 'Timber'], 'A brick town hall around a raised grass courtyard, with timber trusses over the council.'),
 ('Eames House', 'Charles and Ray Eames', 'Los Angeles, US', '1949', 'House', 'Modernism', ['Modular', 'Steel & glass', 'Colour'], 'A Case Study House assembled from off-the-shelf industrial parts.'),
 ('Glass House', 'Philip Johnson', 'New Canaan, US', '1949', 'House', 'Modernism', ['Steel & glass', 'Landscape', 'Free plan'], 'A glass box whose walls are the landscape; only the bathroom is enclosed.'),
 ('Casa Luis Barragán', 'Luis Barragán', 'Mexico City, MX', '1948', 'House', 'Regionalism', ['Colour', 'Light & shadow', 'Courtyard'], 'A blank wall to the street, and colour, light and gardens within.'),
 ('Cathedral of Brasília', 'Oscar Niemeyer', 'Brasília, BR', '1970', 'Religious', 'Modernism', ['Structure as expression', 'Light from above', 'Sculptural form'], 'Sixteen curved concrete columns around a sunken, light-filled nave.'),
 ('Hiroshima Peace Memorial Museum', 'Kenzo Tange', 'Hiroshima, JP', '1955', 'Museum', 'Modernism', ['Pilotis', 'Exposed concrete', 'Axis'], 'Raised on pilotis and aligned on an axis with the A-Bomb Dome.'),
 ('Golconde', 'Antonin Raymond, George Nakashima', 'Puducherry, IN', '1945', 'Housing', 'Modernism', ['Climate response', 'Brise-soleil', 'Timber'], "Often called India's first modernist building: a dormitory cooled by pivoting louvres."),
 # Late modern and brutalism
 ('Salk Institute', 'Louis Kahn', 'La Jolla, US', '1965', 'Workplace', 'Late modernism', ['Exposed concrete', 'Water', 'Courtyard'], 'Laboratories with service floors between them, around a travertine plaza open to the Pacific.'),
 ('Phillips Exeter Academy Library', 'Louis Kahn', 'Exeter, US', '1971', 'Education', 'Late modernism', ['Light from above', 'Brick', 'Double height'], 'Books around a central atrium framed by huge circles; reading carrels at the brick edge.'),
 ('Kimbell Art Museum', 'Louis Kahn', 'Fort Worth, US', '1972', 'Museum', 'Late modernism', ['Light from above', 'Vault', 'Exposed concrete'], 'Cycloid vaults split by a slot of daylight bounced off reflectors.'),
 ('IIM Ahmedabad', 'Louis Kahn', 'Ahmedabad, IN', '1974', 'Education', 'Late modernism', ['Brick', 'Courtyard', 'Climate response'], 'Brick arches tied with concrete, and deep shaded spaces against the Gujarat heat.'),
 ('National Assembly of Bangladesh', 'Louis Kahn', 'Dhaka, BD', '1982', 'Civic', 'Late modernism', ['Monumentality', 'Water', 'Light & shadow'], 'Geometric cut-outs carve light into a concrete citadel set in a lake.'),
 ('Yale Art and Architecture Building', 'Paul Rudolph', 'New Haven, US', '1963', 'Education', 'Brutalism', ['Exposed concrete', 'Section', 'Double height'], 'Dozens of interlocking levels and corduroy concrete: a design studio built in section.'),
 ('Boston City Hall', 'Kallmann McKinnell & Knowles', 'Boston, US', '1968', 'Civic', 'Brutalism', ['Exposed concrete', 'Monumentality', 'Public space'], "An inverted ziggurat whose form shows the city government's functions from outside."),
 ('Yoyogi National Gymnasium', 'Kenzo Tange', 'Tokyo, JP', '1964', 'Culture & sport', 'Late modernism', ['Tensile structure', 'Structure as expression', 'Sculptural form'], 'A suspension roof hung from two concrete masts, built for the 1964 Olympics.'),
 ('Habitat 67', 'Moshe Safdie', 'Montréal, CA', '1967', 'Housing', 'Brutalism', ['Modular', 'Megastructure', 'Prefabrication'], "354 prefabricated modules stacked so each flat gets a garden on a neighbour's roof."),
 ('FAU-USP Building', 'Vilanova Artigas', 'São Paulo, BR', '1969', 'Education', 'Brutalism', ['Exposed concrete', 'Light from above', 'Promenade'], 'An architecture school under one great roof, joined by ramps and open to the city.'),
 ('MASP', 'Lina Bo Bardi', 'São Paulo, BR', '1968', 'Museum', 'Brutalism', ['Public space', 'Structure as expression', 'Exposed concrete'], 'A 74-metre span lifts the galleries to keep the plaza and the view open.'),
 ('SESC Pompéia', 'Lina Bo Bardi', 'São Paulo, BR', '1986', 'Culture & sport', 'Brutalism', ['Adaptive reuse', 'Exposed concrete', 'Public space'], 'A drum factory kept as a leisure centre, with new concrete towers linked by bridges.'),
 ('Trellick Tower', 'Ernő Goldfinger', 'London, UK', '1972', 'Housing', 'Brutalism', ['Exposed concrete', 'Circulation', 'Section'], 'Lifts in a separate tower, bridging to the flats every third floor.'),
 ('Barbican Estate', 'Chamberlin, Powell and Bon', 'London, UK', '1982', 'Housing', 'Brutalism', ['Exposed concrete', 'Megastructure', 'Water'], 'A walkway city of housing, arts centre, lake and conservatory above the street.'),
 ('Sydney Opera House', 'Jørn Utzon', 'Sydney, AU', '1973', 'Culture & sport', 'Late modernism', ['Sculptural form', 'Structure as expression', 'Prefabrication'], 'Shells cut from one sphere so they could be prefabricated, on a stepped podium.'),
 ('Bagsværd Church', 'Jørn Utzon', 'Copenhagen, DK', '1976', 'Religious', 'Late modernism', ['Light from above', 'Vault', 'Exposed concrete'], 'A plain industrial shell outside; inside, a billowing concrete ceiling washed with daylight.'),
 ('Nakagin Capsule Tower', 'Kisho Kurokawa', 'Tokyo, JP', '1972', 'Housing', 'Metabolism', ['Modular', 'Prefabrication', 'Megastructure'], 'Prefabricated capsules bolted to two cores: the Metabolist idea of replaceable parts.'),
 # Regionalism and the Global South
 ('Gandhi Smarak Sangrahalaya', 'Charles Correa', 'Ahmedabad, IN', '1963', 'Museum', 'Regionalism', ['Modular', 'Courtyard', 'Water'], 'A grid of tiled pavilions around a water court, open to the breeze and able to grow.'),
 ('CEPT University', 'B. V. Doshi', 'Ahmedabad, IN', '1966', 'Education', 'Regionalism', ['Brick', 'Exposed concrete', 'Climate response'], 'An architecture school of brick and concrete, open to the campus at every level.'),
 ('Sangath', 'B. V. Doshi', 'Ahmedabad, IN', '1981', 'Workplace', 'Regionalism', ['Vault', 'Climate response', 'Landscape'], 'Half-buried vaults clad in broken china, cooled by earth, water channels and steps.'),
 ('Aranya Low Cost Housing', 'B. V. Doshi', 'Indore, IN', '1989', 'Housing', 'Regionalism', ['Incremental', 'Low cost', 'Community'], 'Plots and a service core for 80,000 people, which families extend over time.'),
 ('Kanchanjunga Apartments', 'Charles Correa', 'Mumbai, IN', '1983', 'Housing', 'Regionalism', ['Section', 'Climate response', 'Double height'], 'Interlocking duplexes with two-storey garden verandas instead of balconies.'),
 ('Jawahar Kala Kendra', 'Charles Correa', 'Jaipur, IN', '1991', 'Culture & sport', 'Regionalism', ['Geometry', 'Courtyard', 'Colour'], 'A nine-square plan based on the navagraha mandala and the city plan of Jaipur.'),
 ('Centre for Development Studies', 'Laurie Baker', 'Thiruvananthapuram, IN', '1971', 'Education', 'Regionalism', ['Brick', 'Low cost', 'Climate response'], 'Rat-trap bond and perforated brick jalis: cheap, cool and built by local masons.'),
 ('Heritance Kandalama', 'Geoffrey Bawa', 'Dambulla, LK', '1994', 'Hospitality', 'Regionalism', ['Landscape', 'Planting', 'Climate response'], 'A hotel laid along a rock face, so overgrown it disappears into the jungle.'),
 ('New Gourna Village', 'Hassan Fathy', 'Luxor, EG', '1948', 'Housing', 'Regionalism', ['Earth & local material', 'Vault', 'Low cost'], 'Mud-brick vaults and domes revived to house villagers cheaply.'),
 ('Gando Primary School', 'Diébédo Francis Kéré', 'Gando, BF', '2001', 'Education', 'Regionalism', ['Earth & local material', 'Climate response', 'Community'], 'Compressed-earth walls under a raised tin roof, built by the village.'),
 ('Leça Swimming Pools', 'Álvaro Siza', 'Matosinhos, PT', '1966', 'Public space', 'Regionalism', ['Landscape', 'Exposed concrete', 'Water'], 'Concrete walls slipped between the rocks so the ocean pools seem natural.'),
 ('Can Lis', 'Jørn Utzon', 'Mallorca, ES', '1972', 'House', 'Regionalism', ['Stone', 'Landscape', 'Light & shadow'], 'Pavilions of local sandstone, with deep window frames that set the sea like pictures.'),
 ('Castelvecchio Museum', 'Carlo Scarpa', 'Verona, IT', '1975', 'Museum', 'Late modernism', ['Adaptive reuse', 'Detail', 'Promenade'], 'A medieval castle reworked with precise new joints, cuts and display stands.'),
 ('Brion Cemetery', 'Carlo Scarpa', "San Vito d'Altivole, IT", '1978', 'Religious', 'Late modernism', ['Detail', 'Water', 'Exposed concrete'], 'Concrete, water and interlocking circles: a lesson in detail and procession.'),
 ('Therme Vals', 'Peter Zumthor', 'Vals, CH', '1996', 'Hospitality', 'Contemporary', ['Stone', 'Water', 'Light from above'], 'Stacked layers of local quartzite, with slots of light between the roof slabs.'),
 ('Bruder Klaus Field Chapel', 'Peter Zumthor', 'Mechernich, DE', '2007', 'Religious', 'Contemporary', ['Exposed concrete', 'Light from above', 'Timber'], 'Concrete rammed around a tent of tree trunks, then burned out to leave a charred interior.'),
 ('Kolumba Museum', 'Peter Zumthor', 'Cologne, DE', '2007', 'Museum', 'Contemporary', ['Adaptive reuse', 'Brick', 'Light & shadow'], 'A perforated brick veil built over the ruins of a Gothic church.'),
 ('Ningbo History Museum', 'Wang Shu', 'Ningbo, CN', '2008', 'Museum', 'Contemporary', ['Reclaimed material', 'Brick', 'Sculptural form'], "Walls laid in 'wapan' from tiles and bricks salvaged from demolished villages."),
 ('Quinta Monroy', 'Alejandro Aravena, Elemental', 'Iquique, CL', '2004', 'Housing', 'Contemporary', ['Incremental', 'Low cost', 'Community'], "'Half a good house': the state builds half and families build the rest."),
 # Japan after Metabolism
 ('Row House in Sumiyoshi', 'Tadao Ando', 'Osaka, JP', '1976', 'House', 'Contemporary', ['Exposed concrete', 'Courtyard', 'Light from above'], 'A concrete box split by an open courtyard you cross to get to bed, even in the rain.'),
 ('Church of the Light', 'Tadao Ando', 'Ibaraki, JP', '1989', 'Religious', 'Contemporary', ['Exposed concrete', 'Light & shadow', 'Geometry'], 'A cross cut into a concrete wall: light as the only ornament.'),
 ('Sendai Mediatheque', 'Toyo Ito', 'Sendai, JP', '2001', 'Culture & sport', 'Contemporary', ['Structure as expression', 'Free plan', 'Steel & glass'], 'Thirteen lattice tubes carry thin floor plates, like seaweed in a tank.'),
 ('21st Century Museum of Contemporary Art, Kanazawa', 'SANAA', 'Kanazawa, JP', '2004', 'Museum', 'Contemporary', ['Free plan', 'Steel & glass', 'Public space'], 'A round glass perimeter with no front, holding the galleries as separate boxes.'),
 ('Moriyama House', 'Ryue Nishizawa', 'Tokyo, JP', '2005', 'House', 'Contemporary', ['Cluster', 'Courtyard', 'Landscape'], 'A house split into ten white boxes, with gardens and paths between the rooms.'),
 ('KAIT Workshop', 'Junya Ishigami', 'Atsugi, JP', '2008', 'Education', 'Contemporary', ['Free plan', 'Structure as expression', 'Steel & glass'], '305 thin steel columns of different sizes, scattered like a forest instead of a grid.'),
 ('Teshima Art Museum', 'Ryue Nishizawa, Rei Naito', 'Teshima, JP', '2010', 'Museum', 'Contemporary', ['Sculptural form', 'Light from above', 'Landscape'], 'One concrete shell with two openings, cast over a mound of earth.'),
 ('House NA', 'Sou Fujimoto', 'Tokyo, JP', '2011', 'House', 'Contemporary', ['Steel & glass', 'Section', 'Free plan'], 'A glass house of 21 floor plates at different heights, like living in a tree.'),
 # High-tech, deconstructivism, contemporary
 ('Centre Pompidou', 'Renzo Piano, Richard Rogers', 'Paris, FR', '1977', 'Culture & sport', 'High-tech', ['Structure as expression', 'Free plan', 'Public space'], 'Structure and services moved outside and colour-coded, leaving free floors and a public piazza.'),
 ("Lloyd's Building", 'Richard Rogers', 'London, UK', '1986', 'Office & tower', 'High-tech', ['Structure as expression', 'Light from above', 'Prefabrication'], 'Lifts, stairs and ducts as plug-in towers around a 60-metre atrium.'),
 ('HSBC Main Building', 'Norman Foster', 'Hong Kong', '1986', 'Office & tower', 'High-tech', ['Structure as expression', 'Prefabrication', 'Public space'], 'Floors hung from suspension trusses, freeing a public plaza beneath.'),
 ('Vitra Fire Station', 'Zaha Hadid', 'Weil am Rhein, DE', '1993', 'Workplace', 'Deconstructivism', ['Sculptural form', 'Exposed concrete', 'Cantilever'], "Zaha Hadid's first built work: sharp concrete planes caught in motion."),
 ('Guggenheim Bilbao', 'Frank Gehry', 'Bilbao, ES', '1997', 'Museum', 'Deconstructivism', ['Sculptural form', 'Facade as skin', 'Parametric'], 'Titanium curves designed with CATIA, software from the aerospace industry.'),
 ('Tate Modern', 'Herzog & de Meuron', 'London, UK', '2000', 'Museum', 'Contemporary', ['Adaptive reuse', 'Public space', 'Brick'], 'A power station turned museum; the Turbine Hall became an indoor street.'),
 ('Jewish Museum Berlin', 'Daniel Libeskind', 'Berlin, DE', '2001', 'Museum', 'Deconstructivism', ['Void', 'Sculptural form', 'Light & shadow'], "A zigzag plan cut through by empty 'voids' that visitors can see but not enter."),
 ('Seattle Central Library', 'OMA', 'Seattle, US', '2004', 'Culture & sport', 'Contemporary', ['Section', 'Steel & glass', 'Promenade'], 'Platforms stacked and shifted inside a diamond-mesh skin; the book spiral is one continuous ramp.'),
 ('Casa da Música', 'OMA', 'Porto, PT', '2005', 'Culture & sport', 'Contemporary', ['Sculptural form', 'Exposed concrete', 'Promenade'], 'A faceted concrete solid with the concert hall cut straight through it, glazed at both ends.'),
 ('Beijing National Stadium', 'Herzog & de Meuron', 'Beijing, CN', '2008', 'Culture & sport', 'Contemporary', ['Structure as expression', 'Facade as skin', 'Steel & glass'], "A 'bird's nest' of steel where structure, facade and roof are one tangle."),
 ('Oslo Opera House', 'Snøhetta', 'Oslo, NO', '2008', 'Culture & sport', 'Contemporary', ['Landscape', 'Public space', 'Stone'], 'A marble roof that slopes into the fjord, open for anyone to walk on.'),
 ('8 House', 'BIG', 'Copenhagen, DK', '2010', 'Housing', 'Contemporary', ['Promenade', 'Courtyard', 'Section'], 'A figure-eight block with a continuous path you can cycle to the top.'),
 ('CCTV Headquarters', 'OMA', 'Beijing, CN', '2012', 'Office & tower', 'Contemporary', ['Cantilever', 'Structure as expression', 'Megastructure'], 'A loop of two leaning towers joined by a 75-metre cantilever.'),
 ('Elbphilharmonie', 'Herzog & de Meuron', 'Hamburg, DE', '2017', 'Culture & sport', 'Contemporary', ['Adaptive reuse', 'Facade as skin', 'Public space'], 'A glass crown on a brick warehouse, with a public plaza between old and new.'),
 ('Louvre Abu Dhabi', 'Jean Nouvel', 'Abu Dhabi, AE', '2017', 'Museum', 'Contemporary', ['Light & shadow', 'Climate response', 'Water'], "A 180-metre dome of layered stars casts a 'rain of light' over a museum town."),
 # Parametric and computational
 ('MAXXI', 'Zaha Hadid', 'Rome, IT', '2010', 'Museum', 'Parametric', ['Promenade', 'Light from above', 'Sculptural form'], 'Braided concrete galleries and black stairs under a roof of light fins.'),
 ('Metropol Parasol', 'J. Mayer H.', 'Seville, ES', '2011', 'Public space', 'Parametric', ['Parametric', 'Timber', 'Public space'], 'Giant timber parasols over a market and Roman ruins, with a walkway on top.'),
 ('Heydar Aliyev Center', 'Zaha Hadid', 'Baku, AZ', '2012', 'Culture & sport', 'Parametric', ['Parametric', 'Sculptural form', 'Facade as skin'], 'One continuous surface folds from plaza to roof, with no line between wall and ground.'),
 ('ICD/ITKE Research Pavilion 2012', 'University of Stuttgart', 'Stuttgart, DE', '2012', 'Pavilion', 'Parametric', ['Digital fabrication', 'Parametric', 'Structure as expression'], "Robot-wound glass and carbon fibre, modelled on a lobster's shell."),
 # Reuse, landscape, ecology
 ('High Line', 'Diller Scofidio + Renfro, James Corner, Piet Oudolf', 'New York, US', '2009', 'Public space', 'Contemporary', ['Adaptive reuse', 'Landscape', 'Promenade'], 'An abandoned elevated railway turned into a park in the air.'),
 ('Stacking Green', 'Vo Trong Nghia', 'Ho Chi Minh City, VN', '2011', 'House', 'Contemporary', ['Planting', 'Climate response', 'Facade as skin'], 'A narrow tube house fronted by stacked planters that shade and cool it.'),
 ('Superkilen', 'BIG, Topotek 1, Superflex', 'Copenhagen, DK', '2012', 'Public space', 'Contemporary', ['Public space', 'Colour', 'Community'], 'A park furnished with objects chosen by neighbours from some 60 countries.'),
 ('Sancaklar Mosque', 'Emre Arolat', 'Istanbul, TR', '2012', 'Religious', 'Contemporary', ['Landscape', 'Light & shadow', 'Stone'], 'A mosque dug into a hillside, its prayer hall lit by slits in the stepped roof.'),
 ('Bosco Verticale', 'Stefano Boeri', 'Milan, IT', '2014', 'Housing', 'Contemporary', ['Planting', 'Climate response', 'Cantilever'], 'Two towers carrying about 900 trees on staggered balconies.'),
 ('Zeitz MOCAA', 'Heatherwick Studio', 'Cape Town, ZA', '2017', 'Museum', 'Contemporary', ['Adaptive reuse', 'Light from above', 'Sculptural form'], 'A grain silo carved into an atrium shaped like a single grain of corn.'),
 # Historic precedents the modernists studied
 ('Pantheon', 'Hadrian (attrib.)', 'Rome, IT', '125', 'Religious', 'Historic precedent', ['Light from above', 'Geometry', 'Vault'], 'A concrete dome as wide as it is high, lit only by the oculus.'),
 ('Katsura Imperial Villa', 'Prince Toshihito and Toshitada', 'Kyoto, JP', '17th c.', 'House', 'Historic precedent', ['Modular', 'Timber', 'Landscape'], 'Tatami-module rooms and sliding screens that inspired Taut, Gropius and Tange.'),
 ('Alhambra', 'Nasrid builders', 'Granada, ES', '14th c.', 'Palace', 'Historic precedent', ['Courtyard', 'Water', 'Detail'], 'A sequence of courtyards, water and pattern, each room opening to the sky.'),
 ('Chand Baori', 'Unknown builders', 'Abhaneri, IN', 'c. 800', 'Infrastructure', 'Historic precedent', ['Geometry', 'Water', 'Climate response'], 'A stepwell thirteen storeys deep: architecture as a climate machine.'),
 ('Villa La Rotonda', 'Andrea Palladio', 'Vicenza, IT', '1592', 'House', 'Historic precedent', ['Geometry', 'Axis', 'Landscape'], 'A square plan with four porticoes: the villa that later classical houses copied.'),
]

REGION = {
    'FR': 'Europe', 'ES': 'Europe', 'CZ': 'Europe', 'DE': 'Europe', 'NL': 'Europe', 'FI': 'Europe', 'UK': 'Europe',
    'DK': 'Europe', 'PT': 'Europe', 'IT': 'Europe', 'CH': 'Europe', 'NO': 'Europe', 'TR': 'Middle East',
    'US': 'Americas', 'MX': 'Americas', 'BR': 'Americas', 'CA': 'Americas', 'CL': 'Americas',
    'IN': 'South Asia', 'BD': 'South Asia', 'LK': 'South Asia',
    'JP': 'East Asia', 'CN': 'East Asia', 'VN': 'East Asia', 'Hong Kong': 'East Asia',
    'EG': 'Africa', 'BF': 'Africa', 'ZA': 'Africa', 'AE': 'Middle East', 'AZ': 'Middle East', 'AU': 'Oceania',
}


def year_num(y):
    n = int(re.search(r'\d+', y).group())
    return (n - 1) * 100 + 50 if 'th c' in y else n  # '17th c.' -> 1650


def era(y):
    if y < 1900: return 'Before 1900'
    if y < 1945: return '1900–1945'
    if y < 1970: return '1945–1970'
    if y < 1990: return '1970–1990'
    if y < 2005: return '1990–2005'
    return '2005–today'


def slug(s):
    s = s.lower()
    for a, b in (('é', 'e'), ('è', 'e'), ('ä', 'a'), ('ö', 'o'), ('ø', 'o'), ('æ', 'ae'), ('ü', 'u'), ('ő', 'o'), ('á', 'a'), ('í', 'i'), ('ó', 'o'), ('ç', 'c'), ('ã', 'a'), ("'", ''), ('’', '')):
        s = s.replace(a, b)
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')


def main():
    old = {}
    if OUT.exists():
        text = OUT.read_text()
        for b in json.loads(text.split('window.BUILDINGS = ', 1)[1].rstrip().rstrip(';')):
            if b.get('images'):
                old[b['id']] = b['images']
    items = []
    for i, (name, by, place, year, typ, movement, concepts, study) in enumerate(ROWS):
        bad = [c for c in concepts if c not in CONCEPTS]
        assert not bad, (name, bad)
        country = place.split(',')[-1].strip()
        y = year_num(year)
        bid = slug(name)
        items.append({
            'id': bid, 'n': i + 1, 'name': name, 'by': by, 'place': place, 'year': year, 'y': y,
            'type': typ, 'movement': movement, 'region': REGION[country], 'era': era(y),
            'concepts': concepts, 'study': study, 'images': old.get(bid, []),
        })
    assert len(items) == 100, len(items)
    assert len({b['id'] for b in items}) == 100
    OUT.write_text('// The first 100, chosen for architecture students. Generated by tools/students_list.py;\n'
                   '// images are filled in by tools/fetch_images.py.\nwindow.BUILDINGS = '
                   + json.dumps(items, ensure_ascii=False, indent=1) + ';\n')
    print(f'Wrote {len(items)} buildings to {OUT.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
