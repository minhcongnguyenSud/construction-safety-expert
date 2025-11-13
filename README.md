# Ontario Construction Safety Expert 🛡️

A RAG-based safety assistant providing comprehensive guidance on Ontario construction safety regulations.

## Features

- **Specialized Safety Skills**: Expert knowledge for all major construction hazards
  - 🪜 Falls Safety, ⚡ Electrical Safety, 🚧 Struck-By Hazards
  - ⛏️ Excavation Safety, 🚪 Confined Spaces, 🏗️ Cranes & Hoisting
  - 🧪 Health Hazards, 🦺 Workplace Safety
- **Comprehensive Knowledge Base**: 97+ entries covering Ontario Regulation 213/91
- **Interactive Web Interface**: Streamlit-based chat interface for safety questions

## Quick Start

1. Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Run the Streamlit app:

```bash
streamlit run streamlit_app.py --server.port 8501
```

3. Open http://localhost:8501 in your browser

## Project Structure

- `streamlit_app.py` - Web interface
- `orchestrator/` - Core processing and LLM integration
- `knowledge_base/` - JSON knowledge bases with safety regulations
- `.claude/skills/` - Specialized safety skills
- **Ontario-Specific**: Focused on O. Reg 213/91, O. Reg 632/05, O. Reg 490/09, and IHSA guidelines
- **Claude Code Native**: Uses Claude Code's built-in skill system for seamless integration

## Knowledge Base Coverage

The system includes **97+ comprehensive entries** across 8 specialized skills:

### 🪜 Falls Safety (22 entries)
- O. Reg 213/91 Section 26 fall protection requirements
- Working at Heights (WAH) training mandates
- Fall protection hierarchy (guardrails > travel restraint > fall arrest)
- Scaffold design requirements (Sections 126-136)
- MEWP operation and safety
- Ladder safety standards
- Guardrail specifications (1070mm ±30mm)

### ⚡ Electrical Safety (12 entries)
- O. Reg 213/91 Sections 181-183 electrical safety
- Lock Out Tag Out (LOTO) 7-step procedure
- Overhead power line clearances by voltage (3m, 5m, 8m+)
- Temporary power and GFCI protection requirements
- Arc flash hazards and prevention
- Underground utility location (Ontario One Call)

### 🚧 Struck-By Hazards (6 entries)
- Struck-by incident statistics (359 injuries, 38 fatalities 2018-2022)
- Mobile equipment and vehicle safety
- Traffic control requirements (Sections 67-69)
- Crane load exclusion zones
- Falling objects and material storage
- Backing vehicle safety and spotter requirements

### ⛏️ Excavation Safety (6 entries)
- Excavation requirements (Sections 222-242)
- Soil classification by type (Type 1, 2, 3, 4)
- Trench cave-in prevention and protection systems
- Access and egress requirements (7.5m lateral travel)
- Atmospheric hazards in excavations
- Ontario One Call utilities location (mandatory 5 days notice)

### 🚪 Confined Spaces (6 entries)
- O. Reg 632/05 confined spaces regulation
- Entry permit requirements (Section 10)
- Atmospheric testing requirements (Section 18: O₂ 19.5-23%)
- Confined space hazards and controls
- Rescue planning and emergency procedures
- Attendant and entry supervisor duties

### 🏗️ Cranes & Hoisting (7 entries)
- 2024 updates to crane regulations
- Crane operations and applicable O. Reg 213/91 sections
- Lift planning and risk management for critical lifts
- Hand signals and communication protocols
- Exclusion zones and load control
- Rigging hardware and daily inspection requirements
- Weather limits (typically 32-40 km/h wind)

### 🧪 Health Hazards (13 entries)
- Designated Substances Regulation (O. Reg 490/09)
- Asbestos identification and controls (pre-1990 buildings)
- Crystalline silica dust exposure and controls
- Lead exposure requirements (Section 30 OHSA)
- Noise exposure and hearing conservation (>85 dBA)
- Hand-arm and whole-body vibration hazards
- Chemical handling and WHMIS 2015
- Heat stress prevention and acclimatization
- Cold stress and winter hazards
- Musculoskeletal disorders (MSDs) prevention
- Manual material handling limits (23 kg)
- Ergonomic controls and task rotation
- Respiratory protection and fit testing

