# GAMMS v0.2

GAMMS (Graph based Adversarial Multiagent Modelling Simulator) is a Python library designed for simulating large scale multi-agent scenarios on environments represented as graphs. The library is a framework which focuses on providing a flexible and extensible architecture to facilitate implementing interactions between agents and the environment as well as controlling the information flow between them. The library is geared towards easing development of high level scenario dynamics and testing agent behaviours rather than low level details like the actual physics of real world interactions. GAMMS tries to solve the following problems:

1. Run large simulations involving multiple agents on an everyday laptop.
2. Provide a simple interface to the user to define the agents and the environment.
3. Allow the user to work with the agents and the environment without worrying about the underlying packages.
4. Create a simulater that is easy to use on any operating system (Windows, Mac, Linux) and is easy to install.

The uniqueness of GAMMS comes from *what it is not* trying to be. It is *not* a physics engine, game engine, deep learning library, or a reinforcement learning library. The goal of GAMMS is to provide a framework where the user can use any of these libraries to implement their own agents and environments. Other libraries like [Unity](https://unity.com), [PyBullet](https://pybullet.org/wordpress/), and [OpenAI Gym](https://gymnasium.farama.org/) are great for simulating environments but they are not designed to be used as a framework for multi-agent simulations on graphs. GAMMS is trying to address the niche use for researchers and developers who want to do a quick iterations on their ideas and test them in simulated environments that have limited interactions. GAMMS want to be a tool to create a standardized way for simulating multi-agent systems, making it easier to share and reproduce results.

## Requirements

Python 3.9+ installed with pip.

Package dependecies:
- pygame
- shapely
- networkx
- cbor2
- aenum

## Installation

Installation support is directly from the source code. The package is not available on PyPi yet. If you have git installed,

```bash
pip install "git+https://github.com/GAMMSim/gamms.git"
```

Another option is to download the source code locally and run the following command in the root directory of the project:

```bash
python setup.py install
```

Detailed installation and setup instructions are available in the [Installation Guide](https://gammsim.github.io/gamms/stable/start/#installation-and-setup).

# Documentation

The documentation is available at [GAMMS Documentation](https://gammsim.github.io/gamms/stable/). The documentation is generated using [mkdocs-materials](https://squidfunk.github.io/mkdocs-material/) with mike for versioning. You can do a local build by cloning the repository and serving the documentation using mkdocs. For new users, [Tutorials](https://gammsim.github.io/gamms/stable/tutorials) is a good place to start.
