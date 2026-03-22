import random
import copy
from typing import Optional

from database import IngredientDatabase
from dataStrucs import Recipe, Malt, Hop
from variation.recombination import consolidate_duplicates, normalize_malt_weight

#Mutation parameters
DEFAULT_MALT_SIGMA = 0.05  # 5% variation around current grain weights
DEFAULT_ADD_REMOVE_PROB = 0.08
DEFAULT_HOP_SWAP_PROB = 0.15
DEFAULT_BOIL_TIME_MUTATION_PROB = 0.15

MALT_MIN_LBS = 0.02
MALT_MAX_LBS = 20.0
HOP_MIN_OZ = 0.01
BOIL_TIME_RANGE = (0, 90)

STANDARD_HOP_TIMES = [0, 5, 10, 15, 20, 30, 45, 60, 75, 90]

# 1/5 Rule tracking
_mutation_history = [] # stores recent success/failure outcomes (last 50 mutations)
_HISTORY_SIZE = 50
_SUCCESS_TARGET = 0.2  # 1/5 rule: target 20% success rate
_ADAPTATION_CONSTANT = 0.85  # c value should range in [0.8, 1]: σ = σ/c if success rate > 1/5, σ = σ×c if success rate < 1/5


def range_control(val, min_val, max_val):
    """returns min_val if val is less than min_val
       returns max_val if val is greater than max_val
       otherwise returns val"""
    
    return max(min_val, min(max_val, val))


def record_mutation_success(was_successful: bool):
    """Record whether the last mutation produced an improvement.
    
       call this after evaluating if a mutation improved fitness
    """
    _mutation_history.append(was_successful)
    if len(_mutation_history) > _HISTORY_SIZE:
        _mutation_history.pop(0)


def get_adapted_parameters(base_sigma=DEFAULT_MALT_SIGMA, 
                          base_add_remove_prob=DEFAULT_ADD_REMOVE_PROB):
    """Calculate adapted mutation parameters based on recent success rate (1/5 rule).
    
    Follows the 1/5 success rule:
    - σ = σ        if success_rate = 1/5  (no change)
    - σ = σ / c    if success_rate > 1/5
    - σ = σ × c    if success_rate < 1/5
    where success_rate is the % of successful mutations and c ∈ [0.8, 1]
    """
    if len(_mutation_history) < _HISTORY_SIZE:
        return base_sigma, base_add_remove_prob  # Not enough data yet
    
    success_rate = sum(_mutation_history) / _HISTORY_SIZE
    
    sigma = base_sigma
    add_remove_prob = base_add_remove_prob
    
    if success_rate > _SUCCESS_TARGET:
        # Too many successes (p_s > 1/5)
        sigma /= _ADAPTATION_CONSTANT
        add_remove_prob /= _ADAPTATION_CONSTANT
    elif success_rate < _SUCCESS_TARGET:
        # Too few successes (p_s < 1/5)
        sigma *= _ADAPTATION_CONSTANT
        add_remove_prob *= _ADAPTATION_CONSTANT
    
    # Keep within reasonable bounds
    sigma = range_control(sigma, 0.01, 0.2)
    add_remove_prob = range_control(add_remove_prob, 0.02, 0.15)
    
    return sigma, add_remove_prob


def mutate_malt_weights(malts, sigma=DEFAULT_MALT_SIGMA):
    """Apply Gaussian perturbation to all malt masses."""
    for malt in malts:
        old = malt.mass_lbs
        new = old * (1.0 + random.gauss(0, sigma))
        malt.mass_lbs = range_control(new, MALT_MIN_LBS, MALT_MAX_LBS)


def mutate_hop_timing(hops, probability=DEFAULT_BOIL_TIME_MUTATION_PROB):
    """Mutate hop addition times in minutes (low probability)."""
    for hop in hops:
        if random.random() < probability:
            delta = random.randint(-10, 10)
            hop.time_added_mins = int(range_control(hop.time_added_mins + delta, *BOIL_TIME_RANGE))
        #Occasional jump to one of the standard boil times
        elif random.random() < 0.05:
            hop.time_added_mins = random.choice(STANDARD_HOP_TIMES)


