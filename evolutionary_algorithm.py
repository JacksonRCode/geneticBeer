"""
Main Evolutionary Algorithm orchestration.
Runs the genetic algorithm to evolve beer recipes toward a target style.
"""

import random
import copy
from typing import List, Dict, Tuple
from dataStrucs import Recipe, Malt, Hop
from database import IngredientDatabase
from fitness import fitness_distance, fitness_range_penalty
from selection import tournament_selection, survivor_selection
from variation.recombination import uniform_crossover, component_swap_crossover
from variation.mutation import mutate_recipe, record_mutation_success


class EvolutionaryAlgorithm:
    """Manages the genetic algorithm evolution process."""
    
    def __init__(self, 
                 target_beer: Dict,
                 population_size: int = 50,
                 num_generations: int = 100,
                 fitness_strategy: str = "distance",
                 num_malts: int = 2,
                 num_hops: int = 2,
                 ingredient_db: IngredientDatabase = None,
                 tournament_size: int = 2,
                 min_malts: int = None,
                 max_malts: int = None,
                 min_hops: int = None,
                 max_hops: int = None,
                 top_n_results: int = 1,
                 convergence_generations: int = 20,
                 convergence_tolerance: float = 1e-5):
        """
        Initialize the evolutionary algorithm.
        
        Args:
            population_size: μ (population size)
            num_generations: Number of generations to evolve
            target_beer: Dictionary with 'og', 'ibu', 'srm' keys (or range dicts for penalty strategy)
            fitness_strategy: "distance" or "range_penalty"
            num_malts: Fixed number of malts per recipe (if min/max not specified)
            num_hops: Fixed number of hops per recipe (if min/max not specified)
            ingredient_db: IngredientDatabase instance
            tournament_size: k value for tournament selection
            min_malts: Minimum malts per recipe (if None, uses num_malts)
            max_malts: Maximum malts per recipe (if None, uses num_malts)
            min_hops: Minimum hops per recipe (if None, uses num_hops)
            max_hops: Maximum hops per recipe (if None, uses num_hops)
            top_n_results: Number of top recipes to return
            convergence_generations: Number of generations without improvement to trigger early stop
            convergence_tolerance: Minimum fitness change to count as improvement
        """
        self.population_size = population_size
        self.num_generations = num_generations
        self.target_beer = target_beer
        self.fitness_strategy = fitness_strategy
        self.num_malts = num_malts
        self.num_hops = num_hops
        self.tournament_size = tournament_size
        self.top_n_results = top_n_results
        self.convergence_generations = convergence_generations
        self.convergence_tolerance = convergence_tolerance
        self.db = ingredient_db or IngredientDatabase()
        
        # Set malt/hop ranges
        self.min_malts = min_malts if min_malts is not None else num_malts
        self.max_malts = max_malts if max_malts is not None else num_malts
        self.min_hops = min_hops if min_hops is not None else num_hops
        self.max_hops = max_hops if max_hops is not None else num_hops
        
        # History tracking for visualization
        self.best_fitness_history = []
        self.avg_fitness_history = []
        self.best_recipe_history = []
        self.generation_counter = 0
        self.diversity_history = []
        self.generations_to_convergence = None
    
    def _create_random_recipe(self) -> Recipe:
        """Create a single random recipe with variable malt/hop counts."""
        # Randomly choose number of malts and hops within the specified ranges
        num_malts = random.randint(self.min_malts, self.max_malts)
        num_hops = random.randint(self.min_hops, self.max_hops)
        
        malts = []
        for _ in range(num_malts):
            malt_dict = self.db.get_random_malt()
            malt = Malt(
                malt_dict["name"],
                malt_dict["yield_ppg"],
                malt_dict["color_srm"],
                mass_lbs=random.uniform(5, 10)
            )
            malts.append(malt)
        
        hops = []
        for _ in range(num_hops):
            hop_dict = self.db.get_random_hop()
            hop = Hop(
                hop_dict["name"],
                hop_dict["alpha_acid_percent"],
                mass_oz=random.uniform(0.5, 2),
                time_added_mins=random.choice([5, 15, 30, 60])
            )
            hops.append(hop)
        
        return Recipe(malts, hops)
    
    def _initialize_population(self) -> List[Recipe]:
        """Create initial random population."""
        return [self._create_random_recipe() for _ in range(self.population_size)]
    
    def _evaluate_recipe(self, recipe: Recipe) -> float:
        """Evaluate fitness for a single recipe."""
        if self.fitness_strategy == "distance":
            fitness_distance(recipe, self.target_beer)
        elif self.fitness_strategy == "range_penalty":
            fitness_range_penalty(recipe, self.target_beer)
        return recipe.fitness_score
    
    def _evaluate_fitness(self, population: List[Recipe]) -> None:
        """Evaluate fitness for entire population."""
        for recipe in population:
            self._evaluate_recipe(recipe)
    
    def _calculate_diversity(self, population: List[Recipe]) -> float:
        """
        Calculate population diversity as average pairwise distance in phenotypic space (OG, IBU, SRM).
        Higher values indicate more diverse recipes. Range: 0-infinity (unbounded).
        """
        if len(population) < 2:
            return 0.0
        
        # Extract phenotypes (OG, IBU, SRM) for all recipes
        phenotypes = []
        for recipe in population:
            og = recipe.calculate_original_gravity()
            ibu = recipe.calculate_ibu()
            srm = recipe.calculate_srm()
            phenotypes.append((og, ibu, srm))
        
        # Calculate average pairwise Euclidean distance
        total_distance = 0.0
        pair_count = 0
        
        for i in range(len(phenotypes)):
            for j in range(i + 1, len(phenotypes)):
                og1, ibu1, srm1 = phenotypes[i]
                og2, ibu2, srm2 = phenotypes[j]
                
                # Euclidean distance (normalized by typical ranges)
                og_range = 0.15  # typical OG range
                ibu_range = 100.0  # typical IBU range
                srm_range = 40.0  # typical SRM range
                
                distance = (
                    ((og1 - og2) / og_range) ** 2 +
                    ((ibu1 - ibu2) / ibu_range) ** 2 +
                    ((srm1 - srm2) / srm_range) ** 2
                ) ** 0.5
                
                total_distance += distance
                pair_count += 1
        
        avg_distance = total_distance / pair_count if pair_count > 0 else 0.0
        return avg_distance
    
    def _check_convergence(self) -> bool:
        """Check if algorithm has converged (no improvement for N generations)."""
        if len(self.best_fitness_history) < self.convergence_generations:
            return False
        
        # Check if best fitness has improved in the last N generations
        recent_best = self.best_fitness_history[-self.convergence_generations:]
        first = recent_best[0]
        last = recent_best[-1]
        
        improvement = abs(first - last)
        return improvement < self.convergence_tolerance
    
    def _recipes_are_equivalent(self, recipe1: Recipe, recipe2: Recipe, mass_tolerance: float = 0.5) -> bool:
        """
        Check if two recipes are equivalent.
        Considers ingredient names and masses (with tolerance for floating point).
        Order-independent.
        
        Args:
            recipe1: First recipe
            recipe2: Second recipe
            mass_tolerance: Tolerance in lbs for malt mass and oz for hops
        
        Returns:
            True if recipes are equivalent, False otherwise
        """
        # Check malt equivalence
        if len(recipe1.malts) != len(recipe2.malts):
            return False
        
        # Sort malts by name for order-independent comparison
        malts1_sorted = sorted(recipe1.malts, key=lambda m: m.name)
        malts2_sorted = sorted(recipe2.malts, key=lambda m: m.name)
        
        for m1, m2 in zip(malts1_sorted, malts2_sorted):
            if m1.name != m2.name or abs(m1.mass_lbs - m2.mass_lbs) > mass_tolerance:
                return False
        
        # Check hop equivalence
        if len(recipe1.hops) != len(recipe2.hops):
            return False
        
        # Sort hops by name for order-independent comparison
        hops1_sorted = sorted(recipe1.hops, key=lambda h: h.name)
        hops2_sorted = sorted(recipe2.hops, key=lambda h: h.name)
        
        for h1, h2 in zip(hops1_sorted, hops2_sorted):
            if h1.name != h2.name or abs(h1.mass_oz - h2.mass_oz) > mass_tolerance or h1.time_added_mins != h2.time_added_mins:
                return False
        
        return True
    
    def _get_unique_recipes_with_counts(self, recipes: List[Recipe]) -> List[Tuple[Recipe, int]]:
        """
        Deduplicate recipes and count how many candidates match each unique recipe.
        
        Args:
            recipes: List of recipes to deduplicate
        
        Returns:
            List of (recipe, count) tuples sorted by fitness (ascending), then by count (descending).
            Lower fitness is better. Higher count indicates more robust solution.
        """
        unique_recipes_with_counts = []
        matched_indices = set()
        
        # Find unique recipes
        for i, recipe in enumerate(recipes):
            if i in matched_indices:
                continue
            
            # Count how many recipes match this one
            count = 1
            for j in range(i + 1, len(recipes)):
                if j not in matched_indices and self._recipes_are_equivalent(recipe, recipes[j]):
                    count += 1
                    matched_indices.add(j)
            
            unique_recipes_with_counts.append((recipe, count))
        
        # Sort by fitness (ascending - lower is better), then by count (descending - more candidates = more robust)
        unique_recipes_with_counts.sort(key=lambda x: (x[0].fitness_score, -x[1]))
        
        return unique_recipes_with_counts
    
    def _create_offspring(self, population: List[Recipe]) -> List[Recipe]:
        """
        Create λ offspring through parent selection and variation.
        λ = population_size (2μ in some EA conventions, but simplified here)
        """
        offspring = []
        
        for _ in range(self.population_size):
            # Parent selection via tournament with configurable k
            parent_a = tournament_selection(population, k=self.tournament_size)
            parent_b = tournament_selection(population, k=self.tournament_size)
            
            # Recombination (alternating strategies for diversity)
            if random.random() < 0.5:
                child = uniform_crossover(parent_a, parent_b)
            else:
                child = component_swap_crossover(parent_a, parent_b)
            
            # Mutation with parent fitness tracking
            parent_fitness = parent_a.fitness_score  # Use one parent's fitness for comparison
            mutate_recipe(child, self.db)
            
            # Record mutation success for 1/5 rule
            child_fitness = self._evaluate_recipe(child)
            was_improvement = child_fitness < parent_fitness
            record_mutation_success(was_improvement)
            
            offspring.append(child)
        
        return offspring
    
    def _record_generation_stats(self, population: List[Recipe]) -> None:
        """Record statistics for this generation."""
        fitnesses = [r.fitness_score for r in population]
        best_fitness = min(fitnesses)
        avg_fitness = sum(fitnesses) / len(fitnesses)
        diversity = self._calculate_diversity(population)
        
        # Find best recipe
        best_recipe = min(population, key=lambda r: r.fitness_score)
        
        self.best_fitness_history.append(best_fitness)
        self.avg_fitness_history.append(avg_fitness)
        self.diversity_history.append(diversity)
        self.best_recipe_history.append(copy.deepcopy(best_recipe))
    
    def run(self, callback=None) -> Tuple[List[Recipe], Dict]:
        """
        Run the evolutionary algorithm.
        
        Args:
            callback: Optional function to call each generation with progress info
                     callback(generation, best_fitness, avg_fitness, best_recipe, diversity)
        
        Returns:
            Tuple of (top_n_recipes, history_dict)
        """
        # Initialize population
        population = self._initialize_population()
        self._evaluate_fitness(population)
        self._record_generation_stats(population)
        
        if callback:
            callback(
                generation=0,
                best_fitness=self.best_fitness_history[0],
                avg_fitness=self.avg_fitness_history[0],
                best_recipe=self.best_recipe_history[0],
                diversity=self.diversity_history[0]
            )
        
        # Main evolutionary loop
        for gen in range(1, self.num_generations):
            self.generation_counter = gen
            
            # Create offspring through variation
            offspring = self._create_offspring(population)
            
            # Evaluate offspring
            self._evaluate_fitness(offspring)
            
            # Survivor selection: (μ, λ) - select best μ from offspring only
            population = survivor_selection(population, offspring, self.population_size)
            
            # Record statistics
            self._record_generation_stats(population)
            
            if callback:
                callback(
                    generation=gen,
                    best_fitness=self.best_fitness_history[gen],
                    avg_fitness=self.avg_fitness_history[gen],
                    best_recipe=self.best_recipe_history[gen],
                    diversity=self.diversity_history[gen]
                )
            
            # Check for convergence
            if self._check_convergence():
                self.generations_to_convergence = gen
                break
        
        # Get top N best UNIQUE recipes from final population
        population_sorted = sorted(population, key=lambda r: r.fitness_score)
        unique_recipes_with_counts = self._get_unique_recipes_with_counts(population_sorted)
        
        # Take top N unique recipes
        top_n_recipes = [recipe for recipe, count in unique_recipes_with_counts[:self.top_n_results]]
        recipe_counts = {id(recipe): count for recipe, count in unique_recipes_with_counts[:self.top_n_results]}
        
        history = {
            "best_fitness": self.best_fitness_history,
            "avg_fitness": self.avg_fitness_history,
            "diversity": self.diversity_history,
            "best_recipe": top_n_recipes[0],
            "top_recipes": top_n_recipes,
            "recipe_counts": recipe_counts,  # Maps recipe id to count
            "best_recipe_history": self.best_recipe_history,
            "generations": len(self.best_fitness_history),
            "generations_to_convergence": self.generations_to_convergence,
            "converged": self.generations_to_convergence is not None
        }
        
        return top_n_recipes, history
