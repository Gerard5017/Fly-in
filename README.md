*This project has been created as part of the 42 curriculum by emarette.*

# Fly-In Drone Simulation

## Description

Fly-In is a Python-based simulation project that models the coordinated movement of multiple drones through a network of hubs with capacity constraints. The goal is to efficiently route drones from a starting hub to an ending hub while respecting hub capacities, connection limits, and zone-specific movement rules. The project implements pathfinding algorithms to compute optimal routes and manages drone timing to prevent bottlenecks, providing both a command-line simulation and a graphical visualization using Pygame.

The simulation addresses real-world challenges in resource allocation and traffic management, where multiple agents must navigate shared infrastructure with limited capacity. By visualizing the drone movements in real-time, users can observe how different path choices and timing strategies affect overall efficiency.

## Instructions

### Prerequisites

- Python 3.10 or higher
- Required dependencies: `pydantic`, `pygame`

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd fly-in
   ```

2. Install dependencies using pip:
   ```bash
   pip install -r requirements.txt
   ```
   Or if using the pyproject.toml:
   ```bash
   pip install .
   ```

### Execution

Run the simulation with a map file:
```bash
python fly_in.py maps/easy/01_linear_path.txt
```

Replace `maps/easy/01_linear_path.txt` with any `.txt` map file from the `maps/` directory. The program will validate the map, run the simulation, and display the graphical visualization.

### Map Files

Maps are located in the `maps/` directory with different difficulty levels:
- `easy/`: Basic pathfinding
- `medium/`: Intermediate challenges with dead ends and loops
- `hard/`: Complex scenarios with extreme constraints
- `challenger/`: Research-level challenges

## Resources

### Classic References
- **Dijkstra's Algorithm**: The fundamental shortest path algorithm used for initial path computation. Reference: Dijkstra, E. W. (1959). "A note on two problems in connexion with graphs". Numerische Mathematik.
- **Yen's k-Shortest Paths Algorithm**: Used to find multiple alternative paths for load distribution. Reference: Yen, Jin Y. (1971). "Finding the K shortest loopless paths in a network". Management Science.
- **Pygame Documentation**: For graphical visualization. Available at https://www.pygame.org/docs/
- **Graph Theory**: General concepts for network modeling and pathfinding algorithms.

### AI Usage
AI was utilized for several tasks in this project:
- **README Creation**: AI assisted in drafting and structuring the project documentation.
- **Docstring Generation**: AI helped write comprehensive docstrings for Python classes and methods to improve code documentation.
- **Code Linting**: AI was used to run and interpret flake8 linting results for code quality improvement.
- **Debugging**: AI provided guidance and suggestions for identifying and fixing bugs in the simulation logic.
- **Learning Pygame**: AI was consulted for tutorials and examples to understand and implement the graphical visualization features.

## Algorithm Choices and Implementation Strategy

### Pathfinding Algorithm
The core algorithm combines **Dijkstra's shortest path** with **Yen's k-shortest paths** to generate multiple viable routes from start to end. Dijkstra ensures optimal single-path routing by minimizing cumulative zone costs (normal: 1, restricted: 2, priority: 1, blocked: infinite). Yen's algorithm then produces alternative paths by iteratively excluding nodes from previous solutions, ensuring route diversity for load balancing.

### Capacity Management Strategy
Drone assignment uses a proportional distribution based on path bottlenecks (minimum capacity along intermediate hubs). Drones on the same path are staggered with delays calculated as `(drone_count - 1) // bottleneck_capacity` to prevent capacity violations. This approach maximizes throughput while respecting constraints.

### Simulation Execution
The simulation runs turn-by-turn with a history stack for undo functionality. Each turn advances all drones simultaneously, checking capacity limits at hubs and connections. Movement respects zone types: priority zones are preferred for efficiency, restricted zones add delays, and blocked zones are avoided entirely.

### Implementation Details
- **Graph Representation**: Hubs as nodes with metadata (capacity, zone type, coordinates), connections as weighted edges.
- **State Management**: Immutable snapshots for undo/redo, enabling step-by-step analysis.
- **Validation**: Comprehensive map parsing with error handling for malformed inputs.

## Visual Representation Features and User Experience Enhancement

The Pygame-based visualizer provides an interactive, real-time view of the simulation that significantly enhances understanding and debugging:

### Key Features
- **Dynamic Graph Rendering**: Hubs displayed as colored circles (normal/green, restricted/red, priority/blue, rainbow/animated), connections as lines with capacity indicators.
- **Drone Animation**: Smooth interpolation of drone movement between hubs over 1-second animations, with unique colors and labels for each drone.
- **HUD Panel**: Real-time display of turn counter, active drones, completed drones, and simulation status.
- **Interactive Controls**: Arrow keys for step-by-step navigation (forward/backward), spacebar for play/pause, escape to quit.
- **Zone Visualization**: Different hub colors and connection styles clearly distinguish zone types and capacities.

### User Experience Enhancements
- **Real-Time Feedback**: Immediate visual feedback on drone positions, bottlenecks, and capacity violations helps users understand algorithmic decisions.
- **Debugging Aid**: Step-by-step mode allows pausing to analyze specific turns, making it easier to identify optimization opportunities or bugs.
- **Intuitive Interface**: Color-coded elements and animations make complex pathfinding concepts accessible to non-experts.
- **Performance Monitoring**: HUD metrics provide quantitative insights into simulation efficiency and completion status.
- **Scalability**: Smooth animations and responsive controls handle maps with up to 25 drones without performance degradation.

The visualization transforms abstract algorithm outputs into tangible, observable behaviors, enabling users to validate correctness, optimize strategies, and gain deeper insights into multi-agent pathfinding challenges.
