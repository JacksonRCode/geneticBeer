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
from variation.mutation import mutate_recipe


class EvolutionaryAlgorithm:
    """Manages the genetic algorithm evolution process."""
    
    def __init__(self, 
                 target_beer: Dict,
                 population_size: int = 50,
                 num_generations: int = 100,
                 fitness_strategy: str = "distance",
                 num_malts: int = 2,
                 num_hops: int = 2,
                 ingredient_db: IngredientDatabase = None):
        """
        Initialize the evolutionary algorithm.
        
        Args:
            population_size: μ (population size)
            num_generations: Number of generations to evolve
            target_beer: Dictionary with 'og', 'ibu', 'srm' keys (or range dicts for penalty strategy)
            fitness_strategy: "distance" or "range_penalty"
            num_malts: Number of malts per recipe
            num_hops: Number of hops per recipe
            ingredient_db: IngredientDatabase instance
        """
        self.population_size = population_size
        self.num_generations = num_generations
        self.target_beer = target_beer
        self.fitness_strategy = fitness_strategy
        self.num_malts = num_malts
        self.num_hops = num_hops
        self.db = ingredient_db or IngredientDatabase()
        
        # History tracking for visualization
        self.best_fitness_history = []
        self.avg_fitness_history = []
        self.best_recipe_history = []
        self.generation_counter = 0
    
    def _create_random_recipe(self) -> Recipe:
        """Create a single random recipe."""
        malts = []
        for _ in range(self.num_malts):
            malt_dict = self.db.get_random_malt()
            malt = Malt(
                malt_dict["name"],
                malt_dict["yield_ppg"],
                malt_dict["color_srm"],
                mass_lbs=random.uniform(5, 10)
            )
            malts.append(malt)
        
        hops = []
        for _ in range(self.num_hops):
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
    
    def _evaluate_fitness(self, population: List[Recipe]) -> None:
        """Evaluate fitness for entire population."""
        for recipe in population:
            if self.fitness_strategy == "distance":
                fitness_distance(recipe, self.target_beer)
            elif self.fitness_strategy == "range_penalty":
                fitness_range_penalty(recipe, self.target_beer)
    
    def _create_offspring(self, population: List[Recipe]) -> List[Recipe]:
        """
        Create λ offspring through parent selection and variation.
        λ = population_size (2μ in some EA conventions, but simplified here)
        """
        offspring = []
        
        for _ in range(self.population_size):
            # Parent selection via tournament
            parent_a = tournament_selection(population, k=3)
            parent_b = tournament_selection(population, k=3)
            
            # Recombination (alternating strategies for diversity)
            if random.random() < 0.5:
                child = uniform_crossover(parent_a, parent_b)
            else:
                child = component_swap_crossover(parent_a, parent_b)
            
            # Mutation
            mutate_recipe(child, self.db)
            
            offspring.append(child)
        
        return offspring
    
    def _record_generation_stats(self, population: List[Recipe]) -> None:
        """Record statistics for this generation."""
        fitnesses = [r.fitness_score for r in population]
        best_fitness = min(fitnesses)
        avg_fitness = sum(fitnesses) / len(fitnesses)
        
        # Find best recipe
        best_recipe = min(population, key=lambda r: r.fitness_score)
        
        self.best_fitness_history.append(best_fitness)
        self.avg_fitness_history.append(avg_fitness)
        self.best_recipe_history.append(copy.deepcopy(best_recipe))
    
    def run(self, callback=None) -> Tuple[Recipe, Dict]:
        """
        Run the evolutionary algorithm.
        
        Args:
            callback: Optional function to call each generation with progress info
                     callback(generation, best_fitness, avg_fitness, best_recipe)
        
        Returns:
            Tuple of (best_recipe, history_dict)
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
                best_recipe=self.best_recipe_history[0]
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
                    best_recipe=self.best_recipe_history[gen]
                )
        
        # Return best recipe found
        best_recipe = min(population, key=lambda r: r.fitness_score)
        
        history = {
            "best_fitness": self.best_fitness_history,
            "avg_fitness": self.avg_fitness_history,
            "best_recipe": best_recipe,
            "best_recipe_history": self.best_recipe_history,
            "generations": self.num_generations
        }
        
        return best_recipe, history
