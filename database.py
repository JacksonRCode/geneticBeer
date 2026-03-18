import csv
import random
from typing import Dict

class IngredientDatabase:
    """
    A unified data source loader for the EA.
    Loads flat CSV files of available brewing ingredients into memory
    once at startup to facilitate rapid random sampling during Initialization and Mutation.
    """
    # This class variable holds the solitary instance of the database across the entire application.
    _instance = None
    
    # Type hints explicitly added to make Pyright/Pylance aware of the 
    # structure populated by the CSV parser, fixing static typing errors.
    malts: list[Dict]
    hops: list[Dict]
    target_beers: Dict[str, Dict[str, float]]

    def __new__(cls, malts_file: str = "malts.csv", hops_file: str = "hops.csv", targets_file: str = "beer_styles.csv"):
        # The Singleton Pattern:
        # Check if the class has already been instantiated anywhere else in the code.
        # If it hasn't, create it using the superclass constructor, and call _load_data() 
        # to read the CSVs from the hard drive into memory.
        if cls._instance is None:
            cls._instance = super(IngredientDatabase, cls).__new__(cls)
            cls._instance._load_data(malts_file, hops_file, targets_file)
        
        # Whether newly created or returning an existing one, hand back the exact same
        # object in memory. This ensures the hard drive is only accessed once, preventing
        # massive IO bottlenecks during the EA's generational loop.
        return cls._instance

    def _load_data(self, malts_file: str, hops_file: str, targets_file: str):
        # Initialize the arrays that will hold the parsed CSV data.
        self.malts = []
        self.hops = []
        self.target_beers = {}
        
        # Load Target Beers
        try:
            with open(targets_file, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    # Check if this is the range format (beer_styles.csv) or point format (targets.csv)
                    if 'og_min' in row and 'og_max' in row:
                        # Range format from beer_styles.csv
                        self.target_beers[row["style"]] = {
                            "og": (float(row["og_min"]), float(row["og_max"])),
                            "ibu": (float(row["ibu_min"]), float(row["ibu_max"])),
                            "srm": (float(row["srm_min"]), float(row["srm_max"]))
                        }
                    else:
                        # Point format from targets.csv
                        self.target_beers[row["style"]] = {
                            "og": float(row["og"]),
                            "ibu": float(row["ibu"]),
                            "srm": float(row["srm"])
                        }
        except FileNotFoundError:
             print(f"Warning: {targets_file} not found. Target beers will be unavailable.")
        
        # Load Malts
        try:
            # We explicitly specify UTF-8 to handle any weird characters in ingredient names.
            with open(malts_file, mode='r', encoding='utf-8') as file:
                # DictReader automatically treats the first row of the CSV as keys for the dictionary.
                reader = csv.DictReader(file)
                for row in reader:
                    # Append a structured dictionary to our in-memory list.
                    # We must cast the numeric attributes to floats, because CSV 
                    # values automatically come through as strings.
                    self.malts.append({
                        "name": row["name"],
                        "yield_ppg": float(row["yield_ppg"]),
                        "color_srm": float(row["color_srm"])
                    })
        except FileNotFoundError:
            print(f"Warning: {malts_file} not found. EA cannot run without Malt definitions.")

        # Load Hops (using the identical strategy as Malts)
        try:
            with open(hops_file, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    self.hops.append({
                        "name": row["name"],
                        "alpha_acid_percent": float(row["alpha_acid_percent"])
                    })
        except FileNotFoundError:
             print(f"Warning: {hops_file} not found. EA cannot run without Hop definitions.")

    def get_random_malt(self) -> Dict:
        """Returns a copy of a random malt dictionary from the available pool."""
        # Using .copy() is critical! Dictionaries in Python are passed by reference.
        # If we didn't copy it, and an EA mutation changed an attribute on the 
        # returned dict, it would permanently corrupt the "master" database in memory.
        return random.choice(self.malts).copy()

    def get_random_hop(self) -> Dict:
        """Returns a copy of a random hop dictionary from the available pool."""
        return random.choice(self.hops).copy()

    def get_target_beer(self, style: str) -> Dict[str, float]:
        """Returns the target parameter values for a specific beer style."""
        if style in self.target_beers:
            return self.target_beers[style].copy()
        raise ValueError(f"Target beer style '{style}' not found. Available: {list(self.target_beers.keys())}")
