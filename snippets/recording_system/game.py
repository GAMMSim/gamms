import gamms, gamms.osm
import config
import random
import blue_strategy
import red_strategy

ctx = gamms.create_context(vis_engine=config.VIS_ENGINE) # create a context with PYGAME as the visual engine

G = gamms.osm.graph_from_xml(config.XML_FILE, resolution=config.RESOLUTION, tolerance=config.TOLERANCE, bidirectional=config.BIDIRECTIONAL)
ctx.graph.attach_networkx_graph(G) # attach the graph to the context

# Create the graph visualization

graph_artist = ctx.visual.set_graph_visual(**config.graph_vis_config) # set the graph visualization with width 1980 and height 1080

# Record
ctx.record.start(path="recording")

# Create recorded component
@ctx.record.component(struct={
    'step': int,
    'max_steps': int,
    'red_tag_score': int,
    'blue_tag_score': int,
    'red_capture_score': int,
    'blue_capture_score': int,
    }
)
class ReportCard:
    def __init__(self):
        self.step = 0
        self.max_steps = config.MIN_SIM_STEPS
        self.red_tag_score = 0
        self.blue_tag_score = 0
        self.red_capture_score = 0
        self.blue_capture_score = 0


report_card = ReportCard(name="report_card")


# Create all the sensors
for name, sensor in config.sensor_config.items():
    ctx.sensor.create_sensor(name, sensor['type'], **sensor)

# Create all the sensors visualization
for name, sensor_config in config.sensor_vis_config.items():
    artist = ctx.visual.set_sensor_visual(name, **sensor_config)

red_team = [name for name in config.agent_config if config.agent_config[name]['meta']['team'] == 0]
blue_team = [name for name in config.agent_config if config.agent_config[name]['meta']['team'] == 1]

# Start position of the agents
nodes = ctx.graph.graph.nodes
node_keys = list(nodes.keys())
blue_territory = set()
red_territory = set()
for name in red_team:
    start_node = random.choice(node_keys)
    config.agent_config[name]['start_node_id'] = start_node
    node_keys.remove(start_node)
    removes = set()
    for node_id in node_keys:
        if (nodes[start_node].x - nodes[node_id].x)**2 + (nodes[start_node].y - nodes[node_id].y)**2 < config.TERRITORY_RADIUS**2:
            red_territory.add(node_id)
            removes.add(node_id)
    
    for node_id in removes:
        node_keys.remove(node_id)

for name in blue_team:
    start_node = random.choice(node_keys)
    config.agent_config[name]['start_node_id'] = start_node
    node_keys.remove(start_node)
    removes = set()
    for node_id in node_keys:
        if (nodes[start_node].x - nodes[node_id].x)**2 + (nodes[start_node].y - nodes[node_id].y)**2 < config.TERRITORY_RADIUS**2:
            blue_territory.add(node_id)
            removes.add(node_id)
    
    for node_id in removes:
        node_keys.remove(node_id)

red_start_dict = {name: config.agent_config[name]['start_node_id'] for name in red_team}
blue_start_dict = {name: config.agent_config[name]['start_node_id'] for name in blue_team}


@ctx.sensor.custom(name="CAPTURE")
class CapturableSensor(gamms.typing.ISensor):
    def __init__(self, ctx, sensor_id, capturable_nodes, range: float = 160.0):
        self.ctx = ctx
        self.capturable_nodes = capturable_nodes
        self._data = {}
        self._sensor_id = sensor_id
        self._range = range
        self._owner = None
    
    def set_owner(self, owner):
        self._owner = owner
    
    @property
    def type(self):
        return gamms.sensor.SensorType.CUSTOM
        
    @property
    def data(self):
        return self._data
    
    @property
    def sensor_id(self):
        return self._sensor_id
    
    def sense(self, node_id):
        node = self.ctx.graph.graph.get_node(node_id)
        self._data.clear()
        for cnode_id in self.capturable_nodes:
            capturable_node = self.ctx.graph.graph.get_node(cnode_id)
            dist = (node.x - capturable_node.x)**2 + (node.y - capturable_node.y)**2
            if dist < self._range**2:
                self._data[cnode_id] = dist**0.5
        
    
    def update(self, data):
        return

