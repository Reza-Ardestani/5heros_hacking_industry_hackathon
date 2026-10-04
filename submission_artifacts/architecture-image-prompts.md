# Architecture image generation

Generated with the built-in image generation tool. Both PNGs visually checked for labels, hierarchy, and flow. Diagrams abstract the shared storage layer; SQLite commits precede ordered TimescaleDB replication. TimescaleDB remains configurable.

## 06-architecture.png

Use case: infographic-diagram.
Create a polished colorful architecture diagram image for the Bottleneck Busters hackathon submission. Landscape 16:9 slide composition, high resolution, crisp flat vector-like infographic, off-white background, navy typography, restrained soft shadows, generous whitespace, large legible exact labels. Colorful but professional: teal data/ingestion, blue database, violet backend, coral frontend. No photo, watermark, mock UI, invented claims, extra components or logo text.
Title exactly "Bottleneck Busters" and subtitle exactly "System Architecture".
Make this simplified yet useful: ONLY five major blocks. External source at far left labeled "Calgary Open Data", tiny supporting line "Incidents · closures · travel times". A large thin rounded boundary enclosing the other FOUR blocks labeled "GitHub Codespaces" with small descriptor "Demo environment".
Inside that boundary, left-to-right data flow: a teal "Data Ingestion" block, a blue database-cylinder block "TimescaleDB" with small subline "PostgreSQL", a broad violet "Backend" container with subtitle "Python / FastAPI", then coral "React Frontend" block with subline "Maps · studies · chat".
Inside Backend show exactly THREE large, clearly spaced tiles: "MCP Server", "Agent Loop", "SUMO Simulation". MCP Server subline "Tools"; Agent Loop subline "Propose · evaluate · revise"; SUMO Simulation subline "Baseline + trials". A small clearly readable two-way arrow only between Agent Loop and SUMO Simulation, representing candidate trials and results. Do not imply an LLM is required.
Connect Calgary Open Data to Data Ingestion with a simple arrow. Data Ingestion to TimescaleDB with a simple arrow. TimescaleDB and Backend with one two-way arrow. Backend and React Frontend with one two-way arrow. Never route connectors through labels or panels. All components large, alignment tidy. Only simple pictograms: data documents, funnel, database, tools, cycle, traffic intersection, browser.
At bottom inside boundary place a single unobtrusive readable note exactly "Storage: SQLite durable journal & fallback · TimescaleDB configurable". This describes real storage architecture without claiming TimescaleDB is the default. No ports, authentication details, database replication boxes, HTTPS labels, planner person, API card, external cloud hosts or microscopic paragraphs. This is the moderately simplified architecture image, not a dense engineering chart.

## 07-architecture-overview.png

Use case: infographic-diagram.
Create a polished colorful high-level architecture image for the Bottleneck Busters hackathon submission, substantially zoomed out and simpler than an engineering diagram. Landscape 16:9 slide composition, high resolution, crisp flat vector-like infographic, off-white background, navy typography, gentle shadows, generous whitespace, very large legible exact labels. Use teal for data/ingestion, blue for database, violet for backend, coral for React. No photo, watermark, invented claims, extra nodes or logo text.
Title exactly "Bottleneck Busters" and subtitle exactly "Architecture at a Glance".
ONLY FIVE major blocks total in a clean horizontal composition. Far left outside a subtle hosting boundary is "Calgary Open Data" with a simple documents icon. Other four blocks enclosed by one large thin rounded hosting boundary labeled prominently "GitHub Codespaces" and smaller text "Demo environment".
The four hosted blocks from left to right:
1. "Ingestion", small supporting line "Collect & prepare data", simple funnel icon.
2. "TimescaleDB", small supporting line "Traffic data & evidence", simple database cylinder icon.
3. "Backend", small supporting lines "MCP Server · Agent Loop" and "SUMO Simulation", simple processing icon. Do NOT draw inner tiles, internal arrows, inner API card or extra backend boxes.
4. "React Frontend", small supporting line "Explore · simulate · compare", simple browser icon.
Connect Calgary Open Data to Ingestion with one clear arrow, Ingestion to TimescaleDB with one clear arrow, TimescaleDB to Backend with one clear bidirectional arrow, Backend to React Frontend with one clear bidirectional arrow. Connectors never cross text or components. Blocks balanced with big readable typography. This is an executive overview, not a detailed component diagram.
At bottom inside hosting boundary add ONE subtle but readable note exactly "SQLite journal & fallback · TimescaleDB configurable". No other notes, no ports, no protocol labels, no autonomous AI claims, no deployment-status stamp. Keep all requested components visible but group backend internals as text only.
