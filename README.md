# GAMMS v0.2

## Requirements

Python 3.7+ installed with pip.

## Installation

Clone or download the github repository.

Go to the cloned directory and run

```bash
pip install .
```

to install gamms.

For debug mode,

```bash
pip install -e .
```

## Understanding the example

There are three main components to the game setup:
1. Config file (`config.py`)
2. Graph Creation (`create_graph.py`)
3. Game File (`game.py`)

### Config File

The config file contains all the parameters for the game. It defines the sensors, agents and how individual agents are rendered.

As the config file itself is a python file, it is possible to create multiple layers of config files as well as separate them into separate parts as required. It only needs to be imported in other python files.

In the example, the config file first defines that it wants to use PYGAME for visualization. Code completion itself can be used to see other types. Right now, the only option is PYGAME and NO_VIS (no visualization).

Following that, the file defines the various sensors that need to be created. It is a simple dictionary structure, right now only requiring the type of the sensor. The three types used are NEIGHBOR, AGENT, MAP -- provides the neighboring nodes, information about all agent positions, complete map information. Type hints directly can be used to see the various types.

The agent configuration contains the team id as meta data, the sensors attached to the individual agents, and the start node id for them.

Remaning part is only for defining the window size and agent rendering information for the visualization engine.

### Graph Creation

This file is there for completeness. It is a vanialla example of how to convert a real world location into a networkx graph and dump it.

### Game File

Any game starts with first creating a gamms context. The example file shows how to attach a networkx graph to the context (internally its no longer a networkx graph). Next step is to iterate over the sensor and agent config, and load them in the context.

Do a similar run over the visual setup.

Game rules can now be defined as simple python function that take the context as its argument and checks for something in the game.

Last step is the actual loop where you run the game until the context is terminated (termination condition defined by rules).

Anything that needs to be logged can be directly logged in the loop and saved at any point.