@ctx.sensor.custom(name="TERRITORY")
class TerritorySensor(gamms.typing.ISensor):
    def __init__(self, ctx, sensor_id, red_nodes, blue_nodes, range: float = 160.0):
        self.ctx = ctx
        self.red_nodes = red_nodes
        self.blue_nodes = blue_nodes
        self._data = {'red': {}, 'blue': {}}
        self._sensor_id = sensor_id
        self._range = range
        self._owner = None
    
    def set_owner(self, owner):
        self._owner = owner
    
    @property
    def type(self):
        return gamms.sensor.SensorType.CUSTOM
        
    @property
    def data(self):
        return self._data
    
    @property
    def sensor_id(self):
        return self._sensor_id
    
    def sense(self, node_id):
        node = self.ctx.graph.graph.get_node(node_id)
        self._data.clear()
        self._data['red'] = {}
        self._data['blue'] = {}
        for cnode_id in self.red_nodes:
            territory_node = self.ctx.graph.graph.get_node(cnode_id)
            dist = (node.x - territory_node.x)**2 + (node.y - territory_node.y)**2
            if dist < self._range**2:
                self._data['red'][cnode_id] = dist**0.5
        for cnode_id in self.blue_nodes:
            territory_node = self.ctx.graph.graph.get_node(cnode_id)
            dist = (node.x - territory_node.x)**2 + (node.y - territory_node.y)**2
            if dist < self._range**2:
                self._data['blue'][cnode_id] = dist**0.5
    
    def update(self, data):
        return

# Territory nodes artist
def draw_territory_nodes(ctx, data):
    size = data.get('size', 10)
    sensor = ctx.sensor.get_sensor(data['sensor'])
    for node_id in sensor.data['red']:
        node = ctx.graph.graph.get_node(node_id)
        ctx.visual.render_circle(node.x, node.y, size, color=(255, 0, 0))
    for node_id in sensor.data['blue']:
        node = ctx.graph.graph.get_node(node_id)
        ctx.visual.render_circle(node.x, node.y, size, color=(0, 0, 255))

# Capturable nodes artist
def draw_capturable_nodes(ctx, data):
    width = data.get('width', 10)
    height = data.get('height', 10)
    sensor = ctx.sensor.get_sensor(data['sensor'])
    color = data.get('color', (0, 0, 0))
    if sensor is not None:
        return
    for node_id in sensor.data:
        node = ctx.graph.graph.get_node(node_id)
        ctx.visual.render_rectangle(node.x, node.y, width, height, color=color)
    
# Create all the agents
for name, agent in config.agent_config.items():
    ctx.agent.create_agent(name, **agent)

# Create capture sensors
for name in red_team:
    sensor_id = f"capture_{name}"
    sensor = CapturableSensor(ctx, sensor_id, list(blue_start_dict.values()), range=160.0)
    ctx.sensor.add_sensor(sensor)
    ctx.agent.get_agent(name).register_sensor(sensor_id, sensor)
    artist = gamms.visual.Artist(
        ctx,
        drawer=draw_capturable_nodes,
        layer=39,
    )
    artist.data['sensor'] = sensor.sensor_id
    artist.data['width'] = 10.0
    artist.data['height'] = 10.0
    artist.data['color'] = (0, 0, 255)
    ctx.visual.add_artist(sensor_id, artist)

for name in blue_team:
    sensor_id = f"capture_{name}"
    sensor = CapturableSensor(ctx, sensor_id, list(red_start_dict.values()), range=160.0)
    ctx.sensor.add_sensor(sensor)
    ctx.agent.get_agent(name).register_sensor(sensor_id, sensor)
    artist = gamms.visual.Artist(
        ctx,
        drawer=draw_capturable_nodes,
        layer=39,
    )
    artist.data['sensor'] = sensor.sensor_id
    artist.data['width'] = 10.0
    artist.data['height'] = 10.0
    artist.data['color'] = (255, 0, 0)
    ctx.visual.add_artist(sensor_id, artist)

# Create territory sensors
for name in red_team:
    sensor_id = f"territory_{name}"
    sensor = TerritorySensor(ctx, sensor_id, list(red_territory), list(blue_territory), range=160.0)
    ctx.sensor.add_sensor(sensor)
    ctx.agent.get_agent(name).register_sensor(sensor_id, sensor)
    artist = gamms.visual.Artist(
        ctx,
        drawer=draw_territory_nodes,
        layer=39,
    )
    artist.data['sensor'] = sensor.sensor_id
    artist.data['size'] = 10.0
    ctx.visual.add_artist(sensor_id, artist)

for name in blue_team:
    sensor_id = f"territory_{name}"
    sensor = TerritorySensor(ctx, sensor_id, list(blue_territory), list(red_territory), range=160.0)
    ctx.sensor.add_sensor(sensor)
    ctx.agent.get_agent(name).register_sensor(sensor_id, sensor)
    artist = gamms.visual.Artist(
        ctx,
        drawer=draw_territory_nodes,
        layer=39,
    )
    artist.data['sensor'] = sensor.sensor_id
    artist.data['size'] = 10.0
    ctx.visual.add_artist(sensor_id, artist)

# Create all agents visualization
for name, vis_config in config.agent_vis_config.items():
    artist = ctx.visual.set_agent_visual(name, **vis_config)

