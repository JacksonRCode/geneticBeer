# fitness.py
from dataStrucs import Recipe

OG_STD  = 0.0172
IBU_STD = 16.00
SRM_STD = 9.67

def fitness_distance(recipe: Recipe, target):
    """
    Normalized
    Fitness based on squared distance to target OG, IBU, SRM.
    Returns fitness
    """
    og = recipe.calculate_original_gravity()
    ibu = recipe.calculate_ibu()
    srm = recipe.calculate_srm()

    og_diff = (target["og"] - og)/OG_STD
    ibu_diff = (target["ibu"] - ibu)/IBU_STD
    srm_diff = (target["srm"] - srm)/SRM_STD

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

    og_penalty = 0
    if og < og_min:
        og_penalty = ((og_min - og)/OG_STD) ** 2
    elif og > og_max:
        og_penalty = ((og - og_max)/OG_STD) ** 2

    ibu_penalty = 0
    if ibu < ibu_min:
        ibu_penalty = ((ibu_min - ibu)/IBU_STD) ** 2
    elif ibu > ibu_max:
        ibu_penalty = ((ibu - ibu_max)/IBU_STD) ** 2

    srm_penalty = 0
    if srm < srm_min:
        srm_penalty = ((srm_min - srm)/SRM_STD) ** 2
    elif srm > srm_max:
        srm_penalty = ((srm - srm_max)/SRM_STD) ** 2

    fitness = og_penalty + ibu_penalty + srm_penalty

    recipe.fitness_score = fitness #store the fitness

    return fitness