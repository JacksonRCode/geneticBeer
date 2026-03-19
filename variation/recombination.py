# variation/recombination.py
import random
import copy
from dataStrucs import Recipe, Malt

def consolidate_duplicates(ingredients):
    """
    This function merges duplicate ingredients by name.
    Ensures that the genotype is easily readable and efficient. 
    """
    if not ingredients:
        return []
 
    # Use dict to track unique ingredients
    unique = {}
    for item in ingredients:
        if item.name in unique:
            if isinstance(item, Malt):
                unique[item.name].mass_lbs += item.mass_lbs
            else:
                unique[item.name].mass_oz += item.mass_oz
        else:
            unique[item.name] = copy.deepcopy(item)

    return list(unique.values())

def normalize_malt_weight(child_malts, target_weight = 95.0):
    """
    Normalizes malt weights to fit target weight.
    Preserves the ratios while meeting the size requirement.
    """
    total_weight = sum(m.mass_lbs for m in child_malts)
    if total_weight > 0:
        scale_factor = target_weight / total_weight
        for malt in child_malts:
            malt.mass_lbs *= scale_factor

    return child_malts

def component_swap_crossover(parent_a, parent_b):
    """ 
    Recombination strategy that swaps entire blocks of grains or hops.        

    This is an exploitation strategy that will likely be most useful in later generations.
    """
    child_malts = copy.deepcopy(parent_a.malts if random.random() > 0.5 else parent_b.malts)
    child_hops = copy.deepcopy(parent_a.hops if random.random() > 0.5 else parent_b.hops)

    # Clean up messy duplicate data
    child_malts = consolidate_duplicates(child_malts)
    child_hops = consolidate_duplicates(child_hops)

    return Recipe(malts = child_malts, hops = child_hops, volume_gal = parent_a.volume_gal)

def uniform_crossover(parent_a, parent_b, target_weight = 95.0):
    """
    Recombination strategy where we swap based on a coin flip for each individual ingredient.

    This is an exploration strategy that will create high diversity by mixing individual ingredients.

    Note: Uniform crossover uses a longest-list approach to make sure no genetic material is lost when
    parents have different numbers of ingredients. Duplicate consolidation is run post-crossover to maintain
    genome integrity.
    """ 

    # ----- Malts -----
    child_malts = []
    longer = parent_a.malts if len(parent_a.malts) >= len(parent_b.malts) else parent_b.malts
    shorter = parent_b.malts if len(parent_a.malts) >= len(parent_b.malts) else parent_a.malts
    
    for i in range(len(longer)):
        if i < len(shorter):
            # Both have a malt
            choice = parent_a.malts[i] if random.random() > 0.5 else parent_b.malts[i]

        else:
            choice = longer[i]

        child_malts.append(copy.deepcopy(choice))

    # Normalize and consolidate
    child_malts = consolidate_duplicates(child_malts)
    child_malts = normalize_malt_weight(child_malts, target_weight)

    # ----- Hops -----
    child_hops = []
    longer = parent_a.hops if len(parent_a.hops) >= len(parent_b.hops) else parent_b.hops
    shorter = parent_b.hops if len(parent_a.hops) >= len(parent_b.hops) else parent_a.hops
    
    for i in range(len(longer)):
        if i < len(shorter):
            # Both have a malt
            choice = parent_a.hops[i] if random.random() > 0.5 else parent_b.hops[i]

        else:
            choice = longer[i]
            
        child_hops.append(copy.deepcopy(choice))

    child_hops = consolidate_duplicates(child_hops)

    return Recipe(malts = child_malts, hops = child_hops, volume_gal = parent_a.volume_gal)

def weighted_recombination(parent_a, parent_b, target_weight):
    """
    Recombination strategy that takes a weighted sum of malts / hops from each recipe.
    Finds intermediate values between parents.
    """
    alpha = random.random() 
    alpha_h = random.random()

    # Malts
    malt_names = set(m.name for m in parent_a.malts) | set(m.name for m in parent_b.malts)
    map_a = {m.name: m for m in parent_a.malts}
    map_b = {m.name: m for m in parent_b.malts}

    child_malts = []

    for name in malt_names:
        malt_a = map_a.get(name)
        malt_b = map_b.get(name)

        source = malt_a if malt_a is not None else malt_b

        if source:
            base = copy.deepcopy(source)

            w_a = malt_a.mass_lbs if malt_a else 0.0
            w_b = malt_b.mass_lbs if malt_b else 0.0

            base.mass_lbs = (w_a * alpha) + (w_b * (1 - alpha))

            child_malts.append(base)
    
    child_malts = normalize_malt_weight(child_malts, target_weight)

    # Hops
    hop_names = set(h.name for h in parent_a.hops) | set(h.name for h in parent_b.hops)
    map_a_h = {h.name: h for h in parent_a.hops}
    map_b_h = {h.name: h for h in parent_b.hops}

    child_hops = []

    for name in hop_names:
        hop_a = map_a_h.get(name)
        hop_b = map_b_h.get(name)

        # If we have both hops, pick based on alpha_h. Otherwise, pick what exists.
        if hop_a and hop_b:
            source = hop_a if alpha_h >= 0.5 else hop_b
        else:
            source = hop_a if hop_a else hop_b

        if source:
            base = copy.deepcopy(source)

            w_a = hop_a.mass_oz if hop_a else 0.0
            w_b = hop_b.mass_oz if hop_b else 0.0

            base.mass_oz = (w_a * alpha_h) + (w_b * (1 - alpha_h))

            child_hops.append(base)

    return Recipe(child_malts, child_hops, parent_a.volume_gal)
    