def mutate_hop_varieties(hops, ingredient_db, probability=DEFAULT_HOP_SWAP_PROB):
    """Swap hop variety in the schedule (exploration)."""
    if not ingredient_db or not ingredient_db.hops:
        return

    for hop in hops:
        if random.random() < probability:
            alternatives = [h for h in ingredient_db.hops if h['name'] != hop.name] #List of alternative hops excluding the current variety

            new_hop = random.choice(alternatives)
            hop.name = new_hop['name']
            hop.alpha_acid_percent = new_hop['alpha_acid_percent']


def mutate_add_remove_malt(recipe, ingredient_db, prob=DEFAULT_ADD_REMOVE_PROB):
    """Add/remove malt with small probability. Should be a lower chance as fitness improves."""
    if not ingredient_db or not ingredient_db.malts:
        return

    if random.random() >= prob:
        return

    if recipe.malts and random.random() < 0.5 and len(recipe.malts) > 1:
        # remove a random malt
        recipe.malts.pop(random.randrange(len(recipe.malts)))
    else:
        # add a new random malt ingredient
        new_malt = ingredient_db.get_random_malt()
        new_mass = random.uniform(0.2, 1.5)
        recipe.malts.append(Malt(name=new_malt['name'], yield_ppg=new_malt['yield_ppg'], color_srm=new_malt['color_srm'], mass_lbs=new_mass))


def mutate_add_remove_hop(recipe, ingredient_db, prob=DEFAULT_ADD_REMOVE_PROB):
    """Add/remove hop with small probability."""
    if not ingredient_db or not ingredient_db.hops:
        return

    if random.random() >= prob:
        return

    if recipe.hops and random.random() < 0.5 and len(recipe.hops) > 1:
        recipe.hops.pop(random.randrange(len(recipe.hops)))
    else:
        new_hop = ingredient_db.get_random_hop()
        new_amount = random.uniform(0.1, 1.5)
        new_time = random.choice(STANDARD_HOP_TIMES)
        recipe.hops.append(Hop(name=new_hop['name'], alpha_acid_percent=new_hop['alpha_acid_percent'], mass_oz=new_amount, time_added_mins=new_time))


def mutate_recipe(recipe: Recipe,
                  ingredient_db: Optional[IngredientDatabase] = None,
                  sigma: float = DEFAULT_MALT_SIGMA,
                  add_remove_prob: float = DEFAULT_ADD_REMOVE_PROB,
                  hop_swap_prob: float = DEFAULT_HOP_SWAP_PROB,
                  boil_time_prob: float = DEFAULT_BOIL_TIME_MUTATION_PROB,
                  use_adaptive_1_5_rule: bool = True,
                  target_weight: float = 95.0) -> Recipe:
    """Main mutation operator for recipes.

    - Malt weights are perturbed with Gaussian noise, preserving OG/SRM effects in phenotype.
    - Small prob for malt hop add/remove to encourage exploration.
    - Hop variety swap + hop timing mutation for IBU diversity.
    - Adaptive parameters based on 1/5 rule (if use_adaptive_1_5_rule=True).
    """
    child = copy.deepcopy(recipe)

    # Apply 1/5 rule: adapt parameters based on recent mutation success rate
    if use_adaptive_1_5_rule:
        sigma, add_remove_prob = get_adapted_parameters(sigma, add_remove_prob)

    mutate_malt_weights(child.malts, sigma=sigma)
    mutate_hop_timing(child.hops, probability=boil_time_prob)
    mutate_hop_varieties(child.hops, ingredient_db, probability=hop_swap_prob)

    mutate_add_remove_malt(child, ingredient_db, prob=add_remove_prob)
    mutate_add_remove_hop(child, ingredient_db, prob=add_remove_prob)

    # Keep genotype clean and normalized
    child.malts = consolidate_duplicates(child.malts)
    child.malts = normalize_malt_weight(child.malts, target_weight)
    child.hops = consolidate_duplicates(child.hops)

    return child
