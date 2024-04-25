import carla
import random
import logging

# Connect to the Carla server
client = carla.Client('localhost', 2000)
client.set_timeout(10.0)

# Retrieve the Carla world object
world = client.get_world()

# Retrieve the blueprint library
blueprint_library = world.get_blueprint_library()

# Find the Tesla Model 3 blueprint
ego_bp = blueprint_library.find('vehicle.tesla.model3')

# Settings MUST BE SET YOU CAN RUN WORLD
settings = world.get_settings()
settings.synchronous_mode = True # Enables synchronous mode
settings.fixed_delta_seconds = 0.08
world.apply_settings(settings)


#-------------------------
#Spawn ego vehicle
#-------------------------
#ego_bp = world.get_blueprint_library().find('vehicle.tesla.model3')
ego_bp.set_attribute('role_name', 'ego')
print('\nEgo role_name is set')
ego_color = random.choice(ego_bp.get_attribute('color').recommended_values)
ego_bp.set_attribute('color', ego_color)
print('\nEgo color is set')

spawn_points = world.get_map().get_spawn_points()
number_of_spawn_points = len(spawn_points)

if 0 < number_of_spawn_points:
    random.shuffle(spawn_points)
    ego_transform = spawn_points[0]
    ego_vehicle = world.spawn_actor(ego_bp, ego_transform)
    print('\nEgo is spawned')
else:
    logging.warning('Could not found any spawn points')
