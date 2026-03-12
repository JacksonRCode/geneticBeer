from dataclasses import dataclass, asdict
from typing import List

@dataclass
class Malt:
    """
    Represents a single fermentable grain addition in a candidate solution.
    
    The properties without defaults (name, yield, color) represent the STATIC 
    characteristics of the grain, provided by the IngredientDatabase via dictionary unpacking.
    The EA will instantiate this by passing in those static properties and then assigning the 
    EVOLVED `mass_lbs` later.
    """
    name: str
    yield_ppg: float  # Points Per Pound per Gallon (for Original Gravity)
    color_srm: float  # Lovibond/SRM rating
    mass_lbs: float = 0.0

@dataclass
class Hop:
    """
    Represents a single hop addition in a candidate solution.
    
    The EA evolves the `mass_oz` and `time_added_mins` (phenotype expressions),
    while the `name` and `alpha_acid_percent` are static properties provided 
    by the IngredientDatabase when the Hop is first randomly selected.
    """
    name: str
    alpha_acid_percent: float
    mass_oz: float = 0.0
    time_added_mins: int = 0  # e.g., 60 for bittering, 5 for aroma

class Recipe:
    """
    The Genome: Represents a complete candidate solution.
    Also acts as the Phenotype simulator via its calculation methods.
    """
    malts: List[Malt]
    hops: List[Hop]
    volume_gal: float
    fitness_score: float

    def __init__(self, malts: List[Malt], hops: List[Hop], volume_gal: float = 5.0):
        self.malts = malts
        self.hops = hops
        self.volume_gal = volume_gal
        
        # Fitness tracking
        self.fitness_score = 0.0

    def calculate_original_gravity(self) -> float:
        """Calculates the Original Gravity (OG) based on malt yield and mass."""
        total_points = sum([malt.mass_lbs * malt.yield_ppg for malt in self.malts])
        efficiency = 0.75  # 75% extraction efficiency
        return 1.0 + ((total_points * efficiency) / self.volume_gal) / 1000

    def calculate_ibu(self) -> float:
        """Calculates total bitterness using the Tinseth formula."""
        og = self.calculate_original_gravity()
        total_ibu = 0.0
        
        # Bigness factor depends on the total sugar density (OG)
        bigness_factor = 1.65 * (0.000125 ** (og - 1.000))
        
        for hop in self.hops:
            # Boil time factor depends on how long the hop is in the kettle
            boil_time_factor = (1 - (2.71828 ** (-0.04 * hop.time_added_mins))) / 4.15
            utilization = bigness_factor * boil_time_factor
            
            # The Tinseth calculation for this specific hop addition
            hop_ibu = (hop.mass_oz * hop.alpha_acid_percent * utilization * 74.89) / self.volume_gal
            total_ibu += hop_ibu
            
        return total_ibu

    def calculate_srm(self) -> float:
        """Calculates color (SRM) using the Morey equation."""
        mcu = sum([(malt.mass_lbs * malt.color_srm) / self.volume_gal for malt in self.malts])
        return 1.4922 * (mcu ** 0.6859)