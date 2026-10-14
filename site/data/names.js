/* Find Great Architecture: one name per architect.
   A building keeps its credit exactly as its source gives it (b.by, shown on the building). These rules only decide
   which credits are the same architect, for the Architect filter, "See all", "More by", the Pritzker medal and the game:
   - a practice named after one person goes under that person (Zaha Hadid Architects → Zaha Hadid);
   - a firm of several partners keeps the firm's name (SANAA, OMA, SOM, BIG, gmp);
   - notes in brackets are dropped (Arata Isozaki (entrance) → Arata Isozaki);
   - spellings with and without accents are one name, the accented one (Antoni Gaudi → Antoni Gaudí);
   - "A and B" counts for both when each is on the wall under their own name.
   Load after data/buildings.js. Add a line to SAME when a new duplicate turns up. */
window.NAMES = (() => {
  'use strict';
  // Credits that contain a comma but are one firm.
  const WHOLE = ['Skidmore, Owings & Merrill', 'Skidmore, Owings and Merrill', 'Chamberlin, Powell and Bon',
    'von Gerkan, Marg und Partner', 'von Gerkan, Marg and Partners'];
  // Another name for the same architect → the name used on the wall.
  const SAME = {
    'Zaha Hadid Architects': 'Zaha Hadid',
    'Foster + Partners': 'Norman Foster', 'Foster and Partners': 'Norman Foster',
    'Renzo Piano Building Workshop': 'Renzo Piano',
    'Ateliers Jean Nouvel': 'Jean Nouvel',
    'Studio Daniel Libeskind': 'Daniel Libeskind', 'Studio Libeskind': 'Daniel Libeskind',
    'David Chipperfield Architects': 'David Chipperfield',
    'Richard Rogers Partnership': 'Richard Rogers', 'Rogers Stirk Harbour + Partners': 'Richard Rogers',
    'Steven Holl Architects': 'Steven Holl',
    'Shigeru Ban Architects': 'Shigeru Ban',
    'Kengo Kuma and Associates': 'Kengo Kuma',
    'Adjaye Associates': 'David Adjaye',
    'Harry Seidler & Associates': 'Harry Seidler',
    'Henning Larsen Architects': 'Henning Larsen',
    'Nicholas Grimshaw & Partners': 'Nicholas Grimshaw', 'Grimshaw': 'Nicholas Grimshaw', 'Grimshaw Architects': 'Nicholas Grimshaw',
    'Michael Wilford and Partners': 'Michael Wilford', 'Michael Wilford and Associates': 'Michael Wilford',
    'Emre Arolat Architecture': 'Emre Arolat',
    'Sean Godsell Architects': 'Sean Godsell',
    'Ove Arup & Partners': 'Ove Arup',
    'Elemental': 'Alejandro Aravena', 'Alejandro Aravena (Elemental)': 'Alejandro Aravena',
    'I. M. Pei & Partners': 'I. M. Pei',
    'Welton Becket & Associates': 'Welton Becket',
    'Robert G. Boughey & Associates': 'Robert Boughey',
    'B. V. Doshi': 'Balkrishna Doshi',
    'Ludwig Mies van der Rohe': 'Mies van der Rohe',
    'Charles-Édouard Jeanneret (Le Corbusier)': 'Le Corbusier',
    'SOM (Gordon Bunshaft)': 'Gordon Bunshaft',
    'Skidmore, Owings & Merrill': 'SOM', 'Skidmore, Owings and Merrill': 'SOM',
    'OMA / Rem Koolhaas': 'OMA', 'Rem Koolhaas': 'OMA',
    'gmp (von Gerkan, Marg and Partners)': 'gmp Architekten', 'gmp Architects': 'gmp Architekten',
    'von Gerkan, Marg und Partner': 'gmp Architekten', 'von Gerkan, Marg and Partners': 'gmp Architekten',
    'Ingenhoven Architects': 'Christoph Ingenhoven', 'ingenhoven associates': 'Christoph Ingenhoven',
    'Adrian Smith + Gordon Gill Architecture': 'Adrian Smith + Gordon Gill',
    'J. Mayer H. Architects': 'J. Mayer H.',
    'Marks Barfield Architects': 'Marks Barfield',
    'Schmidt Hammer Lassen Architects': 'Schmidt Hammer Lassen',
    'JDS Architects': 'JDS',
    'Landprocess': 'LANDPROCESS',
    'Kashef Chowdhury': 'Kashef Mahboob Chowdhury',
    'Fazlur Khan': 'Fazlur Rahman Khan',
    'Willem Marinus Dudok': 'Willem Dudok',
    'Josep Antoni Coderch': 'José Antonio Coderch',
    'Arthur Tarkhanyan': 'Artur Tarkhanyan',
    'Frederich Silaban': 'Friedrich Silaban',
    'Mohamed Makiya': 'Mohammed Saleh Makiya'
  };
  const fold = s => String(s).toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '');

  // "A, B; roof by C with D" → [A, B, C, D]. Commas inside brackets and inside the firms above don't split.
  function parts(by) {
    let s = String(by || '');
    WHOLE.forEach((w, i) => { s = s.split(w).join(`\u0001${i}\u0001`); });
    const out = [];
    let depth = 0, cur = '';
    for (const ch of s) {
      if (ch === '(') depth++;
      if (ch === ')') depth = Math.max(0, depth - 1);
      if (!depth && (ch === ',' || ch === ';')) { out.push(cur); cur = ''; } else cur += ch;
    }
    out.push(cur);
    return out.flatMap(p => p.split(/\s+with\s+/i))
      .map(p => p.replace(/\u0001(\d+)\u0001/g, (m, i) => WHOLE[i]).replace(/^[a-z][^A-Z]*?\bby\s+/, '').trim())
      .filter(Boolean);
  }
  function tidy(name) {
    if (SAME[name]) return SAME[name];
    const bare = name.replace(/\s*\(.*?\)\s*/g, ' ').replace(/\s*\(.*$/, '').trim() || name;
    return SAME[bare] || bare;
  }
  // How many buildings each tidied name has, before the two steps below.
  const count = new Map();
  (window.BUILDINGS || []).forEach(b => parts(b.by).forEach(p => { const t = tidy(p); count.set(t, (count.get(t) || 0) + 1); }));
  // "Le Corbusier and Pierre Jeanneret" counts for both, but only when each half is on the wall under its own name
  // ("Venturi and Rauch" and "Chamberlin, Powell and Bon" stay whole).
  const pair = t => { const bits = t.split(/\s+and\s+/).map(tidy); return bits.length > 1 && bits.every(x => count.has(x)) ? bits : [t]; };
  // Accented and plain spellings: the one with more accents wins, then the one with more buildings.
  const spelling = new Map();
  const marks = s => (s.normalize('NFD').match(/[\u0300-\u036f]/g) || []).length;
  for (const [name, k] of count) {
    const key = fold(name), best = spelling.get(key);
    if (!best || marks(name) > marks(best) || (marks(name) === marks(best) && k > count.get(best))) spelling.set(key, name);
  }
  const spell = t => spelling.get(fold(t)) || t;
  const canon = name => spell(tidy(String(name).trim()));
  const list = by => [...new Set(parts(by).flatMap(p => pair(tidy(p))).map(spell))];
  return { list, first: by => list(by)[0] || String(by || '').trim(), canon };
})();
