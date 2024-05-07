import carla
import random
import pygame
import numpy as np
import torch
from torchvision import transforms
from PIL import Image, ImageDraw

# Initialize CARLA client and world
client = carla.Client('localhost', 2000)
client.set_timeout(10.0)
world = client.get_world()

# Set synchronous mode
settings = world.get_settings()
settings.synchronous_mode = True
settings.fixed_delta_seconds = 0.08
world.apply_settings(settings)

# Traffic manager settings
traffic_manager = client.get_trafficmanager()
traffic_manager.set_synchronous_mode(True)
traffic_manager.set_random_device_seed(0)
random.seed(0)

# Spawn an ego vehicle
ego_bp = world.get_blueprint_library().find('vehicle.tesla.model3')
ego_bp.set_attribute('role_name', 'ego')
spawn_points = world.get_map().get_spawn_points()
ego_vehicle = world.spawn_actor(ego_bp, spawn_points[5])

# Set up traffic vehicles
models = ['dodge', 'audi', 'model3', 'mini', 'mustang']
blueprints = [bp for bp in world.get_blueprint_library().filter('*vehicle*') if any(model in bp.id for model in models)]
vehicles = [world.try_spawn_actor(random.choice(blueprints), sp) for sp in random.sample(spawn_points, 10)]
for vehicle in vehicles:
    if vehicle:
        vehicle.set_autopilot(True)

# Define a rendering object
class RenderObject:
    def __init__(self, width, height):
        self.surface = pygame.Surface((width, height))
        self.width = width
        self.height = height

# Initialize and load the detection model
detection_model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)
detection_model.eval()

# Camera sensor callback
def pygame_callback(image, obj):
    img = np.reshape(np.copy(image.raw_data), (image.height, image.width, 4))
    img = img[:, :, :3]
    img = img[:, :, ::-1]
    
    # Convert to PIL image and apply detection model
    img_pil = Image.fromarray(img)
    results = detection_model(img_pil)
    
    # Draw bounding boxes on the PIL image
    draw = ImageDraw.Draw(img_pil)
    for box in results.xyxy[0].numpy():
        draw.rectangle([(box[0], box[1]), (box[2], box[3])], outline='red', width=3)

    # Convert back to Pygame surface
    img_pygame = np.array(img_pil)[:, :, ::-1]  # BGR to RGB
    obj.surface = pygame.surfarray.make_surface(img_pygame.swapaxes(0, 1))

# Main function to run the simulation and visualize detection results
def main():
    camera_init_trans = carla.Transform(carla.Location(x=-4, z=2), carla.Rotation(pitch=-20, yaw=0))
    camera_bp = world.get_blueprint_library().find('sensor.camera.rgb')
    camera_bp.set_attribute('image_size_x', '800')
    camera_bp.set_attribute('image_size_y', '600')
    camera = world.spawn_actor(camera_bp, camera_init_trans, attach_to=ego_vehicle)

    # Start camera with Pygame callback
    renderObject = RenderObject(800, 600)
    camera.listen(lambda image: pygame_callback(image, renderObject))

    pygame.init()
    gameDisplay = pygame.display.set_mode((800, 600), pygame.HWSURFACE | pygame.DOUBLEBUF)
    gameDisplay.fill((0, 0, 0))
    pygame.display.flip()

    crashed = False
    while not crashed:
        world.tick()
        gameDisplay.blit(renderObject.surface, (0, 0))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                crashed = True

    camera.stop()
    pygame.quit()

main()
