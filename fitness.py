# fitness.py
from dataStrucs import Recipe

def fitness_distance(recipe: Recipe, target):
    """
    Normalized
    Fitness based on squared distance to target OG, IBU, SRM.
    Returns fitness
    """
    og = recipe.calculate_original_gravity()
    ibu = recipe.calculate_ibu()
    srm = recipe.calculate_srm()

    #normalize values
    og_range = 0.1 #difference between minimum of all og values in beer_styles.csv and max of all og values
    ibu_range = 100 #same as above, for ibu
    srm_range = 38.5

    og_diff = (target["og"] - og)/og_range
    ibu_diff = (target["ibu"] - ibu)/ibu_range
    srm_diff = (target["srm"] - srm)/srm_range

    fitness = ((og_diff ** 2) + (ibu_diff ** 2) + (srm_diff ** 2))**0.5

    recipe.fitness_score = fitness #store the fitness

    return fitness


def fitness_distance_unormalized(recipe: Recipe, target):
    """
    Fitness based on squared distance to target OG, IBU, SRM.
    Returns fitness
    """
    og = recipe.calculate_original_gravity()
    ibu = recipe.calculate_ibu()
    srm = recipe.calculate_srm()

    og_diff = (target["og"] - og)
    ibu_diff = (target["ibu"] - ibu)
    srm_diff = (target["srm"] - srm)

    fitness = ((og_diff ** 2) + (ibu_diff ** 2) + (srm_diff ** 2))**0.5

    recipe.fitness_score = fitness #store the fitness

    return fitness

def fitness_range_penalty(recipe: Recipe, target_range):
    """ 
    Normalized
    Range-based penalty fitness function.
    Returns fitness_score
    """
    og = recipe.calculate_original_gravity()
    ibu = recipe.calculate_ibu()
    srm = recipe.calculate_srm()

    og_min, og_max = target_range["og"]
    ibu_min, ibu_max = target_range["ibu"]
    srm_min, srm_max = target_range["srm"]

    #normalize values
    og_range = og_max - og_min
    ibu_range = ibu_max - ibu_min
    srm_range = srm_max - srm_min

    og_penalty = 0
    if og < og_min:
        og_penalty = ((og_min - og)/og_range) ** 2
    elif og > og_max:
        og_penalty = ((og - og_max)/og_range) ** 2

    ibu_penalty = 0
    if ibu < ibu_min:
        ibu_penalty = ((ibu_min - ibu)/ibu_range) ** 2
    elif ibu > ibu_max:
        ibu_penalty = ((ibu - ibu_max)/ibu_range) ** 2

    srm_penalty = 0
    if srm < srm_min:
        srm_penalty = ((srm_min - srm)/srm_range) ** 2
    elif srm > srm_max:
        srm_penalty = ((srm - srm_max)/srm_range) ** 2

    fitness = og_penalty + ibu_penalty + srm_penalty

    recipe.fitness_score = fitness #store the fitness

    return fitness