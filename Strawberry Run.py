# things to add (possibly:
# - each level collecting a different thing for different person
# - each level collect dfferent item for an ingredient
# - depth perception 

import pygame
import os
import sys
import random
import time
import keyboard
import math

pygame.init()
pygame.font.init()
pygame.mixer.init()

# initialize window, drawing onto surface will scale with fullscreen
SCALE = 4
WIDTH, HEIGHT = 160 * (SCALE), 90 * SCALE
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
fscreen = screen.copy()
pygame.display.set_caption("Strawberry Run")

COLLECTED_FONT = pygame.font.Font("assets/manaspace/manaspc.ttf", 20)
PLAY_AGAIN_FONT = pygame.font.Font("assets/manaspace/manaspc.ttf", 22)
COLLECT_SOUND = pygame.mixer.Sound("assets/sounds/videogame-jump-type-sound-fx.wav")
DAMAGE_SOUND = pygame.mixer.Sound("assets/sounds/Fire.wav")
BARK_SOUND = pygame.mixer.Sound("assets/sounds/bark.wav")


BG_MUSIC = pygame.mixer.music.load("assets/sounds/compassionate-cafe.mp3")
pygame.mixer.music.play(-1)

class Object:
	def __init__(self, x, y, width, height, type):
		self.x = x
		self.y = y
		self.width = width
		self.height = height
		self.type = type

	def make_rect(self):
		return pygame.Rect(self.x, self.y, self.width, self.height)

class Start_Sign:
	def __init__(self, y):
		self.y = y
		self.move_up = False
		self.move_down = True

# constants
FPS = 120

WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
RED = (255, 0 ,0)
BLACK = (0,0,0)

OBJECT_GEN_RATE = 75

VEL = 2

WALK_FRAMES = list(range(1, 9))

CANVAS_SIZE_LENGTH = 16

GROUND_RATIO = 0.5

COLLECT_TO_WIN = 11
STRAWBERRY_SPAWN_RATE = 10

HERO_WIDTH, HERO_HEIGHT = 11, 14
HERO_SPRITE_LEFT_WHITESPACE, HERO_SPRITE_TOP_WHITESPACE = 3, 2
HERO_SCALE = 4

OBJECT_WIDTH, OBJECT_HEIGHT = 8 * HERO_SCALE, 8 * HERO_SCALE

CENTER_W, CENTER_H = WIDTH // 2 , WIDTH // 2


MAX_HEALTH = 100
HEALTH_BAR_SCALE = 2

HEALTH_BAR_WIDTH, HEALTH_BAR_HEIGHT = MAX_HEALTH * HEALTH_BAR_SCALE, 20

HOW_FAR_TO_WALK = 500

# add unique events
STRAWBERRY_HIT = pygame.USEREVENT + 1
SPIKE_HIT = pygame.USEREVENT + 2

TOP_LANE = HEIGHT - (HEIGHT * GROUND_RATIO) 

BOT_LANE = HEIGHT - (HERO_HEIGHT * SCALE) # bigger num

ONE_THIRD_LANE = (2/3) * (TOP_LANE) + (1/3) * (BOT_LANE)

TWO_THIRD_LANE =(2/3) * (BOT_LANE) + (1/3) * (TOP_LANE)


LANE_POSITIONS = [TOP_LANE, ONE_THIRD_LANE, TWO_THIRD_LANE, BOT_LANE]

# global objects
class Movement:
	def __init__(self):
		self.right = True
		self.left = False
		self.up = False
		self.down = False
		self.moving = False
		self.walkCount = 0
		self.relx = WIDTH // 4
		self.x = WIDTH // 4
		self.y = LANE_POSITIONS[2]
		self.health = 500
		self.score = 0
		self.dead = False

		# moving right when right it specifically pressed (needed for correct tick counting)
		self.movingright = False
		self.movingleft = False

		lane_index = 0
		
		
hero_movement = Movement()