### 🦺 Workplace Safety (25 entries)
- Personal Protective Equipment (PPE) requirements
- Fire safety requirements (Sections 52-58)
- Welding and cutting/hot work permits (Sections 122-124)
- Demolition requirements and engineered procedures (Sections 212-221)
- Hard hat selection, use, and maintenance
- Respiratory protection and fit testing requirements
- Housekeeping and slips/trips/falls prevention
- Emergency action plans and response procedures
- Incident reporting to Ministry (critical injuries, fatalities)
- Ontario legal duties: employer, supervisor, worker (OHSA)
- Hazard communication and right to know
- Machine guarding requirements
- Fire extinguisher types and selection
- Structural alteration procedures

## Project Structure

```
rag_langchain_claude/
├── .claude/
│   ├── skills/                      # 8 Claude Code expert skills
│   │   ├── electrical-safety/       # Electrical hazards expert (12 entries)
│   │   ├── falls-safety/            # Falls prevention expert (22 entries)
│   │   ├── struck-by-hazards/       # Struck-by hazards expert (6 entries)
│   │   ├── excavation-safety/       # Excavation & trenching expert (6 entries)
│   │   ├── confined-spaces/         # Confined space entry expert (6 entries)
│   │   ├── cranes-hoisting/         # Crane operations expert (7 entries)
│   │   ├── health-hazards/          # Occupational health expert (13 entries)
│   │   └── workplace-safety/        # General workplace safety expert (25 entries)
│   └── settings.local.json          # Claude Code settings
├── knowledge_base/
│   ├── electrical_base.json         # 12 electrical safety entries
│   ├── fall_base.json               # 22 falls prevention entries
│   ├── struckby_base.json           # 6 struck-by hazard entries
│   ├── general_base.json            # 63 entries (excavation, confined spaces, cranes, health, workplace)
│   └── README.md                    # Knowledge base documentation
├── legacy/                          # Legacy Python scripts and tests (archived)
│   ├── streamlit_app.py             # Old web interface
│   ├── test scripts                 # Test files for legacy system
│   └── README.md                    # Legacy documentation
├── orchestrator/                    # Legacy Python implementation (deprecated)
├── SKILLS_MATRIX.md                 # Detailed skills and knowledge base mapping
├── CHANGELOG.md                     # Project evolution history
└── README.md                        # This file
```

**See [SKILLS_MATRIX.md](SKILLS_MATRIX.md) for detailed mapping of skills to knowledge base entries.**

## Adding New Knowledge

To add new safety information to the knowledge base:

1. **Identify the appropriate JSON file:**
   - `electrical_base.json` - Electrical hazards and LOTO
   - `fall_base.json` - Falls from heights and fall protection
   - `struckby_base.json` - Struck-by hazards
   - `general_base.json` - Excavation, confined spaces, cranes, health hazards, workplace safety

2. **Add entry following the JSON structure:**

```json
{
  "title": "Topic Title",
  "content": "Detailed safety information with specific requirements...",
  "category": "category_name",
  "source": "O. Reg 213/91 Section X",
  "keywords": ["keyword1", "keyword2", "keyword3"]
}
```

3. **The relevant skill will automatically access the updated knowledge.**

See [SKILLS_MATRIX.md](SKILLS_MATRIX.md) for details on which entries each skill uses.

## Safety Notice

⚠️ **Important**: This system provides safety guidance based on Ontario Regulation 213/91 and related construction safety regulations. It should not replace:

- Professional safety training and certification
- Site-specific safety protocols and procedures
- Qualified safety personnel and supervisors
- Official OHSA regulations and Ministry of Labour guidance
- Employer-specific policies and procedures

Always consult with qualified safety professionals and follow your organization's specific safety procedures. In case of emergency, contact appropriate emergency services immediately.

## License

MIT License - See LICENSE file for details

## Contributing

Contributions are welcome! Areas for contribution:
- Expanding knowledge base entries
- Improving skill prompts
- Adding new safety topics
- Updating regulations (as they change)

Please feel free to submit a Pull Request.

## Acknowledgments

Built with:
- [Claude Code](https://claude.com/claude-code) - AI coding assistant
- [Anthropic Claude](https://anthropic.com/) - AI model
- Ontario Ministry of Labour regulations and IHSA guidelines
