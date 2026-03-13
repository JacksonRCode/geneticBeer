## Evolutionary Beer Recipe Generator
#### Group Project - CISC 455/851
___
### Overview
##### This project implements a Genetic Algorithm (GA) to automate the creation of beer recipes. Given a target beer style (defined by Original Gravity, Bitterness, and Colour), the system evolves a population of candidate recipes until it finds an optimal brew that meets the specific style guidelines.
___
### System Architecture
#### 1. Representation
Using Python Dataclasses, we represent a recipe as a complex genotype:
- Malt Bill: A list of fermentable grains with specific yields and colour ratings.
- Hop Schedule: A list of hop additions with varying alpha-acid percentages and boil timings.
- Phenotype Simulation: The Recipe class includes a built-in simulator that calculates real-world brewing metrics (OG, IBU, SRM) using the Tinseth and Morey equations.
#### 2. Variation (Recombination and Mutation)
- Hybrid recombination strategies: A mix of Componenet Swapping, Uniform Crossover, and Arithmetic Blending.
- Genetic Repair: Automated consolidation of duplicate ingredients and proportional mass scaling to ensure every child is "brewable".
- Mutation: 
#### 3. Selection and Fitness
___
### Getting Started
#### Prerequisites
- Python 3.10+
- (Optional) matplotlib (or whatever we end up using) for plotting fitness curves
- Other
___
### Installation
```
git clone https://github.com/JacksonRCode/geneticBeer.git
cd geneticBeer
pip install -r requirements.txt
```
___
### Running the Optimizer (Or my guess as to how we will do it eventually)
```
python main.py --style "IPA" --generations 100 --population_size 50
```
___
### Results
___
### Team
- Jackson Reid
- Rowan Mohammed
- Brandon Liang
- George Salib
- Kevin _____