# images
HERO_SPRITESHEET = pygame.image.load("assets/sprites/amy.png")
BACKGROUND = pygame.transform.scale(pygame.image.load("assets/sprites/bgback.png"), (WIDTH, HEIGHT))
FOREGROUND = pygame.transform.scale(pygame.image.load("assets/sprites/fg.png"), (WIDTH, HEIGHT))
STRAWBERRY_SPRITE = pygame.image.load("assets/sprites/strawberry.png")
SPIKE_SPRITE = pygame.image.load("assets/sprites/spike.png")
START_SIGN = pygame.transform.scale(pygame.image.load("assets/sprites/woodsign.png"), (WIDTH * 0.85, HEIGHT * 0.85))
STRAWBERRY_WALL = pygame.transform.scale(pygame.image.load("assets/sprites/strawberrywall.png"), (WIDTH, HEIGHT))
DOG_SPRITESHEET = pygame.image.load("assets/sprites/bambi.png")
HOUSE = pygame.transform.scale(pygame.image.load("assets/sprites/logcabin.png"), (350, 250))
HOUSE_TOP = pygame.transform.scale(pygame.image.load("assets/sprites/logcabintop.png"), (350, 250))
CAKE = pygame.transform.scale(pygame.image.load("assets/sprites/cake.png"), (64, 64))

BG_IMAGES = [BACKGROUND, FOREGROUND]

background_scroll = 0
strawberrywall_scroll = 0
strawberrywall_iterations = 2

GAMESTATES = ["start", "game", "walk", "end", "thanks"]

DIALOGUE_BOX_X, DIALOGUE_BOX_Y = WIDTH // 3, HEIGHT * GROUND_RATIO - 50

# change file icon
pygame.display.set_icon(pygame.transform.scale(STRAWBERRY_SPRITE, (128, 128)))

