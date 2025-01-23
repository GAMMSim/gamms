# Getting Started
**Gamms** is a library designed to simulate adversial games in a graph based world. This guide will help you quickly install and set up Gamms so you can start experimenting as soon as possible.

## Python Requierement
Gamms requires **Python 3.9** or later. If you already have a suitable version installed, skip to [Installation and Setup](#installation-and-setup).

Otherwise, visit the official Python download page to install a compatible version for your device (Windows, Mac, or Linux): [Python](https://www.python.org/downloads/)

## Installation and Setup

Before installing **Gamms**, ensure that [pip](https://pypi.org/project/pip/) is installed. Most Python distributions include pip by default; if you need to install it separately, follow the instructions on the pip documentation page.

Once pip is set up, use the appropriate commands below for your operating system.

### Installing Git

=== "Mac"
   - [Git via Homebrew](https://brew.sh/)
   - [Wget via Homebrew](https://brew.sh/)
=== "Linux"
   - `sudo apt-get install git wget` (Debian/Ubuntu)
   - `sudo dnf install git wget` (Fedora)
   - `sudo pacman -S git wget` (Arch)
=== "Windows"
   - [Git for Windows](https://git-scm.com/download/win)
   - [Wget for Windows](https://gnuwin32.sourceforge.net/packages/wget.htm)


### Creating a Project Folder and Virtual Environment

**Create a new folder** in the directory where you want your project to live. We'll name it `gamms`:
```sh
mkdir gamms
cd gamms
```
**Create a Python virtual environment** within this folder. You can do this using `python` or `python3`, depending on your system:
```sh
python -m venv venv
```

This command will create a subfolder named `venv` that contains your virtual environment files.

**Activate the virtual environment**:

=== "Mac/Linux"
   ```sh
   source venv/bin/activate
   ```

=== "Windows"
   ```cmd
   venv\Scripts\activate
   ```

**Install Gamms** within the virtual environment:
```sh
python -m pip install git+https://github.com/GAMMSim/gamms.git
```

**Verify your installation**:
```py
   import gamms
   print("Gamms version:", gamms.__version__)
```

Once these steps are completed, you will have **Gamms** installed in a clean virtual environment. Remember to activate the virtual environment (step 3) whenever you want to work on your project.


## Running Examples

Clone or download the `examples` directory from [GAMMSim/gamms](https://github.com/GAMMSim/gamms/tree/main/examples).

=== "Git"
   ```sh
   git clone https://github.com/GAMMSim/gamms.git
   mv gamms/examples examples
   rm -rf gamms
   ```

=== "Wget"
   ```sh
   wget https://github.com/GAMMSim/gamms/archive/refs/heads/main.zip
   unzip main.zip
   mv gamms-main/examples examples
   rm -rf gamms-main main.zip
   ```

Execute the script:
```sh
python create_graph.py
```
Verify that a `.pkl` file is successfully created. This indicates that the graph has been created properly.

**Creating Strategy and Configuration Files**

**Step 1**: Create a folder named `games` (in the root of your project directory):
   ```sh
   mkdir games
   ```
**Step 2**: Inside the `games` folder, create three Python files:

   - **`blue_strategy.py`**  
   - **`red_strategy.py`**  
   - **`config.py`**

**Step 3:** Implement the logic for each file according to your specific needs. For example:

   - `blue_strategy.py` might define functions or classes related to the Blue team's strategy.
   - `red_strategy.py` might define functions or classes related to the Red team's strategy.
   - `config.py` might define shared constants, environment variables, or other settings.

