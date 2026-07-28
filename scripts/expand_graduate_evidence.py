"""Merge source-backed graduate faculty, project, and alumni evidence.

The canonical input remains job_search/config/grad_school_programs.researched.json.
This script deliberately writes to an explicit output path so the merged result can
be inspected before replacing that already-dirty canonical file.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


VERIFIED_ON = "2026-07-28"
PROGRAM_GUARDS = {
    "University of British Columbia (UBC)": "Master of Land and Water Systems",
}


def source(url: str, source_type: str, label: str) -> dict[str, str]:
    return {"url": url, "source_type": source_type, "label": label}


EXPANSIONS: dict[str, dict[str, Any]] = {
    "Khalifa University": {
        "faculty": [
            {
                "name": "Hassan Arafat",
                "title": "Professor, Chemical and Petroleum Engineering",
                "lab_or_group": "Water and Environmental Engineering / RIC2D",
                "profile_urls": [
                    "https://www.ku.ac.ae/college-people/hassan-arafat",
                    "https://khazna.ku.ac.ae/en/persons/hassan-arafat-6/",
                ],
                "profile_sources": [
                    source("https://www.ku.ac.ae/college-people/hassan-arafat", "official_faculty_profile", "Khalifa University faculty page"),
                    source("https://khazna.ku.ac.ae/en/persons/hassan-arafat-6/", "official_research_profile", "Khalifa University research portal"),
                ],
                "recent_papers": [],
                "recent_projects": [
                    {
                        "title": "Anti-fouling remediation strategies for water intake for nuclear reactor cooling systems",
                        "funder": "Emirates Nuclear Energy Company",
                        "period": "2021-2023",
                        "amount": "USD 517,000",
                        "url": "https://www.ku.ac.ae/college-people/hassan-arafat",
                    },
                    {
                        "title": "Light Responsive MOF-based sponges for ultrafast and cost-effective adsorption desalination",
                        "funder": "Abu Dhabi Agriculture and Food Safety Authority",
                        "period": "2021-2023",
                        "amount": "USD 735,000",
                        "url": "https://www.ku.ac.ae/college-people/hassan-arafat",
                    },
                ],
            },
            {
                "name": "Shadi W. Hasan",
                "title": "Professor and Director, Center for Membranes and Advanced Water Technology",
                "lab_or_group": "CMAT / Water and Environmental Engineering",
                "profile_urls": ["https://www.ku.ac.ae/college-people/shadi-w-hasan"],
                "profile_sources": [
                    source("https://www.ku.ac.ae/college-people/shadi-w-hasan", "official_faculty_profile", "Khalifa University faculty page")
                ],
                "recent_papers": [],
                "recent_projects": [
                    {
                        "title": "Solar-Powered Seawater Desalination",
                        "funder": "ASPIRE",
                        "period": "2022-2027",
                        "amount": "USD 1,294,479 (professor page states USD 17,938,584 total programme funding)",
                        "url": "https://www.ku.ac.ae/college-people/shadi-w-hasan",
                    }
                ],
            },
        ]
    },
    "United Arab Emirates University": {
        "faculty": [
            {
                "name": "Mohamed Hamouda",
                "title": "Professor, Civil and Environmental Engineering",
                "lab_or_group": "Water resources, desalination, flood mapping and environmental modelling",
                "profile_urls": ["https://research.uaeu.ac.ae/en/persons/mohamed-hamouda/"],
                "profile_sources": [
                    source("https://research.uaeu.ac.ae/en/persons/mohamed-hamouda/", "official_research_profile", "UAEU research portal")
                ],
                "recent_papers": [
                    {
                        "year": "2026",
                        "title": "Impact of LULC Classification Methods on Runoff Simulation in an Arid Mountainous Watershed Using Remote Sensing and Machine Learning",
                        "venue": "Earth 7(1), 26",
                        "url": "https://research.uaeu.ac.ae/en/persons/mohamed-hamouda/",
                    },
                    {
                        "year": "2025",
                        "title": "Advancements in reverse osmosis desalination: Technology, environment, economy, and bibliometric insights",
                        "venue": "Desalination 598, 118413",
                        "url": "https://research.uaeu.ac.ae/en/persons/mohamed-hamouda/",
                    },
                    {
                        "year": "2025",
                        "title": "A hybrid convolutional neural network model coupled with AdaBoost regressor for flood mapping using geotagged flood photographs",
                        "venue": "Natural Hazards 121(5), 5799-5819",
                        "url": "https://research.uaeu.ac.ae/en/persons/mohamed-hamouda/",
                    },
                ],
                "recent_projects": [],
            }
        ]
    },
    "King Abdullah University of Science and Technology (KAUST)": {
        "faculty": [
            {
                "name": "Noreddine Ghaffour",
                "title": "Professor, Environmental Science and Engineering",
                "lab_or_group": "Water Desalination and Reuse Center / DESAL",
                "profile_urls": ["https://www.kaust.edu.sa/en/study/biomed/faculty/noreddine-ghaffour"],
                "profile_sources": [
                    source("https://www.kaust.edu.sa/en/study/biomed/faculty/noreddine-ghaffour", "official_faculty_profile", "KAUST faculty page")
                ],
                "recent_papers": [],
                "recent_projects": [],
            },
            {
                "name": "Johannes Vrouwenvelder",
                "title": "Professor, Environmental Science and Engineering",
                "lab_or_group": "Water treatment, membrane biofouling, sensing and numerical modelling",
                "profile_urls": ["https://www.kaust.edu.sa/en/study/faculty/vrouwenvelder-johannes"],
                "profile_sources": [
                    source("https://www.kaust.edu.sa/en/study/faculty/vrouwenvelder-johannes", "official_faculty_profile", "KAUST faculty page")
                ],
                "recent_papers": [],
                "recent_projects": [],
            },
            {
                "name": "Peiying Hong",
                "title": "Professor and Program Chair, Environmental Science and Engineering",
                "lab_or_group": "Environmental Microbial Safety and Biotechnology Laboratory",
                "profile_urls": ["https://www.kaust.edu.sa/en/study/faculty/peiying-hong"],
                "profile_sources": [
                    source("https://www.kaust.edu.sa/en/study/faculty/peiying-hong", "official_faculty_profile", "KAUST faculty page")
                ],
                "recent_papers": [],
                "recent_projects": [],
            },
        ]
    },
    "The University of Queensland": {
        "faculty": [
            {
                "name": "Zhiguo Yuan",
                "title": "Honorary Professor and Director, Australian Centre for Water and Environmental Biotechnology",
                "lab_or_group": "Urban water management and environmental biotechnology",
                "profile_urls": ["https://www.eait.uq.edu.au/node/3128"],
                "profile_sources": [
                    source("https://www.eait.uq.edu.au/node/3128", "official_faculty_profile", "UQ EAIT faculty page")
                ],
                "recent_papers": [],
                "recent_projects": [],
            },
            {
                "name": "Liu Ye",
                "title": "Professor, School of Chemical Engineering",
                "lab_or_group": "Urban Water Engineering / net-zero wastewater systems",
                "profile_urls": ["https://chemeng.uq.edu.au/node/7216"],
                "profile_sources": [
                    source("https://chemeng.uq.edu.au/node/7216", "official_faculty_profile", "UQ Chemical Engineering faculty page")
                ],
                "recent_papers": [],
                "recent_projects": [],
            },
        ]
    },
    "The University of Adelaide": {
        "faculty": [
            {
                "name": "Seth Westra",
                "title": "Professor",
                "lab_or_group": "Hydrology, climate extremes and water resources",
                "profile_urls": ["https://researchers.adelaide.edu.au/profile/seth.westra"],
                "profile_sources": [
                    source("https://researchers.adelaide.edu.au/profile/seth.westra", "official_research_profile", "University of Adelaide researcher profile")
                ],
                "recent_papers": [],
                "recent_projects": [],
            },
            {
                "name": "Martin Lambert",
                "title": "Professor",
                "lab_or_group": "Water distribution systems, hydraulics and transient analysis",
                "profile_urls": ["https://researchers.adelaide.edu.au/profile/martin-lambert"],
                "profile_sources": [
                    source("https://researchers.adelaide.edu.au/profile/martin-lambert", "official_research_profile", "University of Adelaide researcher profile")
                ],
                "recent_papers": [],
                "recent_projects": [],
            },
        ]
    },
    "University of Canterbury": {
        "faculty": [
            {
                "name": "Markus Pahlow",
                "title": "Associate Professor",
                "lab_or_group": "Hydrology and Water Resources Engineering",
                "profile_urls": ["https://profiles.canterbury.ac.nz/Markus-Pahlow"],
                "profile_sources": [
                    source("https://profiles.canterbury.ac.nz/Markus-Pahlow", "official_faculty_profile", "University of Canterbury faculty profile")
                ],
                "recent_papers": [],
                "recent_projects": [],
            }
        ],
        "graduate_testimonials": [
            {
                "person": "Anna Meikle",
                "summary": "The alumna says the degree strengthened technical skills and understanding of links between water, environment and society.",
                "context": "Public LinkedIn profile; the exact current role is not exposed, so this is not counted as a verified employment outcome.",
                "sources": [
                    source("https://nz.linkedin.com/in/anna-meikle-662833283", "public_alumni_review", "Anna Meikle public LinkedIn profile")
                ],
            }
        ],
    },
    "KU Leuven / Vrije Universiteit Brussel (IUPWARE consortium)": {
        "faculty": [
            {
                "name": "Patrick Willems",
                "title": "Full Professor, Urban and River Hydrology and Hydraulics",
                "lab_or_group": "Hydraulics and Geotechnics / Hydrology",
                "profile_urls": [
                    "https://bwk.kuleuven.be/hydr/willems.htm",
                    "https://www.kuleuven.be/wieiswie/en/person/00009249",
                ],
                "profile_sources": [
                    source("https://bwk.kuleuven.be/hydr/willems.htm", "official_faculty_profile", "KU Leuven Hydraulics faculty page"),
                    source("https://www.kuleuven.be/wieiswie/en/person/00009249", "official_research_profile", "KU Leuven Who is Who research profile"),
                ],
                "recent_papers": [
                    {
                        "year": "2026",
                        "title": "Rainfall and coastal water level relative timing as drivers of compound flooding in Haikou, China",
                        "venue": "Journal of Hydrology: Regional Studies 66, 103635",
                        "url": "https://www.kuleuven.be/wieiswie/en/person/00009249",
                    }
                ],
                "recent_projects": [
                    {
                        "title": "Developing a design-driven methodology for integrated water management in Flanders - A case study on water storage landscapes in the Brabantse Wouden",
                        "funder": "KU Leuven project record",
                        "period": "2025-2029",
                        "amount": "",
                        "url": "https://www.kuleuven.be/wieiswie/en/person/00009249",
                    }
                ],
            }
        ]
    },
    "University of Waterloo": {
        "faculty": [
            {
                "name": "Bryan Tolson",
                "title": "Professor, Civil and Environmental Engineering",
                "lab_or_group": "Water resources systems analysis and optimization",
                "profile_urls": ["https://uwaterloo.ca/civil-environmental-engineering/profile/btolson"],
                "profile_sources": [
                    source("https://uwaterloo.ca/civil-environmental-engineering/profile/btolson", "official_faculty_profile", "University of Waterloo faculty profile")
                ],
                "recent_papers": [],
                "recent_projects": [],
            },
            {
                "name": "Nandita Basu",
                "title": "Professor and Canada Research Chair",
                "lab_or_group": "Global Water Sustainability and Ecohydrology",
                "profile_urls": ["https://uwaterloo.ca/earth-environmental-sciences/profile/n2basu"],
                "profile_sources": [
                    source("https://uwaterloo.ca/earth-environmental-sciences/profile/n2basu", "official_faculty_profile", "University of Waterloo faculty profile")
                ],
                "recent_papers": [],
                "recent_projects": [],
            },
        ],
        "graduate_destinations": [
            {
                "year_range": "CWP cohort 3 (2015/16); role reconfirmed 2025",
                "destination": "UK DEFRA / Independent Water Commission",
                "role": "Fabiola Alvarado-Revilla - water policy and reform",
                "url": "https://uwaterloo.ca/environment-resources-and-sustainability/news/sers-phd-alumna-honoured-cwp-alumni-achievement-award",
                "source_type": "official_alumni_outcome",
                "source_label": "Waterloo 2025 alumni award profile",
            },
            {
                "year_range": "CWP cohort 3 (2015/16)",
                "destination": "Natural Resources Canada",
                "role": "Sabrina Bedjera - Policy Analyst",
                "url": "https://uwaterloo.ca/collaborative-water-program/",
                "source_type": "official_alumni_outcome",
                "source_label": "CWP official alumni network",
            },
            {
                "year_range": "CWP cohort 4 (2016/17)",
                "destination": "GHD",
                "role": "Chris Muirhead - Water Resources Engineer",
                "url": "https://uwaterloo.ca/collaborative-water-program/",
                "source_type": "official_alumni_outcome",
                "source_label": "CWP official alumni network",
            },
            {
                "year_range": "CWP cohort 1 (2013/14)",
                "destination": "University of Alberta",
                "role": "Maricor Arlos - Assistant Professor, Civil and Environmental Engineering",
                "url": "https://uwaterloo.ca/collaborative-water-program/",
                "source_type": "official_alumni_outcome",
                "source_label": "CWP official alumni network",
            },
        ],
        "graduate_testimonials": [
            {
                "person": "Chris Muirhead",
                "summary": "The alumnus describes the interdisciplinary collaboration as a professional-career enabler.",
                "context": "Official CWP alumni testimonial.",
                "sources": [
                    source("https://uwaterloo.ca/collaborative-water-program/", "public_alumni_review", "CWP official alumni testimonial")
                ],
            },
            {
                "person": "Maricor Arlos",
                "summary": "The alumna says the program shaped how she thinks and works in day-to-day professional activities.",
                "context": "Official CWP alumni testimonial.",
                "sources": [
                    source("https://uwaterloo.ca/collaborative-water-program/", "public_alumni_review", "CWP official alumni testimonial")
                ],
            },
        ],
    },
    "University of British Columbia (UBC)": {
        "faculty": [
            {
                "name": "Leslie Lavkulich",
                "title": "Professor Emeritus and Academic Director, Master of Land and Water Systems",
                "lab_or_group": "Land and water systems, resource management and science-policy",
                "profile_urls": ["https://www.landfood.ubc.ca/leslie-lavkulich/"],
                "profile_sources": [
                    source("https://www.landfood.ubc.ca/leslie-lavkulich/", "official_faculty_profile", "UBC Faculty of Land and Food Systems profile")
                ],
                "recent_papers": [],
                "recent_projects": [],
            }
        ],
        "graduate_destinations": [
            {
                "year_range": "UBC profile published 2019",
                "destination": "BC Hydro",
                "role": "Brittany Myhal - Natural Resource Specialist",
                "url": "https://www.landfood.ubc.ca/brittany-myhal/",
                "source_type": "official_alumni_outcome",
                "source_label": "UBC alumni profile",
            }
        ],
        "graduate_testimonials": [
            {
                "person": "Brittany Myhal",
                "summary": "The alumna reports finding a job immediately after graduation and says the academic experience exceeded expectations, while noting the programme is self-directed and financially demanding.",
                "context": "UBC alumni profile; valuable but dated 2019.",
                "sources": [
                    source("https://www.landfood.ubc.ca/brittany-myhal/", "public_alumni_review", "UBC alumni profile and review")
                ],
            }
        ],
        "application_deadline": "2026/27 academic year: programme paused and not accepting applications; check the official page for later intakes.",
        "official_verification_status": "verified_program_paused_2026_27",
        "source_urls": [
            "https://mlws.landfood.ubc.ca/front-page/",
            "https://www.landfood.ubc.ca/leslie-lavkulich/",
            "https://www.landfood.ubc.ca/brittany-myhal/",
        ],
    },
}


def merge_named(existing: list[Any], additions: list[dict[str, Any]], key: str) -> list[Any]:
    merged = list(existing) if isinstance(existing, list) else []
    positions = {
        str(item.get(key, "")).strip().casefold(): index
        for index, item in enumerate(merged)
        if isinstance(item, dict) and item.get(key)
    }
    for addition in additions:
        identity = str(addition.get(key, "")).strip().casefold()
        if identity in positions:
            merged[positions[identity]] = addition
        else:
            positions[identity] = len(merged)
            merged.append(addition)
    return merged


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    records = json.loads(args.input.read_text(encoding="utf-8"))
    if not isinstance(records, list):
        raise ValueError("Expected the researched graduate source to be a JSON array")

    matched: set[str] = set()
    for record in records:
        if not isinstance(record, dict):
            continue
        university = str(record.get("university", "")).strip()
        expansion = EXPANSIONS.get(university)
        if not expansion:
            continue
        guarded_program = PROGRAM_GUARDS.get(university)
        if guarded_program and record.get("program") != guarded_program:
            continue
        matched.add(university)
        record["faculty"] = merge_named(record.get("faculty", []), expansion.get("faculty", []), "name")
        record["graduate_destinations"] = merge_named(
            record.get("graduate_destinations", []),
            expansion.get("graduate_destinations", []),
            "destination",
        )
        record["graduate_testimonials"] = merge_named(
            record.get("graduate_testimonials", []),
            expansion.get("graduate_testimonials", []),
            "person",
        )
        for field in ("application_deadline", "official_verification_status", "source_urls"):
            if field in expansion:
                record[field] = expansion[field]
        record["faculty_last_verified"] = VERIFIED_ON
        record["last_verified"] = VERIFIED_ON
        record["faculty_evidence_status"] = "source_backed_official_profiles"
        record["faculty_freshness"] = "current_as_of_2026_07_28"

    missing = sorted(set(EXPANSIONS) - matched)
    if missing:
        raise ValueError(f"Expansion targets were not found: {missing}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Expanded {len(matched)} programmes -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
