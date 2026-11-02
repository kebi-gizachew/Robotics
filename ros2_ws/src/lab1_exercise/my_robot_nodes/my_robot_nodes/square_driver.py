#!/usr/bin/env python3
"""Drive a square by sending DriveDistance and Rotate goals one after another."""

from action_msgs.msg import GoalStatus
import rclpy
from rclpy.action import ActionClient
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node

from lab_interfaces.action import DriveDistance
from my_robot_interfaces.action import Rotate

SIDES = 4
TURN_ANGLE = 1.57


class SquareDriver(Node):

    def __init__(self):
        super().__init__("square_driver")
        self.declare_parameter("side_length", 0.5)

        self.drive_client = ActionClient(self, DriveDistance, "/drive_distance")
        self.rotate_client = ActionClient(self, Rotate, "/rotate")

        self.side = 1
        self.start_timer = self.create_timer(0.5, self.try_start)

    def try_start(self):
        if not self.drive_client.server_is_ready():
            self.get_logger().info("Waiting for /drive_distance")
            return
        if not self.rotate_client.server_is_ready():
            self.get_logger().info("Waiting for /rotate")
            return
        self.start_timer.cancel()
        side_length = self.get_parameter("side_length").value
        self.get_logger().info(
            f"Starting square, side_length={side_length:.2f} m"
        )
        self.send_drive()

    def fail(self, action_name):
        self.get_logger().error(
            f"{action_name} failed on side {self.side}, stopping square"
        )

    def send_drive(self):
        goal = DriveDistance.Goal()
        goal.distance = float(self.get_parameter("side_length").value)
        self.get_logger().info(
            f"Side {self.side}: sending DriveDistance {goal.distance:.2f} m"
        )
        future = self.drive_client.send_goal_async(goal)
        future.add_done_callback(self.on_drive_response)

    def on_drive_response(self, future):
        goal_handle = future.result()
        if goal_handle is None or not goal_handle.accepted:
            self.fail("DriveDistance")
            return
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self.on_drive_result)

    def on_drive_result(self, future):
        response = future.result()
        if (
            response is None
            or response.status != GoalStatus.STATUS_SUCCEEDED
            or not response.result.reached
        ):
            self.fail("DriveDistance")
            return
        self.get_logger().info(
            f"Side {self.side}: DriveDistance done, "
            f"travelled {response.result.travelled:.2f} m"
        )
        self.send_rotate()

    def send_rotate(self):
        goal = Rotate.Goal()
        goal.angle = TURN_ANGLE
        self.get_logger().info(
            f"Side {self.side}: sending Rotate {goal.angle:.2f} rad"
        )
        future = self.rotate_client.send_goal_async(goal)
        future.add_done_callback(self.on_rotate_response)

    def on_rotate_response(self, future):
        goal_handle = future.result()
        if goal_handle is None or not goal_handle.accepted:
            self.fail("Rotate")
            return
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self.on_rotate_result)

    def on_rotate_result(self, future):
        response = future.result()
        if response is None or response.status != GoalStatus.STATUS_SUCCEEDED:
            self.fail("Rotate")
            return
        self.get_logger().info(
            f"Side {self.side}: Rotate done, turned {response.result.turned:.2f} rad"
        )
        if self.side >= SIDES:
            self.get_logger().info("Square complete")
            return
        self.side += 1
        self.send_drive()


def main():
    rclpy.init()
    node = SquareDriver()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    node.destroy_node()
    rclpy.try_shutdown()


if __name__ == "__main__":
    main()
