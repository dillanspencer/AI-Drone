from djitellopy.tello import Tello
import cv2
import pygame
import numpy as np
import time
import sys

######################################################################
width = 640  # WIDTH OF THE IMAGE
height = 480  # HEIGHT OF THE IMAGE
deadZone = 100
######################################################################

# Speed of the drone
S = 30
# Frames per second of the pygame window display
FPS = 25

# Face height for distance
faceX = 405
faceY = 285
faceWidth = 100
faceHeight = 100

frameWidth = width
frameHeight = height

font = cv2.FONT_HERSHEY_SIMPLEX

# org
org = (50, 50)

# fontScale
fontScale = 1

# Blue color in BGR
color = (255, 0, 0)

# Line thickness of 2 px
thickness = 2

faceCascade = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")


# cap = cv2.VideoCapture(1)
# cap.set(3, frameWidth)
# cap.set(4, frameHeight)
# cap.set(10,200)

class FrontEnd(object):

    def __init__(self):
        # Init pygame
        pygame.init()

        # Create pygame window
        pygame.display.set_caption("Tello video stream")
        self.screen = pygame.display.set_mode([960, 720])

        # Init Tello object that interacts with the Tello drone
        self.tello = Tello()

        # Drone velocities between -100~100
        self.for_back_velocity = 0
        self.left_right_velocity = 0
        self.up_down_velocity = 0
        self.yaw_velocity = 0
        self.speed = 10

        self.send_rc_control = False

        # create update timer
        pygame.time.set_timer(pygame.USEREVENT + 1, 50)

    def run(self):

        if not self.tello.connect():
            print("Tello not connected")
            return

        if not self.tello.set_speed(self.speed):
            print("Not set speed to lowest possible")
            return

        # In case streaming is on. This happens when we quit this program without the escape key.
        if not self.tello.streamoff():
            print("Could not stop video stream")
            return

        if not self.tello.streamon():
            print("Could not start video stream")
            return

        frame_read = self.tello.get_frame_read()

        # TELLO EVENT REGION

        should_stop = False
        while not should_stop:

            for event in pygame.event.get():
                if event.type == pygame.USEREVENT + 1:
                    self.update()
                elif event.type == pygame.QUIT:
                    should_stop = True
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        should_stop = True
                    else:
                        self.keydown(event.key)
                elif event.type == pygame.KEYUP:
                    self.keyup(event.key)

            if frame_read.stopped:
                frame_read.stop()
                break

            self.updateOnFaces(frame_read)

            self.screen.fill([0, 0, 0])
            frame = cv2.cvtColor(frame_read.frame, cv2.COLOR_BGR2RGB)
            frame = np.rot90(frame)
            frame = np.flipud(frame)
            frame = pygame.surfarray.make_surface(frame)
            self.screen.blit(frame, (0, 0))

            # HAND TRACKING
            pygame.display.update()

            time.sleep(1 / FPS)

        # Call it always before finishing. To deallocate resources.
        self.tello.end()

    def updateOnFaces(self, frame_read):
        gray = cv2.cvtColor(frame_read.frame, cv2.COLOR_BGR2GRAY)

        faces = faceCascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30),
        )

        # Draw a rectangle around the faces
        index = 0
        for (x, y, w, h) in faces:
            if index != 0:
                return
            if x < 960 / 2:
                image = cv2.putText(frame_read.frame, 'LEFT', org, font,
                                    fontScale, color, thickness, cv2.LINE_AA)
                self.left_right_velocity = -S
            elif x > 960 / 2:
                image = cv2.putText(frame_read.frame, 'RIGHT', org, font,
                                    fontScale, color, thickness, cv2.LINE_AA)
                self.left_right_velocity = S
            if y > (720 / 2) - h:
                image = cv2.putText(frame_read.frame, 'DOWN', (900, 50), font,
                                    fontScale, color, thickness, cv2.LINE_AA)
                self.up_down_velocity = -S
            elif y < 720 / 2:
                image = cv2.putText(frame_read.frame, 'UP', (900, 50), font,
                                    fontScale, color, thickness, cv2.LINE_AA)
                self.up_down_velocity = S
            if (w * h) < faceWidth*faceHeight:
                image = cv2.putText(frame_read.frame, 'FORWARD', (50, 100), font,
                                    fontScale, color, thickness, cv2.LINE_AA)
                self.for_back_velocity = S
            elif (w * h) > faceWidth*faceHeight:
                image = cv2.putText(frame_read.frame, 'BACKWARD', (50, 100), font,
                                    fontScale, color, thickness, cv2.LINE_AA)
                self.for_back_velocity = -S
            cv2.rectangle(frame_read.frame, (faceX, faceY), (faceX+faceWidth, faceY+faceHeight), (0, 0, 255), 2)
            cv2.rectangle(frame_read.frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            index += 1

    def keydown(self, key):
        """ Update velocities based on key pressed
        Arguments:
            key: pygame key
        """
        if key == pygame.K_UP:  # set forward velocity
            self.for_back_velocity = S
        elif key == pygame.K_DOWN:  # set backward velocity
            self.for_back_velocity = -S
        elif key == pygame.K_LEFT:  # set left velocity
            self.left_right_velocity = -S
        elif key == pygame.K_RIGHT:  # set right velocity
            self.left_right_velocity = S
        elif key == pygame.K_w:  # set up velocity
            self.up_down_velocity = S
        elif key == pygame.K_s:  # set down velocity
            self.up_down_velocity = -S
        elif key == pygame.K_a:  # set yaw counter clockwise velocity
            self.yaw_velocity = -S
        elif key == pygame.K_d:  # set yaw clockwise velocity
            self.yaw_velocity = S

    def keyup(self, key):
        """ Update velocities based on key released
        Arguments:
            key: pygame key
        """
        keys = pygame.key.get_pressed()
        if key == pygame.K_UP or key == pygame.K_DOWN:  # set zero forward/backward velocity
            self.for_back_velocity = 0
        elif key == pygame.K_LEFT or key == pygame.K_RIGHT:  # set zero left/right velocity
            self.left_right_velocity = 0
        elif key == pygame.K_w or key == pygame.K_s:  # set zero up/down velocity
            self.up_down_velocity = 0
        elif key == pygame.K_a or key == pygame.K_d:  # set zero yaw velocity
            self.yaw_velocity = 0
        elif key == pygame.K_t:  # takeoff
            self.tello.takeoff()
            self.send_rc_control = True
        elif key == pygame.K_l:  # land
            self.tello.land()
            self.send_rc_control = False
        elif key == pygame.K_f:
            self.tello.flip_back()
        elif key == pygame.K_g:
            self.tello.flip_forward()
        elif key == pygame.K_h:
            self.tello.flip_right()
        elif key == pygame.K_j:
            self.tello.flip_left()

    def update(self):
        """ Update routine. Send velocities to Tello."""
        if self.send_rc_control:
            self.tello.send_rc_control(self.left_right_velocity, self.for_back_velocity, self.up_down_velocity,
                                       self.yaw_velocity)


def main():
    frontend = FrontEnd()

    # run frontend
    frontend.run()


if __name__ == '__main__':
    main()
