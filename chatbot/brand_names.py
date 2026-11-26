"""
Brand and common names -> generic names to look for in DDInter.

Focused on medicines older adults often take together. Each value is a list
of generic names to try in order, because DDInter sometimes uses a different
form (e.g. "Acetylsalicylic acid" for aspirin, "Alendronic acid" for alendronate).

Generic names (e.g. "metoprolol") don't need to be listed here: the matcher
finds them in DDInter directly. Add a line here only for brand names, common
names, or generics DDInter spells differently.

Check which entries are missing from your data:
    python -m chatbot.name_matcher
"""

SYNONYMS = {
    # --- Pain, fever, arthritis ---
    "aspirin": ["acetylsalicylic acid", "aspirin"],
    "bayer": ["acetylsalicylic acid", "aspirin"],
    "ecotrin": ["acetylsalicylic acid", "aspirin"],
    "tylenol": ["acetaminophen", "paracetamol"],
    "panadol": ["acetaminophen", "paracetamol"],
    "parol": ["acetaminophen", "paracetamol"],
    "paracetamol": ["paracetamol", "acetaminophen"],
    "acetaminophen": ["acetaminophen", "paracetamol"],
    "advil": ["ibuprofen"],
    "motrin": ["ibuprofen"],
    "nurofen": ["ibuprofen"],
    "aleve": ["naproxen"],
    "naprosyn": ["naproxen"],
    "celebrex": ["celecoxib"],
    "mobic": ["meloxicam"],
    "voltaren": ["diclofenac"],
    "ultram": ["tramadol"],
    "oxycontin": ["oxycodone"],
    "percocet": ["oxycodone"],
    "vicodin": ["hydrocodone"],
    "norco": ["hydrocodone"],
    "neurontin": ["gabapentin"],
    "lyrica": ["pregabalin"],
    "deltasone": ["prednisone"],

    # --- Blood thinners and antiplatelets ---
    "coumadin": ["warfarin"],
    "jantoven": ["warfarin"],
    "eliquis": ["apixaban"],
    "xarelto": ["rivaroxaban"],
    "plavix": ["clopidogrel"],
    "brilinta": ["ticagrelor"],

    # --- Blood pressure and heart ---
    "norvasc": ["amlodipine"],
    "zestril": ["lisinopril"],
    "prinivil": ["lisinopril"],
    "vasotec": ["enalapril"],
    "altace": ["ramipril"],
    "cozaar": ["losartan"],
    "diovan": ["valsartan"],
    "benicar": ["olmesartan"],
    "lopressor": ["metoprolol"],
    "toprol": ["metoprolol"],
    "tenormin": ["atenolol"],
    "coreg": ["carvedilol"],
    "cardizem": ["diltiazem"],
    "calan": ["verapamil"],
    "lasix": ["furosemide"],
    "microzide": ["hydrochlorothiazide"],
    "hctz": ["hydrochlorothiazide"],
    "aldactone": ["spironolactone"],
    "lanoxin": ["digoxin"],
    "cordarone": ["amiodarone"],
    "pacerone": ["amiodarone"],
    "entresto": ["sacubitril"],
    "nitrostat": ["nitroglycerin"],
    "imdur": ["isosorbide mononitrate"],

    # --- Cholesterol ---
    "lipitor": ["atorvastatin"],
    "zocor": ["simvastatin"],
    "crestor": ["rosuvastatin"],
    "pravachol": ["pravastatin"],
    "zetia": ["ezetimibe"],

    # --- Diabetes ---
    "glucophage": ["metformin"],
    "glucotrol": ["glipizide"],
    "amaryl": ["glimepiride"],
    "januvia": ["sitagliptin"],
    "jardiance": ["empagliflozin"],
    "farxiga": ["dapagliflozin"],
    "actos": ["pioglitazone"],
    "ozempic": ["semaglutide"],
    "trulicity": ["dulaglutide"],
    "lantus": ["insulin glargine"],
    "humalog": ["insulin lispro"],
    "novolog": ["insulin aspart (aspart)", "insulin aspart"],

    # --- Thyroid ---
    "synthroid": ["levothyroxine"],
    "levoxyl": ["levothyroxine"],

    # --- Stomach ---
    "prilosec": ["omeprazole"],
    "nexium": ["esomeprazole"],
    "protonix": ["pantoprazole"],
    "pepcid": ["famotidine"],
    "zofran": ["ondansetron"],

    # --- Bones ---
    "fosamax": ["alendronic acid", "alendronate"],
    "alendronate": ["alendronic acid", "alendronate"],
    "actonel": ["risedronic acid", "risedronate"],
    "risedronate": ["risedronic acid", "risedronate"],
    "boniva": ["ibandronic acid", "ibandronate"],
    "vitamin d": ["cholecalciferol", "ergocalciferol"],
    "vitamin d3": ["cholecalciferol"],
    "calcium": ["calcium carbonate"],

    # --- Prostate and bladder ---
    "flomax": ["tamsulosin"],
    "proscar": ["finasteride"],
    "avodart": ["dutasteride"],
    "ditropan": ["oxybutynin"],
    "myrbetriq": ["mirabegron"],

    # --- Memory and Parkinson's ---
    "aricept": ["donepezil"],
    "namenda": ["memantine"],
    "exelon": ["rivastigmine"],
    "sinemet": ["levodopa"],
    "requip": ["ropinirole"],
    "mirapex": ["pramipexole"],

    # --- Mood, anxiety, sleep ---
    "zoloft": ["sertraline"],
    "prozac": ["fluoxetine"],
    "lexapro": ["escitalopram"],
    "celexa": ["citalopram"],
    "paxil": ["paroxetine"],
    "cymbalta": ["duloxetine"],
    "effexor": ["venlafaxine"],
    "wellbutrin": ["bupropion"],
    "remeron": ["mirtazapine"],
    "desyrel": ["trazodone"],
    "seroquel": ["quetiapine"],
    "xanax": ["alprazolam"],
    "ativan": ["lorazepam"],
    "valium": ["diazepam"],
    "klonopin": ["clonazepam"],
    "ambien": ["zolpidem"],
    "depakote": ["valproic acid"],
    "valproate": ["valproic acid"],

    # --- Lungs and allergy ---
    "singulair": ["montelukast"],
    "spiriva": ["tiotropium"],
    "claritin": ["loratadine"],
    "zyrtec": ["cetirizine"],
    "benadryl": ["diphenhydramine"],

    # --- Gout ---
    "zyloprim": ["allopurinol"],
    "colcrys": ["colchicine"],

    # --- Antibiotics ---
    "zithromax": ["azithromycin"],
    "cipro": ["ciprofloxacin"],
    "levaquin": ["levofloxacin"],
    "bactrim": ["sulfamethoxazole"],
    "augmentin": ["amoxicillin"],
    "flagyl": ["metronidazole"],

    # --- Other ---
    "potassium": ["potassium chloride"],
    "folate": ["folic acid"],
    "viagra": ["sildenafil"],
    "cialis": ["tadalafil"],
}