def main():

	# start at start screen
	state_index = 0

	# var for end of game
	end_seq = 0
	dog_walk_cnt = 0
	dog_tick = 0
	dog_x = WIDTH + 400
	dog_y = (int(HEIGHT * GROUND_RATIO) + HEIGHT) // 2

	# get sprites
	hero_sprite, hero_walk_ani = get_sprites()
	dog_still, dog_walk_r, dog_walk_l = get_dog_sprites()
	strawberry = get_obj_sprite(STRAWBERRY_SPRITE, 0, OBJECT_WIDTH, OBJECT_HEIGHT, HERO_SCALE, BLACK, CANVAS_SIZE_LENGTH // 2)
	spike = get_obj_sprite(SPIKE_SPRITE, 0, OBJECT_WIDTH, OBJECT_HEIGHT, HERO_SCALE, BLACK, CANVAS_SIZE_LENGTH // 2)

	# health bar outline
	health_bar_outline = pygame.Rect(7, 7, HEALTH_BAR_WIDTH + 6, HEALTH_BAR_HEIGHT + 6)
	
	run = True
	tick_cnt = 0
	objects_list = []
	collected = 0
	health = MAX_HEALTH
	positions = set()
	final_x = math.inf
	in_front_of_house = False

	sign_pos = Start_Sign(1)
	sign_text1 = PLAY_AGAIN_FONT.render("HELP WANTED:", True, BLACK)
	sign_text1 = pygame.transform.scale(sign_text1, (sign_text1.get_width() * 1.25, sign_text1.get_height() * 1.25))
	sign_text2 = PLAY_AGAIN_FONT.render(f"Need {COLLECT_TO_WIN} strawberries", True, BLACK)
	sign_text3 = PLAY_AGAIN_FONT.render("for my cake, Thanks :)", True, BLACK)
	sign_text4 = PLAY_AGAIN_FONT.render("Press ENTER to start", True, BLACK)
	sign_text5 = PLAY_AGAIN_FONT.render("(Use arrow keys to move)", True, BLACK)
	sign_text5 = pygame.transform.scale(sign_text5, (sign_text1.get_width(), sign_text1.get_height() * 0.75))
	sign_text = [sign_text1, sign_text2, sign_text3, sign_text4, sign_text5]
	
	dialogue1 = PLAY_AGAIN_FONT.render("Thanks for getting the strawberries for me!", True, WHITE)
	dialogue1_2 = PLAY_AGAIN_FONT.render("Although, I may need to wash them...", True, WHITE)
	dialogue1 = pygame.transform.scale(dialogue1, (dialogue1.get_width() // 2, dialogue1.get_height() // 2))
	dialogue1_2 = pygame.transform.scale(dialogue1_2, (dialogue1_2.get_width() // 2, dialogue1_2.get_height() // 2))
	dialogue2 = PLAY_AGAIN_FONT.render("I'll make sure to share some cake with you!", True, WHITE)
	dialogue2 = pygame.transform.scale(dialogue2, (dialogue2.get_width() // 2, dialogue2.get_height() // 2))
	dialogue_box1 = pygame.Rect(DIALOGUE_BOX_X, DIALOGUE_BOX_Y, dialogue2.get_width() + 20, 50)
	dialogue_box2 = pygame.Rect(DIALOGUE_BOX_X + 2.5, DIALOGUE_BOX_Y + 2.5, dialogue2.get_width() + 20 - 4, 50 - 5)
	dialogue_press_enter = PLAY_AGAIN_FONT.render("(press ENTER)", True, WHITE)
	dialogue_press_enter = pygame.transform.scale(
		dialogue_press_enter, (dialogue_press_enter.get_width() // 3 , dialogue_press_enter.get_height() // 3))
	dialogue_box = [dialogue_box1, dialogue_box2, dialogue_press_enter]

	thanks_text = PLAY_AGAIN_FONT.render("Thanks for playing!", True, WHITE)


	pygame.time.Clock().tick(FPS)
	while run:
		gamestate = GAMESTATES[state_index]

		# slow down everything
		pygame.time.delay(5)

		hero_hitbox = pygame.Rect(hero_movement.x, hero_movement.y, 
			HERO_WIDTH * HERO_SCALE, (HERO_HEIGHT * HERO_SCALE))

		# update health bar
		green_health_bar = pygame.Rect(10, 10, HEALTH_BAR_WIDTH - (
			(MAX_HEALTH - health) * HEALTH_BAR_SCALE), HEALTH_BAR_HEIGHT)
		red_health_bar = pygame.Rect(10 + HEALTH_BAR_WIDTH - (
			(MAX_HEALTH - health) * HEALTH_BAR_SCALE), 
			10, HEALTH_BAR_WIDTH - (health * HEALTH_BAR_SCALE ), HEALTH_BAR_HEIGHT)
		health_bar = [green_health_bar, red_health_bar]
		

		# functions that may post event
		handle_objects(hero_hitbox, objects_list)

		# events
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				run = False
				pygame.quit()
				sys.exit()

			if event.type == pygame.VIDEORESIZE:
				screen = pygame.display.set_mode(event.size, pygame.RESIZABLE)

			# update stats if object hit 
			if event.type == STRAWBERRY_HIT:
				collected += 1
				COLLECT_SOUND.play()

			if event.type == SPIKE_HIT:
				health -= 20
				DAMAGE_SOUND.play()


		# start menu
		if gamestate == GAMESTATES[0]:
			if sign_pos.y <= 0:
				sign_pos.move_down = True
				sign_pos.move_up = False
			if sign_pos.y == HEIGHT - START_SIGN.get_height():
				sign_pos.move_down = False
				sign_pos.move_up = True

			if sign_pos.move_down:
				sign_pos.y += 0.25

			else:
				sign_pos.y -= 0.25

			draw_start_sign(sign_pos.y, sign_text)

			keys_pressed = pygame.key.get_pressed()
			if keys_pressed[pygame.K_RETURN]:
				state_index += 1


		# main gameplay
		elif gamestate == GAMESTATES[1]:
			# generate an object every 300 ticks
			# onlt add tick if new position is greateer than all previous positions
			positions.add(hero_movement.relx)
			if hero_movement.movingright and\
				all(hero_movement.relx >= item for item in positions):
				tick_cnt += 1
				if tick_cnt > OBJECT_GEN_RATE:
					tick_cnt = tick_cnt - OBJECT_GEN_RATE
					generate_object(objects_list)



			keys_pressed = pygame.key.get_pressed()
			hero_events(keys_pressed, objects_list, final_x)
			
			draw_window(hero_sprite, hero_walk_ani, objects_list, 
				strawberry, spike, hero_hitbox)

			draw_stat_bar(collected, health_bar, health_bar_outline)

			# if player dies, end loop and change screen
			if red_health_bar.width == HEALTH_BAR_WIDTH:
				hero_movement.dead = True
				hero_events(keys_pressed, objects_list, final_x)
				draw_window(hero_sprite, hero_walk_ani, objects_list, 
					strawberry, spike, hero_hitbox)
				draw_stat_bar(collected, health_bar, health_bar_outline)
				# if user wants to end gain, quit
				if end_game():
					pygame.event.post(pygame.event.Event(pygame.QUIT))
				# otherwise, restart
				else:
					pygame.time.delay(500)
					main()

			if collected == COLLECT_TO_WIN:
				hero_movement.relx = hero_movement.x
				final_x = hero_movement.relx + HOW_FAR_TO_WALK
				state_index += 1


		# get to dog
		elif gamestate == GAMESTATES[2]:
			# user hits final x, end loop, give strawberries
			if hero_movement.relx >= final_x:
				# go to next state
				state_index += 1
			
			keys_pressed = pygame.key.get_pressed()
			hero_events(keys_pressed, objects_list, final_x)

			if hero_movement.movingright:
				dog_x -= VEL
				
			elif hero_movement.movingleft:
				dog_x += VEL


			draw_window(hero_sprite, hero_walk_ani, objects_list, 
				strawberry, spike, hero_hitbox)
			draw_stat_bar(collected, health_bar, health_bar_outline)

			# ONLY MOVE HOUSE AT THIS STATE
			house_x = dog_x
			# draw house and dog at final x
			fscreen.blit(HOUSE, (house_x + 30, 
				((int(HEIGHT * GROUND_RATIO) + HEIGHT) // 2 - HOUSE.get_height())))
			fscreen.blit(dog_still[0], (dog_x, dog_y))



		# player win scene
		# hands over strawberries to dog
		elif gamestate == GAMESTATES[3]:
			# make player still
			hero_movement.moving, hero_movement.up, hero_movement.down = False, False, False

			# end sequence
			if end_seq == 0:
				# redraw everything (so that user is still)
				draw_window(hero_sprite, hero_walk_ani, objects_list, 
					strawberry, spike, hero_hitbox)
				draw_stat_bar(collected, health_bar, health_bar_outline)
				fscreen.blit(dog_still[0], (dog_x, dog_y))
				fscreen.blit(HOUSE, (house_x + 30, 
					((int(HEIGHT * GROUND_RATIO) + HEIGHT) // 2 - HOUSE.get_height())))

				# draw dialogue
				display_dialogue(dialogue1, dialogue_box)
				display_dialogue(dialogue1_2, dialogue_box)

				end_seq += 1

			# dog walks over to player
			elif end_seq == 1:
				# dog walking animation with slow down
				dog_tick += 1
				if dog_tick >= 5:
					dog_tick = 0
					dog_walk_cnt += 1
				if dog_walk_cnt >= (len(dog_walk_l)):
					dog_walk_cnt = 0

				draw_window(hero_sprite, hero_walk_ani, objects_list, 
					strawberry, spike, hero_hitbox)
				draw_stat_bar(collected, health_bar, health_bar_outline)

				if dog_x >= hero_movement.x + hero_hitbox.width:
					# move dog towards user by normalizing vector
					# get distance x, distance y
					dx, dy = (hero_movement.x + hero_hitbox.width) - dog_x, (
						hero_movement.y + (hero_hitbox.height//2)) - dog_y
					hypotenuse = math.hypot(dx, dy)
					try: 
						dx, dy = dx/hypotenuse, dy/hypotenuse
					except ZeroDivisionError:
						end_seq += 1
					
					dog_x += dx * 1.25
					dog_y += dy * 1.25
				else:
					end_seq += 1

				# draw house and dog at final x 
				fscreen.blit(dog_walk_l[dog_walk_cnt], (dog_x, dog_y))
				fscreen.blit(HOUSE, (house_x + 30, 
					((int(HEIGHT * GROUND_RATIO) + HEIGHT) // 2 - HOUSE.get_height())))

			elif end_seq == 2:
				draw_window(hero_sprite, hero_walk_ani, objects_list, 
					strawberry, spike, hero_hitbox)
				draw_stat_bar(collected, health_bar, health_bar_outline)
				fscreen.blit(dog_still[1], (dog_x, dog_y))
				fscreen.blit(HOUSE, (house_x + 30, 
					((int(HEIGHT * GROUND_RATIO) + HEIGHT) // 2 - HOUSE.get_height())))	

				# draw dialogue
				display_dialogue(dialogue2, dialogue_box)

				end_seq += 1

			# walk walks into house
			elif end_seq == 3:
				# dog walking animation with slow down
				dog_tick += 1
				if dog_tick >= 5:
					dog_tick = 0
					dog_walk_cnt += 1
				if dog_walk_cnt >= (len(dog_walk_l)):
					dog_walk_cnt = 0

				draw_window(hero_sprite, hero_walk_ani, objects_list, 
						strawberry, spike, hero_hitbox)
				draw_stat_bar(collected, health_bar, health_bar_outline)

				# walk to front of house
				if not in_front_of_house:	
					if dog_x <= house_x + HOUSE.get_width()//2 - 100:
						# move dog towards user by normalizing vector
						# get distance x, distance y
						dx, dy = (house_x + HOUSE.get_width()//2 - 100) - dog_x, (
							int(HEIGHT * GROUND_RATIO) + HEIGHT) // 2 - 10 - dog_y
						hypotenuse = math.hypot(dx, dy)
						try: 
							dx, dy = dx/hypotenuse, dy/hypotenuse
						except ZeroDivisionError:
							end_seq += 1
						
						dog_x += dx * 1.25
						dog_y += dy * 1.25
					else:
						in_front_of_house = True
				# walk into house
				else:
					if dog_x <= house_x + HOUSE.get_width()//2:
						# move dog towards user by normalizing vector
						# get distance x, distance y
						dx, dy = (house_x + HOUSE.get_width()//2) - dog_x, (
							int(HEIGHT * GROUND_RATIO) + HEIGHT) // 2 - 40 - dog_y
						hypotenuse = math.hypot(dx, dy)
						try: 
							dx, dy = dx/hypotenuse, dy/hypotenuse
						except ZeroDivisionError:
							end_seq += 1
						
						dog_x += dx * 1.25
						dog_y += dy * 1.25
					else:
						end_seq += 1

				fscreen.blit(HOUSE, (house_x + 30, 
					((int(HEIGHT * GROUND_RATIO) + HEIGHT) // 2 - HOUSE.get_height())))		
				fscreen.blit(dog_walk_r[dog_walk_cnt], (dog_x, dog_y))
				fscreen.blit(HOUSE_TOP, (house_x + 30, 
					((int(HEIGHT * GROUND_RATIO) + HEIGHT) // 2 - HOUSE.get_height())))
			
			else:
				state_index += 1

		# thank you screen
		elif gamestate == GAMESTATES[4]:
				fscreen.fill(BLACK)
				fscreen.blit(thanks_text, (WIDTH // 2 - thanks_text.get_width() // 2, 
					HEIGHT // 2 - thanks_text.get_height() // 2))
				fscreen.blit(CAKE, (WIDTH // 2 - CAKE.get_width() // 2, 
					HEIGHT // 2 - CAKE.get_height() // 2 + thanks_text.get_height()*3))

				# restart if return is pressed
				keys_pressed = pygame.key.get_pressed()
				if keys_pressed[pygame.K_RETURN]:
					pygame.time.delay(500)
					fscreen.fill(BLACK)
					# if user wants to end gain, quit
					if end_game():
						pygame.event.post(pygame.event.Event(pygame.QUIT))
					# otherwise, restart
					else:
						pygame.time.delay(500)
						main()
				

		# update real screen
		update_real_screen()
			
		# update display at the end of each iteration
		pygame.display.update()


def display_dialogue(dialogue, dialogue_box):
	BARK_SOUND.play()
	enter_pressed = False
	while not enter_pressed:
		pygame.draw.rect(fscreen, WHITE, dialogue_box[0])
		pygame.draw.rect(fscreen, BLACK, dialogue_box[1])
		fscreen.blit(dialogue, (DIALOGUE_BOX_X + 10, DIALOGUE_BOX_Y + 10))
		fscreen.blit(dialogue_box[2], (DIALOGUE_BOX_X + dialogue_box[1].width - dialogue_box[2].get_width(), 
			DIALOGUE_BOX_Y + dialogue_box[1].height - dialogue_box[2].get_height()))
		update_real_screen()
		pygame.display.update()

		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				run = False
				pygame.quit()
				sys.exit()

			if event.type == pygame.VIDEORESIZE:
				screen = pygame.display.set_mode(event.size, pygame.RESIZABLE)

			elif event.type == pygame.KEYDOWN:
				if event.key == pygame.K_RETURN:
					enter_pressed = True


def draw_start_sign(sign_y, sign_text):
	# scroll strawberry background
	global strawberrywall_scroll, strawberrywall_iterations
	strawberrywall_scroll += 1
	if strawberrywall_scroll == HEIGHT:
		strawberrywall_scroll = 0
		strawberrywall_iterations += 1

	for i in range(strawberrywall_iterations):
		fscreen.blit(STRAWBERRY_WALL, (0, (i * HEIGHT) - strawberrywall_scroll))

	# draw sign with text
	fscreen.blit(START_SIGN, ((WIDTH - (WIDTH * 0.85)) // 2, sign_y))
	fscreen.blit(sign_text[0], (((WIDTH - (WIDTH * 0.85)) // 2) + 162.5, sign_y + 50))
	fscreen.blit(sign_text[1], (((WIDTH - (WIDTH * 0.85)) // 2) + 120, sign_y + 100))
	fscreen.blit(sign_text[2], (((WIDTH - (WIDTH * 0.85)) // 2) + 120, sign_y + 125))
	fscreen.blit(sign_text[3], (((WIDTH - (WIDTH * 0.85)) // 2) + 122.5, sign_y + 200))
	fscreen.blit(sign_text[4], (((WIDTH - (WIDTH * 0.85)) // 2) + 160, sign_y + 225))


def update_real_screen():
	screen.blit(pygame.transform.scale(fscreen, screen.get_rect().size), (0, 0))

def end_game():
	# reset player
	hero_movement.relx = hero_movement.x
	hero_movement.dead = False
	#run end screen until user input
	end_screen = True
	play_again = True

	end_box = pygame.Rect(100, 100, WIDTH - 200, HEIGHT - 200)
	yes_underline = pygame.Rect(200, 225, 45, 5)
	no_underline = pygame.Rect(end_box.width - 75 + 35, 225, 30, 5)

	while end_screen:
		# events
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				end_screen = False
				pygame.quit()
				sys.exit()

		
		pygame.draw.rect(fscreen, BLACK, end_box)
		play_again_text = PLAY_AGAIN_FONT.render("Do you want to play again?", True, WHITE)
		yes_text = PLAY_AGAIN_FONT.render("Yes", True, WHITE)
		no_text = PLAY_AGAIN_FONT.render("No", True, WHITE)
		fscreen.blit(play_again_text, (125, 125))
		fscreen.blit(yes_text, (200, 195))
		fscreen.blit(no_text, (end_box.width - 75 + 37, 195))

		# should underline yes at first
		pygame.draw.rect(fscreen, WHITE, yes_underline)

		# check for keypressed
		keys_pressed = pygame.key.get_pressed()

		if keys_pressed[pygame.K_LEFT]:
			play_again = True
		if keys_pressed[pygame.K_RIGHT]:
			play_again = False
		if keys_pressed[pygame.K_RETURN]:
			# if user wants to play again return to game
			if not play_again:
				return True
			else:
				return False

		# check if yes or no is checked, and place underline
		if not play_again:
			pygame.draw.rect(fscreen, WHITE, no_underline)
			pygame.draw.rect(fscreen, BLACK, yes_underline)
		else:
			pygame.draw.rect(fscreen, WHITE, yes_underline)
			pygame.draw.rect(fscreen, BLACK, no_underline)
		
		screen.blit(pygame.transform.scale(fscreen, screen.get_rect().size), (0, 0))

		pygame.display.update()


# draw onto fake screen, then blit upscaled fake screen onto screen
def draw_window(hero_sprite, hero_walk_ani, objects_list, strawberry, spike, hero_hitbox):
	# draw background
	update_bg(hero_hitbox)

	# draw hero
	# pygame.draw.rect(fscreen, BLUE, hero)
	hero_state(hero_sprite, hero_walk_ani)

	# display objects
	for each_object in objects_list:
		hit_box = each_object.make_rect()
		if each_object.type == "strawberry":
			fscreen.blit(strawberry, (hit_box.x, hit_box.y))
		elif each_object.type == "spike":
			fscreen.blit(spike, (hit_box.x, hit_box.y))


def draw_stat_bar(collected, health_bar, health_bar_outline):
	# display stats
	#pygame.draw.rect(fscreen, BLACK, health_bar_outline)
	pygame.draw.rect(fscreen, GREEN, health_bar[0])
	pygame.draw.rect(fscreen, RED, health_bar[1])
	collected_text = COLLECTED_FONT.render("Collected: " + str(collected) + f"/{COLLECT_TO_WIN}", 1, BLACK)
	fscreen.blit(pygame.transform.scale(STRAWBERRY_SPRITE,(OBJECT_WIDTH // 2, OBJECT_HEIGHT // 2)), 
		(10, 20 + HEALTH_BAR_HEIGHT))
	fscreen.blit(collected_text, (30, 20 + HEALTH_BAR_HEIGHT))	
	

def handle_objects(hit_box, objects_list):
	# if object hits player, post event and remove object
	for each_object in objects_list:
		obj_hit_box = each_object.make_rect()
		if hit_box.colliderect(obj_hit_box):
			if each_object.type == "strawberry":
				pygame.event.post(pygame.event.Event(STRAWBERRY_HIT))
			elif each_object.type == "spike":
				pygame.event.post(pygame.event.Event(SPIKE_HIT))
			objects_list.remove(each_object)


# randomly generate object, scroll on screen, add events
def generate_object(objects_list):
	# only generate once in a while
	position = random.randint(HEIGHT - int(GROUND_RATIO * HEIGHT) + HERO_HEIGHT + 10, HEIGHT - OBJECT_HEIGHT)
	chance = random.randint(0, 100)
	if chance < STRAWBERRY_SPAWN_RATE:
		# generate strawberry
		strawberry = Object(WIDTH, position , OBJECT_WIDTH, OBJECT_HEIGHT, "strawberry")
		objects_list.append(strawberry)


	elif chance >= STRAWBERRY_SPAWN_RATE:
		# generate spike
		spike = Object(WIDTH, position , OBJECT_WIDTH, OBJECT_HEIGHT, "spike")
		objects_list.append(spike)


def get_sprites():
	# get sprites
	hero_sprite_right = get_hero_sprite(HERO_SPRITESHEET, 0, HERO_WIDTH, HERO_HEIGHT, HERO_SCALE , RED)
	hero_sprite_left = get_hero_sprite_flipped(HERO_SPRITESHEET, 0, HERO_WIDTH, HERO_HEIGHT, HERO_SCALE, RED)
	hero_death = get_obj_sprite(HERO_SPRITESHEET, 9, 16, 16, HERO_SCALE , RED, 16)
	hero_sprite = [hero_sprite_right, hero_sprite_left, hero_death]
	walk_right = []
	walk_left = []
	for frame in WALK_FRAMES:
		walk_right.append(get_hero_sprite(HERO_SPRITESHEET, frame, HERO_WIDTH, HERO_HEIGHT, HERO_SCALE, RED))
	for frame in WALK_FRAMES:
		walk_left.append(get_hero_sprite_flipped(HERO_SPRITESHEET, frame, HERO_WIDTH, HERO_HEIGHT, HERO_SCALE, RED))
	hero_walk_ani = [walk_right, walk_left]
	
	return hero_sprite, hero_walk_ani

def get_dog_sprites():
	# get still sprites
	dog_still = get_obj_sprite(DOG_SPRITESHEET, 0, 16, 16, HERO_SCALE // 2, RED, CANVAS_SIZE_LENGTH)
	dog_still_basket = get_obj_sprite(DOG_SPRITESHEET, 1, 16, 16, HERO_SCALE // 2, RED, CANVAS_SIZE_LENGTH)
	dog_still_list = [dog_still, dog_still_basket]
	dog_walk_r = []
	for i in range(2, 6):
		dog_walk_r.append(get_obj_sprite(DOG_SPRITESHEET, i, 16, 16, HERO_SCALE // 2, RED, CANVAS_SIZE_LENGTH))
	dog_walk_l = []
	for i in range(6, 10):
		dog_walk_l.append(get_obj_sprite(DOG_SPRITESHEET, i, 16, 16, HERO_SCALE // 2, RED, CANVAS_SIZE_LENGTH))

	return dog_still_list, dog_walk_r, dog_walk_l



def hero_events(keys_pressed, objects_list, final_x):
	global background_scroll
	# check for no buttons pressed
	event_list = pygame.event.get()
	if len(event_list) == 0:
		hero_movement.moving = False
		hero_movement.up = False
		hero_movement.down = False
		hero_movement.movingright = False
		hero_movement.movingleft = False

	# check for border
	if keys_pressed[pygame.K_LEFT] and not hero_movement.relx <= 0: #LEFT
		hero_movement.left = True
		hero_movement.right = False
		hero_movement.moving = True
		background_scroll -= 1

		hero_movement.relx -= 1.5

		for object in objects_list:
			object.x += VEL

		hero_movement.movingleft = True
		hero_movement.movingright = False
		if keys_pressed[pygame.K_RIGHT]:
			hero_movement.movingleft = False


	if keys_pressed[pygame.K_RIGHT] and not hero_movement.relx >= final_x: #RIGHT
		hero_movement.left = False
		hero_movement.right = True
		hero_movement.moving = True
		background_scroll += 1

		hero_movement.relx += 1.5

		for object in objects_list:
			object.x -= VEL

		hero_movement.movingright = True
		hero_movement.movingleft = False

		# if pressing left and right, dont count ticks
		if keys_pressed[pygame.K_LEFT]:
			hero_movement.movingright = False
	

	if keys_pressed[pygame.K_UP]: #UP 
		hero_movement.moving = True
		hero_movement.up = True
		hero_movement.down = False

		# if up or down in pressed , but not right, do not count ticks
		if not (keys_pressed[pygame.K_RIGHT]):
			hero_movement.movingright = False

		if not (keys_pressed[pygame.K_LEFT]):
			hero_movement.movingleft = False

	if keys_pressed[pygame.K_DOWN]: #DOWN
		hero_movement.moving = True
		hero_movement.up = False
		hero_movement.down = True

		# if up or down in pressed , but not right, do not count ticks
		if not (keys_pressed[pygame.K_RIGHT]):
			hero_movement.movingright = False
		if not (keys_pressed[pygame.K_LEFT]):
			hero_movement.movingleft = False


# move background relative to user position
def update_bg(hero_hitbox):
	global background_scroll

	border = pygame.Rect(0, 0, hero_movement.x - hero_movement.relx, HEIGHT)

	# background moves slower than foreground
	for i in range(50):
		scroll = 1
		for bg in BG_IMAGES:
			fscreen.blit(bg, ((i * WIDTH) - background_scroll * scroll, 0))
			scroll += 0.5

	# draw in border
	pygame.draw.rect(fscreen, BLACK, border)


def hero_state(hero_sprite, hero_walk_ani):
	if not hero_movement.dead:
		# check walk count
		if hero_movement.walkCount + 10 >= (len(hero_walk_ani[0]) * 5):
				hero_movement.walkCount = 0

		# print sprite in rectangle (check for)
		if hero_movement.up:
			if hero_movement.y > HEIGHT - (HEIGHT * GROUND_RATIO):
				hero_movement.y -= VEL
		if hero_movement.down:
			# check if at bound
			if hero_movement.y + (HERO_HEIGHT*HERO_SCALE) < HEIGHT:
				hero_movement.y += VEL

		if hero_movement.right:
			if hero_movement.moving:
				hero_movement.walkCount += 1
				fscreen.blit(hero_walk_ani[0][hero_movement.walkCount // 5], (hero_movement.x, hero_movement.y))

			else:
				fscreen.blit(hero_sprite[0], (hero_movement.x, hero_movement.y))
		if hero_movement.left:
			if hero_movement.moving:
				hero_movement.walkCount += 1
				fscreen.blit(hero_walk_ani[1][hero_movement.walkCount // 5], (hero_movement.x, hero_movement.y))
			else:
				fscreen.blit(hero_sprite[1], (hero_movement.x, hero_movement.y))

	else:
		fscreen.blit(hero_sprite[2], (hero_movement.x, hero_movement.y))


def get_hero_sprite_flipped(sheet, frame, width, height, scale, bgcolor):
	# initalize image
	image = pygame.Surface((width, height)).convert_alpha()
	# put frame from sprite sheet on image
	image.blit(sheet, (0,0), 
		((frame * CANVAS_SIZE_LENGTH) + HERO_SPRITE_LEFT_WHITESPACE, HERO_SPRITE_TOP_WHITESPACE, width, height))
	image = pygame.transform.flip(pygame.transform.scale(image, (width * scale, height * scale)), True, False)
	image.set_colorkey(bgcolor)

	return image

def get_hero_sprite(sheet, frame, width, height, scale, bgcolor):
	# initalize image
	image = pygame.Surface((width, height)).convert_alpha()
	# put frame from sprite sheet on image
	image.blit(sheet, (0,0), 
		((frame * CANVAS_SIZE_LENGTH) + HERO_SPRITE_LEFT_WHITESPACE, HERO_SPRITE_TOP_WHITESPACE, width, height))
	image = pygame.transform.scale(image, (width * scale, height * scale))
	image.set_colorkey(bgcolor)

	return image


def get_obj_sprite(sheet, frame, width, height, scale, bgcolor, canvas_size):
	# initalize image
	image = pygame.Surface((width, height)).convert_alpha()
	# put frame from sprite sheet on image
	image.blit(sheet, (0,0), ((frame * (canvas_size)), 0, width, height))
	image = pygame.transform.scale(image, (width * scale, height * scale))
	image.set_colorkey(bgcolor)

	return image


if __name__ == "__main__":
	main()