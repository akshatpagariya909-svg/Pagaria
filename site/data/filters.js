// Line drawings and groups for the filter panel (site/filter.js).
// Each idea and building type has a small drawing on a 24 x 24 grid. A new idea or type in the data
// still works without one: it goes into an "Other" group with a plain dot until a drawing is added here.
window.FILTER_ART = {
 "ideaGroups": [
  [
   "Light",
   "How daylight is let in, filtered and coloured.",
   [
    "Light from above",
    "Light & shadow",
    "Brise-soleil",
    "Colour"
   ]
  ],
  [
   "Structure",
   "How it stands up, and how that is shown.",
   [
    "Structure as expression",
    "Cantilever",
    "Vault",
    "Pilotis",
    "Tensile structure",
    "Megastructure",
    "Prefabrication",
    "Modular",
    "Parametric",
    "Digital fabrication"
   ]
  ],
  [
   "Material",
   "What it is made of and how it is finished.",
   [
    "Exposed concrete",
    "Brick",
    "Stone",
    "Timber",
    "Steel & glass",
    "Earth & local material",
    "Reclaimed material",
    "Facade as skin",
    "Detail"
   ]
  ],
  [
   "Space",
   "How rooms, levels and routes are arranged.",
   [
    "Courtyard",
    "Double height",
    "Section",
    "Promenade",
    "Circulation",
    "Void",
    "Free plan",
    "Cluster",
    "Axis",
    "Geometry",
    "Sculptural form"
   ]
  ],
  [
   "Place",
   "How it meets its site, climate and people.",
   [
    "Landscape",
    "Water",
    "Planting",
    "Climate response",
    "Public space",
    "Community",
    "Monumentality",
    "Adaptive reuse",
    "Low cost",
    "Incremental",
    "Human comfort"
   ]
  ]
 ],
 "typeGroups": [
  [
   "Culture",
   "Places to see, read and gather.",
   [
    "Museum",
    "Library",
    "Culture & sport",
    "Pavilion"
   ]
  ],
  [
   "Living",
   "Places to live and stay.",
   [
    "House",
    "Housing",
    "Hospitality"
   ]
  ],
  [
   "Work and learning",
   "Places to work, study and heal.",
   [
    "Office & tower",
    "Workplace",
    "Education",
    "Health"
   ]
  ],
  [
   "Civic and sacred",
   "Government, worship and memory.",
   [
    "Civic",
    "Palace",
    "Religious",
    "Memorial"
   ]
  ],
  [
   "The city",
   "Spaces and structures everyone shares.",
   [
    "Public space",
    "Infrastructure"
   ]
  ]
 ],
 "ideaIcons": {
  "Light from above": "M3 10h7M14 10h7M3 10v11M21 10v11M12 2v5M8 3l2 4M16 3l-2 4M3 21h18",
  "Light & shadow": "M12 3a9 9 0 1 0 0 18zM3 21h18",
  "Brise-soleil": "M4 3v18M20 3v18M4 6l16 2M4 10l16 2M4 14l16 2M4 18l16 2",
  "Colour": "M14 9a5 5 0 1 1-10 0a5 5 0 1 1 10 0M20 9a5 5 0 1 1-10 0a5 5 0 1 1 10 0M17 15a5 5 0 1 1-10 0a5 5 0 1 1 10 0",
  "Structure as expression": "M2 18h20M2 18L7 8l5 10 5-10 5 10M7 8h10",
  "Cantilever": "M2 21h20M5 21V9h17v4H10v8",
  "Vault": "M3 21v-8a9 9 0 0 1 18 0v8M3 21h18M8 21v-7a4 4 0 0 1 8 0v7",
  "Pilotis": "M3 4h18v8H3zM6 12v9M12 12v9M18 12v9M2 21h20",
  "Tensile structure": "M4 21V4M20 21V4M4 6c4 9 12 9 16 0M2 21h20",
  "Megastructure": "M3 21V3h18v18M3 9h18M9 3v18M12 13h3v3h-3zM5 13h2v4H5z",
  "Prefabrication": "M4 21h16M5 21v-5h6v5M13 21v-5h6v5M8 16v-5h8v5M12 2v6M10 8h4",
  "Modular": "M3 21v-6h6v6zM9 21v-6h6v6zM15 21v-6h6v6zM6 15V9h6v6zM12 9V3h6v6z",
  "Parametric": "M3 20c3-8 6-8 9 0s6 8 9 0M3 13c3-7 6-7 9 0s6 7 9 0M3 6c3-4 6-4 9 0s6 4 9 0",
  "Digital fabrication": "M4 21h16M6 21V11M18 21V11M6 11c2-7 10-7 12 0M9 15h.01M12 13h.01M15 15h.01",
  "Exposed concrete": "M3 4h18v16H3zM3 12h18M12 4v16M7.5 8h.01M16.5 8h.01M7.5 16h.01M16.5 16h.01",
  "Brick": "M3 5h18v16H3zM3 9h18M3 13h18M3 17h18M9 5v4M15 5v4M6 9v4M12 9v4M18 9v4M9 13v4M15 13v4M6 17v4M12 17v4M18 17v4",
  "Stone": "M3 21h18M3 21v-6l4-1 3 1v6M10 21v-5l5-1 3 2v4M5 14l1-5 5 1v5M11 15l1-6 6 1-1 5",
  "Timber": "M3 6h18v12H3zM3 10c6-2 12 2 18 0M3 14c6-2 12 2 18 0",
  "Steel & glass": "M5 2h14v20H5zM5 7h14M5 12h14M5 17h14M12 2v20",
  "Earth & local material": "M3 6h18v15H3zM3 10c4 1 8-1 12 0s4 0 6 0M3 14c4 1 8-1 12 0s4 0 6 0M3 18c4 1 8-1 12 0s4 0 6 0",
  "Reclaimed material": "M20 12a8 8 0 0 1-14 5M4 12a8 8 0 0 1 14-5M18 3v4h-4M6 21v-4h4",
  "Facade as skin": "M7 3v18M17 3v18M7 3h10M7 21h10M3 4c2 4 2 12 0 16M21 4c-2 4-2 12 0 16",
  "Detail": "M16 10a6 6 0 1 1-12 0a6 6 0 1 1 12 0M14.5 14.5L21 21M7 10h6M10 7v6",
  "Courtyard": "M3 3h18v18H3zM8 8h8v8H8z",
  "Double height": "M3 3h18v18H3zM3 12h8M11 12v9",
  "Section": "M3 21V8l9-5 9 5v13M3 21h18M3 14h18M7 21v-3h4v-4",
  "Promenade": "M3 21h6l5-5h7M3 13h6l5-5h7",
  "Circulation": "M3 21h4v-4h4v-4h4V9h4V5h2",
  "Void": "M3 3h18v18H3zM15 12a3 3 0 1 1-6 0a3 3 0 1 1 6 0",
  "Free plan": "M5 5h.01M12 5h.01M19 5h.01M5 12h.01M12 12h.01M19 12h.01M5 19h.01M12 19h.01M19 19h.01M7 17c3-2 2-8 8-10",
  "Cluster": "M2 21h20M3 21v-5l3-3 3 3v5M10 21v-7l3-3 3 3v7M17 21v-5l2-2 2 2v5",
  "Axis": "M12 2v20M6 7h12v10H6z",
  "Geometry": "M4 4h16v16H4zM20 12a8 8 0 1 1-16 0a8 8 0 1 1 16 0M4 20L20 4",
  "Sculptural form": "M3 21c1-8 4-14 9-17 1 6 4 12 9 17M7 21c1-5 3-9 5-11M3 21h18",
  "Landscape": "M2 20c4-7 8-9 12-5s6 3 8 0M2 20h20",
  "Water": "M2 10c3-3 5 3 8 0s5 3 8 0 3-1 4 0M2 16c3-3 5 3 8 0s5 3 8 0 3-1 4 0",
  "Planting": "M12 21v-7M12 14c-4 0-6-3-6-6 3 0 6 2 6 6 0-4 3-6 6-6 0 3-2 6-6 6M4 21h16",
  "Climate response": "M2 11h15l4 3M5 11v10M14 11v10M2 21h20M20 5a2 2 0 1 1-4 0a2 2 0 1 1 4 0",
  "Public space": "M3 21h18M7.5 12a1.5 1.5 0 1 1-3 0a1.5 1.5 0 1 1 3 0M6 14v5M13.5 10a1.5 1.5 0 1 1-3 0a1.5 1.5 0 1 1 3 0M12 12v7M19.5 12a1.5 1.5 0 1 1-3 0a1.5 1.5 0 1 1 3 0M18 14v5",
  "Community": "M14 12a2 2 0 1 1-4 0a2 2 0 1 1 4 0M12 3v5M12 16v5M3 12h5M16 12h5M6 6l3 3M18 6l-3 3M6 18l3-3M18 18l-3-3",
  "Monumentality": "M2 21h20M4 21v-2h16v2M6 19v-2h12v2M8 17V4h8v13",
  "Adaptive reuse": "M3 21V9l9-6 9 6v12M3 21h18M8 21v-7h8v7",
  "Low cost": "M3 21V11l9-7 9 7v10M3 21h18M10 21v-6h4v6",
  "Incremental": "M2 21h20M3 21v-9l5-4 5 4v9M13 15h4v6M17 13h4v8",
  "Human comfort": "M6 12V4M6 12h10l2 9M6 12l-2 9M16 12V9"
 },
 "typeIcons": {
  "Civic": "M3 21h18M5 21V11h14v10M4 11h16M8 11V8a4 4 0 0 1 8 0v3M9 21v-5M15 21v-5",
  "Culture & sport": "M2 10c0 3 4.5 5 10 5s10-2 10-5M2 10c0-3 4.5-5 10-5s10 2 10 5M2 10v6c0 3 4.5 5 10 5s10-2 10-5v-6",
  "Education": "M3 5c3-1 6 0 9 2 3-2 6-3 9-2v14c-3-1-6 0-9 2-3-2-6-3-9-2zM12 7v14",
  "Health": "M4 21V6h16v15M2 21h20M12 9v6M9 12h6",
  "Hospitality": "M3 19V8M3 15h18v4M21 15v-1a3 3 0 0 0-3-3h-7v4M5 12h3",
  "House": "M3 21V10l9-7 9 7v11M3 21h18M9 21v-6h6v6",
  "Housing": "M5 21V3h14v18M3 21h18M8 6h2M14 6h2M8 10h2M14 10h2M8 14h2M14 14h2M10 21v-3h4v3",
  "Infrastructure": "M2 16h20M2 10c5 0 7 6 10 6s5-6 10-6M6 16v5M18 16v5M12 16v5",
  "Library": "M4 21V4h3v17M8 21V6h3v15M12 21V4h3v17M16 21l2-15 3 .5-2 15M3 21h18",
  "Memorial": "M12 2l2 4v13h-4V6zM7 21h10M10 19h4",
  "Museum": "M3 9l9-6 9 6M4 9h16M5 21V9M9 21V9M15 21V9M19 21V9M3 21h18",
  "Office & tower": "M8 21V3h8v18M5 21h14M10 6h4M10 10h4M10 14h4",
  "Palace": "M3 21V8h3v3h3V8h6v3h3V8h3v13M3 21h18M10 21v-5h4v5",
  "Pavilion": "M2 8l10-4 10 4M4 8v13M20 8v13M2 21h20",
  "Public space": "M3 21h18M5 17h14M12 17V10M9 12c0-3 1.5-5 3-5s3 2 3 5",
  "Religious": "M12 2v4M10 4h4M7 21V11l5-5 5 5v10M3 21h18M10 21v-4a2 2 0 0 1 4 0v4",
  "Workplace": "M3 21h18M5 21V9h14v12M9 9V5h6v4M8 13h3M13 13h3M8 17h3M13 17h3"
 }
};
