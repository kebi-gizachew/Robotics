#!/usr/bin/env python3
"""Drive forward until an obstacle is too close, then turn away from it."""

import rclpy
from geometry_msgs.msg import Twist
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.parameter import Parameter
from std_srvs.srv import SetBool

from lab_interfaces.msg import ObstacleInfo
from my_robot_interfaces.msg import RobotStatus
from my_robot_interfaces.srv import SetTurnSpeed


class TurnAway(Node):

    def __init__(self):
        super().__init__("turn_away")
        self.declare_parameter("forward_speed", 0.2)
        self.declare_parameter("turn_speed", 0.5)
        self.declare_parameter("max_turn_speed", 1.5)

        self.enabled = False
        self.last_obstacle_distance = 0.0

        self.cmd_vel = self.create_publisher(Twist, "cmd_vel", 10)
        self.status_pub = self.create_publisher(RobotStatus, "/robot_status", 10)
        self.create_subscription(ObstacleInfo, "obstacle", self.on_obstacle, 10)
        self.create_service(SetBool, "/turn_away_enable", self.on_enable)
        self.create_service(SetTurnSpeed, "/set_turn_speed", self.on_set_turn_speed)

    def publish_status(self, state):
        status = RobotStatus()
        status.state = state
        status.obstacle_distance = self.last_obstacle_distance
        self.status_pub.publish(status)

    def on_enable(self, request, response):
        if request.data:
            self.enabled = True
            response.success = True
            response.message = "enabled"
        else:
            if self.enabled:
                self.cmd_vel.publish(Twist())
            self.enabled = False
            self.publish_status("stopped")
            response.success = True
            response.message = "stopped"
        self.get_logger().info(response.message)
        return response

    def on_set_turn_speed(self, request, response):
        max_turn_speed = self.get_parameter("max_turn_speed").value
        if request.turn_speed <= 0.0:
            response.success = False
            response.message = "turn_speed must be greater than 0"
        elif request.turn_speed > max_turn_speed:
            response.success = False
            response.message = (
                f"turn_speed must be at most {max_turn_speed}"
            )
        else:
            self.set_parameters([
                Parameter("turn_speed", value=float(request.turn_speed)),
            ])
            response.success = True
            response.message = f"turn_speed set to {request.turn_speed:.2f}"
        self.get_logger().info(response.message)
        return response

    def on_obstacle(self, msg):
        self.last_obstacle_distance = msg.distance
        if not self.enabled:
            self.publish_status("stopped")
            return

        forward_speed = self.get_parameter("forward_speed").value
        turn_speed = self.get_parameter("turn_speed").value

        twist = Twist()
        if not msg.too_close:
            twist.linear.x = forward_speed
            twist.angular.z = 0.0
            state = "forward"
        else:
            twist.linear.x = 0.0
            # angle > 0 means the obstacle is to the left, so turn right
            twist.angular.z = -turn_speed if msg.angle > 0.0 else turn_speed
            state = "turning"
        self.cmd_vel.publish(twist)
        self.publish_status(state)


def main():
    rclpy.init()
    node = TurnAway()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    node.destroy_node()
    rclpy.try_shutdown()


if __name__ == "__main__":
    main()
