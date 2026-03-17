"""
Streamlit web dashboard for interactive beer recipe evolution visualization.
Run with: streamlit run app.py
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from database import IngredientDatabase
from evolutionary_algorithm import EvolutionaryAlgorithm


# Page configuration
st.set_page_config(
    page_title="Genetic Beer Optimizer",
    page_icon="🍺",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🍺 Genetic Beer Recipe Optimizer")
st.markdown("Evolve the perfect beer recipe using genetic algorithms")

# Initialize session state
if "running" not in st.session_state:
    st.session_state.running = False
if "history" not in st.session_state:
    st.session_state.history = None
if "best_recipe" not in st.session_state:
    st.session_state.best_recipe = None

# Load database
db = IngredientDatabase()

# ===== SIDEBAR: Configuration =====
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Beer Style Selection
    st.subheader("Target Beer Style")
    available_styles = list(db.target_beers.keys())
    selected_style = st.selectbox(
        "Select a beer style:",
        options=available_styles,
        help="Choose a predefined beer style to target"
    )
    
    target_beer = db.target_beers[selected_style].copy()
    
    # Detect if target_beer uses ranges or point values
    is_range_format = isinstance(target_beer['og'], tuple)
    
    # Show target stats
    st.subheader("Target Range")
    if is_range_format:
        st.write(f"**OG:** {target_beer['og'][0]:.3f} - {target_beer['og'][1]:.3f}")
        st.write(f"**IBU:** {target_beer['ibu'][0]:.0f} - {target_beer['ibu'][1]:.0f}")
        st.write(f"**SRM:** {target_beer['srm'][0]:.1f} - {target_beer['srm'][1]:.1f}")
    else:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("OG", f"{target_beer['og']:.3f}")
        with col2:
            st.metric("IBU", f"{target_beer['ibu']:.1f}")
        with col3:
            st.metric("SRM", f"{target_beer['srm']:.1f}")
    
    st.write("---")
    
    # Custom ranges option
    st.subheader("Advanced Options")
    use_custom_ranges = st.checkbox(
        "Customize ranges",
        value=False,
        help="Adjust the acceptable ranges for this beer style"
    )
    
    if use_custom_ranges and is_range_format:
        st.write("**Acceptable Ranges:**")
        
        og_min, og_max = st.slider(
            "OG Range",
            min_value=1.0,
            max_value=1.15,
            value=target_beer['og'],
            step=0.005,
            format="%.3f"
        )
        
        ibu_min, ibu_max = st.slider(
            "IBU Range",
            min_value=0.0,
            max_value=100.0,
            value=target_beer['ibu'],
            step=1.0
        )
        
        srm_min, srm_max = st.slider(
            "SRM Range",
            min_value=0.0,
            max_value=40.0,
            value=target_beer['srm'],
            step=0.5
        )
        
        # Convert to range format
        target_beer_config = {
            "og": (og_min, og_max),
            "ibu": (ibu_min, ibu_max),
            "srm": (srm_min, srm_max)
        }
        fitness_strategy = "range_penalty"
    elif is_range_format:
        # Use ranges from beer_styles.csv
        target_beer_config = target_beer
        fitness_strategy = "range_penalty"
    else:
        # Use point values from targets.csv
        target_beer_config = target_beer
        fitness_strategy = "distance"
    
    st.write("---")
    
    # Algorithm Parameters
    st.subheader("Algorithm Parameters")
    
    population_size = st.slider(
        "Population Size (μ)",
        min_value=10,
        max_value=100,
        value=30,
        step=5,
        help="Number of recipes in each generation"
    )
    
    num_generations = st.slider(
        "Number of Generations",
        min_value=10,
        max_value=500,
        value=50,
        step=10,
        help="How many generations to evolve"
    )
    
    num_malts = st.slider(
        "Malts per Recipe",
        min_value=1,
        max_value=5,
        value=2,
        help="Number of different grains in each recipe"
    )
    
    num_hops = st.slider(
        "Hops per Recipe",
        min_value=1,
        max_value=5,
        value=2,
        help="Number of different hop additions in each recipe"
    )
    
    st.write("---")
    
    # Run button
    col1, col2 = st.columns(2)
    with col1:
        start_button = st.button("🚀 Start Evolution")
    with col2:
        clear_button = st.button("🔄 Clear Results")


# ===== MAIN CONTENT =====

if clear_button:
    st.session_state.history = None
    st.session_state.best_recipe = None
    st.experimental_rerun()

if start_button:
    st.session_state.running = True
    
    # Create progress placeholder
    progress_container = st.container()
    status_placeholder = progress_container.empty()
    progress_placeholder = progress_container.empty()
    
    # Initialize EA
    ea = EvolutionaryAlgorithm(
        target_beer=target_beer_config,
        population_size=population_size,
        num_generations=num_generations,
        fitness_strategy=fitness_strategy,
        num_malts=num_malts,
        num_hops=num_hops,
        ingredient_db=db
    )
    
    # Progress tracking
    def progress_callback(generation, best_fitness, avg_fitness, best_recipe):
        progress = generation / num_generations
        progress_placeholder.progress(progress)
        status_placeholder.info(f"Generation {generation}/{num_generations} | Best Fitness: {best_fitness:.4f} | Avg Fitness: {avg_fitness:.4f}")
    
    # Run the algorithm
    best_recipe, history = ea.run(callback=progress_callback)
    
    # Store results
    st.session_state.history = history
    st.session_state.best_recipe = best_recipe
    st.session_state.running = False
    
    # Clear progress indicators
    progress_placeholder.empty()
    status_placeholder.empty()
    
    # Success message
    progress_container.success("✅ Evolution Complete!")


# ===== RESULTS DISPLAY =====

if st.session_state.history and st.session_state.best_recipe:
    st.write("---")
    st.header("📊 Results")
    
    history = st.session_state.history
    best_recipe = st.session_state.best_recipe
    
    # Create visualizations
    st.subheader("📈 Fitness Evolution")
    
    best_fitness_list = list(history['best_fitness'])
    avg_fitness_list = list(history['avg_fitness'])
    generations = list(range(len(best_fitness_list)))
    
    # Create line chart with scatter points
    fig_fitness = go.Figure()
    
    # Add best fitness trace
    fig_fitness.add_trace(go.Scatter(
        x=generations,
        y=best_fitness_list,
        mode='lines+markers',
        name='Best Fitness',
        line=dict(color='#1f77b4', width=2),
        marker=dict(size=5),
        hovertemplate='Generation: %{x}<br>Best Fitness: %{y:.4f}<extra></extra>'
    ))
    
    # Add average fitness trace
    fig_fitness.add_trace(go.Scatter(
        x=generations,
        y=avg_fitness_list,
        mode='lines',
        name='Average Fitness',
        line=dict(color='#ff7f0e', width=2, dash='dash'),
        hovertemplate='Generation: %{x}<br>Avg Fitness: %{y:.4f}<extra></extra>'
    ))
    
    fig_fitness.update_layout(
        xaxis_title="Generation",
        yaxis_title="Fitness (lower is better)",
        height=400,
        hovermode='x unified',
        showlegend=True
    )
    st.plotly_chart(fig_fitness)
    
    st.write("---")
    
    # 3D Trajectory Plot - Show how OG, IBU, SRM evolved
    st.subheader("🌐 Recipe Evolution in 3D Space")
    
    # Extract OG, IBU, SRM from best recipes across generations
    og_trajectory = []
    ibu_trajectory = []
    srm_trajectory = []
    
    for best_recipe_gen in history.get('best_recipe_history', [best_recipe]):
        og_trajectory.append(best_recipe_gen.calculate_original_gravity())
        ibu_trajectory.append(best_recipe_gen.calculate_ibu())
        srm_trajectory.append(best_recipe_gen.calculate_srm())
    
    # If we only have the final recipe, also show it in 3D
    if len(og_trajectory) == 0:
        og_trajectory = [best_recipe.calculate_original_gravity()]
        ibu_trajectory = [best_recipe.calculate_ibu()]
        srm_trajectory = [best_recipe.calculate_srm()]
    
    # Create 3D scatter plot with better color gradient and target marker
    fig_3d = go.Figure()
    
    # Get target values - handle both range and point formats
    if isinstance(target_beer_config['og'], tuple):
        target_og = (target_beer_config['og'][0] + target_beer_config['og'][1]) / 2
        target_ibu = (target_beer_config['ibu'][0] + target_beer_config['ibu'][1]) / 2
        target_srm = (target_beer_config['srm'][0] + target_beer_config['srm'][1]) / 2
    else:
        target_og = target_beer_config['og']
        target_ibu = target_beer_config['ibu']
        target_srm = target_beer_config['srm']
    
    # Plot trajectory with generation-based colors
    gen_colors = generations[:len(og_trajectory)]
    
    # Add trajectory line
    fig_3d.add_trace(go.Scatter3d(
        x=og_trajectory,
        y=ibu_trajectory,
        z=srm_trajectory,
        mode='lines',
        line=dict(
            color=gen_colors,
            colorscale='Plasma',
            width=4,
            showscale=False
        ),
        name='Evolution Path',
        hoverinfo='skip'
    ))
    
    # Add generation points with color gradient
    fig_3d.add_trace(go.Scatter3d(
        x=og_trajectory,
        y=ibu_trajectory,
        z=srm_trajectory,
        mode='markers',
        marker=dict(
            size=7,
            color=gen_colors,
            colorscale='Plasma',
            colorbar=dict(title="Generation", thickness=15, len=0.7),
            showscale=True,
            line=dict(color='white', width=1)
        ),
        text=[f"Gen {g}<br>OG: {og:.3f}<br>IBU: {ib:.1f}<br>SRM: {sr:.1f}" 
              for g, og, ib, sr in zip(gen_colors, og_trajectory, ibu_trajectory, srm_trajectory)],
        hovertemplate='<b>%{text}</b><extra></extra>',
        name='Recipe Generations'
    ))
    
    # Add target point as a larger marker
    fig_3d.add_trace(go.Scatter3d(
        x=[target_og],
        y=[target_ibu],
        z=[target_srm],
        mode='markers+text',
        marker=dict(
            size=12,
            color='red',
            symbol='diamond',
            line=dict(color='darkred', width=2)
        ),
        text=['TARGET'],
        textposition='top center',
        name='Target Style',
        hovertemplate='<b>Target Style</b><br>OG: %{x:.3f}<br>IBU: %{y:.1f}<br>SRM: %{z:.1f}<extra></extra>'
    ))
    
    fig_3d.update_layout(
        title="🌐 Recipe Evolution in 3D Space (OG, IBU, SRM)",
        scene=dict(
            xaxis_title='Original Gravity (OG)',
            yaxis_title='Bitterness (IBU)',
            zaxis_title='Color (SRM)',
            camera=dict(
                eye=dict(x=1.5, y=1.5, z=1.3)
            )
        ),
        height=600,
        showlegend=True,
        legend=dict(x=0.02, y=0.98)
    )
    st.plotly_chart(fig_3d)
    
    st.write("---")
    
    # Best Recipe Metrics - Simple display
    st.subheader("🍻 Best Recipe Metrics")
    
    og = best_recipe.calculate_original_gravity()
    ibu = best_recipe.calculate_ibu()
    srm = best_recipe.calculate_srm()
    
    # Display as metrics in a clean row
    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
    
    # Format target display
    if isinstance(target_beer['og'], tuple):
        og_target = f"Target: {target_beer['og'][0]:.3f}-{target_beer['og'][1]:.3f}"
        ibu_target = f"Target: {target_beer['ibu'][0]:.0f}-{target_beer['ibu'][1]:.0f}"
        srm_target = f"Target: {target_beer['srm'][0]:.1f}-{target_beer['srm'][1]:.1f}"
    else:
        og_target = f"Target: {target_beer['og']:.3f}"
        ibu_target = f"Target: {target_beer['ibu']:.1f}"
        srm_target = f"Target: {target_beer['srm']:.1f}"
    
    with metric_col1:
        st.metric(
            "Original Gravity",
            f"{og:.3f}",
            og_target
        )
    
    with metric_col2:
        st.metric(
            "IBU",
            f"{ibu:.1f}",
            ibu_target
        )
    
    with metric_col3:
        st.metric(
            "Color (SRM)",
            f"{srm:.1f}",
            srm_target
        )
    
    with metric_col4:
        st.metric(
            "Fitness Score",
            f"{best_recipe.fitness_score:.4f}",
            "Lower is better"
        )
    
    st.write("---")
    
    # Malt Bill
    st.subheader("Malt Bill")
    malt_data = []
    for malt in best_recipe.malts:
        malt_data.append({
            "Grain": malt.name,
            "Mass (lbs)": f"{malt.mass_lbs:.2f}",
            "Yield (PPG)": malt.yield_ppg,
            "Color (SRM)": malt.color_srm
        })
    
    if malt_data:
        df_malts = pd.DataFrame(malt_data)
        st.dataframe(df_malts)
    
    # Hop Schedule
    st.subheader("Hop Schedule")
    hop_data = []
    for hop in best_recipe.hops:
        hop_data.append({
            "Hop": hop.name,
            "Amount (oz)": f"{hop.mass_oz:.2f}",
            "Boil Time (min)": hop.time_added_mins,
            "Alpha Acid %": hop.alpha_acid_percent
        })
    
    if hop_data:
        df_hops = pd.DataFrame(hop_data)
        st.dataframe(df_hops)
    
    # Download recipe
    st.write("---")
    
    # Format target values for display
    if isinstance(target_beer['og'], tuple):
        target_og_str = f"{target_beer['og'][0]:.3f} - {target_beer['og'][1]:.3f}"
        target_ibu_str = f"{target_beer['ibu'][0]:.0f} - {target_beer['ibu'][1]:.0f}"
        target_srm_str = f"{target_beer['srm'][0]:.1f} - {target_beer['srm'][1]:.1f}"
    else:
        target_og_str = f"{target_beer['og']:.3f}"
        target_ibu_str = f"{target_beer['ibu']:.1f}"
        target_srm_str = f"{target_beer['srm']:.1f}"
    
    recipe_text = f"""
# {selected_style} Recipe

## Target Style
- OG: {target_og_str}
- IBU: {target_ibu_str}
- SRM: {target_srm_str}

## Best Recipe Generated
- OG: {og:.3f}
- IBU: {ibu:.1f}
- SRM: {srm:.1f}
- Fitness Score: {best_recipe.fitness_score:.4f}

## Malt Bill
"""
    for malt in best_recipe.malts:
        recipe_text += f"\n- {malt.name}: {malt.mass_lbs:.2f} lbs (PPG: {malt.yield_ppg}, Color: {malt.color_srm})"
    
    recipe_text += "\n\n## Hop Schedule\n"
    for hop in best_recipe.hops:
        recipe_text += f"\n- {hop.name}: {hop.mass_oz:.2f} oz ({hop.alpha_acid_percent}% AA) @ {hop.time_added_mins} min"
    
    st.download_button(
        label="📄 Download Recipe as Text",
        data=recipe_text,
        file_name=f"{selected_style.replace(' ', '_')}_recipe.txt",
        mime="text/plain"
    )

else:
    st.info("👈 Configure parameters in the sidebar and click 'Start Evolution' to begin optimizing recipes!")