for node_id in nodes:
    for red_agent in red_team:
        start = config.agent_config[red_agent]['start_node_id']
        if (nodes[start].x - nodes[node_id].x)**2 + (nodes[start].y - nodes[node_id].y)**2 < config.TERRITORY_RADIUS**2:
            red_territory.add(node_id)
            break
    for blue_agent in blue_team:
        start = config.agent_config[blue_agent]['start_node_id']
        if (nodes[start].x - nodes[node_id].x)**2 + (nodes[start].y - nodes[node_id].y)**2 < config.TERRITORY_RADIUS**2:
            blue_territory.add(node_id)
            break


strategies = blue_strategy.mapper(
    blue_team,
)

for name, strategy in strategies.items():
    ctx.agent.get_agent(name).register_strategy(strategy)

strategies = red_strategy.mapper(
    red_team,
)

for name, strategy in strategies.items():
    ctx.agent.get_agent(name).register_strategy(strategy)

del strategies


def tag_rule(ctx):
    for red_agent in red_team:
        for blue_agent in blue_team:
            ragent = ctx.agent.get_agent(red_agent)
            bagent = ctx.agent.get_agent(blue_agent)
            if ragent.current_node_id == bagent.current_node_id:
                if ragent.current_node_id in red_territory:
                    # Red team gets a point
                    report_card.red_tag_score = report_card.red_tag_score + 1
                    # Reset only the blue agent to its starting position
                    bagent.current_node_id = blue_start_dict[blue_agent]
                    bagent.prev_node_id = blue_start_dict[blue_agent]
                    report_card.max_steps = report_card.max_steps + config.STEP_INCREMENT
                elif ragent.current_node_id in blue_territory:
                    # Blue team gets a point
                    report_card.blue_tag_score = report_card.blue_tag_score + 1
                    # Reset only the red agent to its starting position
                    ragent.current_node_id = red_start_dict[red_agent]
                    ragent.prev_node_id = red_start_dict[red_agent]
                    report_card.max_steps = report_card.max_steps + config.STEP_INCREMENT
                else:
                    # Reset the agents to their starting positions
                    ragent.current_node_id = red_start_dict[red_agent]
                    bagent.current_node_id = blue_start_dict[blue_agent]
                    ragent.prev_node_id = red_start_dict[red_agent]
                    bagent.prev_node_id = blue_start_dict[blue_agent]


def capture_rule(ctx):
    for red_agent in red_team:
        agent = ctx.agent.get_agent(red_agent)
        for val in blue_start_dict.values():
            if agent.current_node_id == val:
                # Red team gets a point
                report_card.red_capture_score = report_card.red_capture_score + 1
                # Reset the agent to its starting position
                agent.current_node_id = red_start_dict[red_agent]
                agent.prev_node_id = red_start_dict[red_agent]
                report_card.max_steps = report_card.max_steps + config.STEP_INCREMENT
    
    for blue_agent in blue_team:
        agent = ctx.agent.get_agent(blue_agent)
        for val in red_start_dict.values():
            if agent.current_node_id == val:
                # Blue team gets a point
                report_card.blue_capture_score = report_card.blue_capture_score + 1
                # Reset the agent to its starting position
                agent.current_node_id = blue_start_dict[blue_agent]
                agent.prev_node_id = blue_start_dict[blue_agent]
                report_card.max_steps = report_card.max_steps + config.STEP_INCREMENT


def termination_rule(ctx):
    if report_card.step >= report_card.max_steps or report_card.step >= config.MAX_SIM_STEPS:
        ctx.terminate()


ctx.visual.simulate() # Draw loop for the visual engine

while not ctx.is_terminated(): # run the loop until the context is terminated
    report_card.step = report_card.step + 1 # increment the step
    state_dict = {}
    for agent in ctx.agent.create_iter():
        # Get the current state of the agent
        state = agent.get_state() # get the state of the agent
        state_dict[agent.name] = state
    
    for agent in ctx.agent.create_iter():
        agent.strategy(state_dict[agent.name]) # call the strategy function of the agent
    
    for agent in ctx.agent.create_iter():
        agent.set_state() # set the state of the agent    

    ctx.visual.simulate() # Draw loop for the visual engine
    capture_rule(ctx) # check capture rule
    tag_rule(ctx) # check tag rule
    red_team_score = report_card.red_tag_score + report_card.red_capture_score
    blue_team_score = report_card.blue_tag_score + report_card.blue_capture_score
    print(f"Step: {report_card.step}/{report_card.max_steps} | Red Team Score: {red_team_score} | Blue Team Score: {blue_team_score}", " "*10, end="\r")
    termination_rule(ctx) # check termination rule
