/*
 * motor_driver.c
 *
 *  Created on: Feb 3, 2025
 *      Author: A
 */

#include "motor_driver.h"
#include "main.h"

// Define GPIO pins for direction control
#define MOTOR1_DIR_PIN_1 GPIO_PIN_2
#define MOTOR1_DIR_PORT_1 GPIOA
#define MOTOR1_DIR_PIN_2 GPIO_PIN_3
#define MOTOR1_DIR_PORT_2 GPIOA

#define MOTOR2_DIR_PIN_1 GPIO_PIN_4        //PA4
#define MOTOR2_DIR_PORT_1 GPIOA
#define MOTOR2_DIR_PIN_2 GPIO_PIN_5       //PA5
#define MOTOR2_DIR_PORT_2 GPIOA

// Initialize the motor driver
void Motor_Init(void) {
	GPIO_InitTypeDef GPIO_InitStruct = {0}; // Local scope (reset for each motor)
	__HAL_RCC_GPIOA_CLK_ENABLE(); // Enable GPIOA clock

	 // Initialize Motor 1 Direction Pins (PA0 and PA1)
	GPIO_InitStruct.Pin = MOTOR1_DIR_PIN_1 | MOTOR1_DIR_PIN_2;
	GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP; // Push-pull output
	GPIO_InitStruct.Pull = GPIO_NOPULL;         // No pull-up/pull-down
	GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW; // Adjust speed
	HAL_GPIO_Init(MOTOR1_DIR_PORT_1, &GPIO_InitStruct);

	    // Motor 2 Direction Pins (PA2 and PA3)
	GPIO_InitStruct.Pin = MOTOR2_DIR_PIN_1 | MOTOR2_DIR_PIN_2;
	GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;    // Re-defined for clarity
	GPIO_InitStruct.Pull = GPIO_NOPULL;            // Re-defined for clarity
	GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;  // Re-defined for clarity
	HAL_GPIO_Init(MOTOR2_DIR_PORT_2, &GPIO_InitStruct);

    // Start the PWM timers for both channels
    HAL_TIM_PWM_Start(&htim2, TIM_CHANNEL_1);  // Motor 1
    HAL_TIM_PWM_Start(&htim2, TIM_CHANNEL_2);  // Motor 2

    // Set default direction (forward) for both motors
    HAL_GPIO_WritePin(MOTOR1_DIR_PORT_1, MOTOR1_DIR_PIN_1, GPIO_PIN_SET);
    HAL_GPIO_WritePin(MOTOR1_DIR_PORT_2, MOTOR1_DIR_PIN_2, GPIO_PIN_RESET);

    HAL_GPIO_WritePin(MOTOR2_DIR_PORT_1, MOTOR2_DIR_PIN_1, GPIO_PIN_SET);
    HAL_GPIO_WritePin(MOTOR2_DIR_PORT_2, MOTOR2_DIR_PIN_2, GPIO_PIN_RESET);
}

// Move Motor 1 forward at specified speed (0 to 100%)
void Motor1_Forward(uint16_t speed) {
    // Set direction pins for forward motion
    HAL_GPIO_WritePin(MOTOR1_DIR_PORT_1, MOTOR1_DIR_PIN_1, GPIO_PIN_SET);
    HAL_GPIO_WritePin(MOTOR1_DIR_PORT_2, MOTOR1_DIR_PIN_2, GPIO_PIN_RESET);

    // Set PWM duty cycle (speed)
    uint16_t pwm_value = (speed * htim2.Instance->ARR) / 100;  // Scale speed to PWM value
    __HAL_TIM_SET_COMPARE(&htim2, TIM_CHANNEL_1, pwm_value);
}

// Move Motor 1 backward at specified speed (0 to 100%)
void Motor1_Backward(uint16_t speed) {
    // Set direction pins for backward motion
    HAL_GPIO_WritePin(MOTOR1_DIR_PORT_1, MOTOR1_DIR_PIN_1, GPIO_PIN_RESET);
    HAL_GPIO_WritePin(MOTOR1_DIR_PORT_2, MOTOR1_DIR_PIN_2, GPIO_PIN_SET);

    // Set PWM duty cycle (speed)
    uint16_t pwm_value = (speed * htim2.Instance->ARR) / 100;  // Scale speed to PWM value
    __HAL_TIM_SET_COMPARE(&htim2, TIM_CHANNEL_1, pwm_value);
}

// Move Motor 2 forward at specified speed (0 to 100%)
void Motor2_Forward(uint16_t speed) {
    // Set direction pins for forward motion
    HAL_GPIO_WritePin(MOTOR2_DIR_PORT_1, MOTOR2_DIR_PIN_1, GPIO_PIN_SET);
    HAL_GPIO_WritePin(MOTOR2_DIR_PORT_2, MOTOR2_DIR_PIN_2, GPIO_PIN_RESET);

    // Set PWM duty cycle (speed)
    uint16_t pwm_value = (speed * htim2.Instance->ARR) / 100;  // Scale speed to PWM value
    __HAL_TIM_SET_COMPARE(&htim2, TIM_CHANNEL_2, pwm_value);
}

// Move Motor 2 backward at specified speed (0 to 100%)
void Motor2_Backward(uint16_t speed) {
    // Set direction pins for backward motion
    HAL_GPIO_WritePin(MOTOR2_DIR_PORT_1, MOTOR2_DIR_PIN_1, GPIO_PIN_RESET);
    HAL_GPIO_WritePin(MOTOR2_DIR_PORT_2, MOTOR2_DIR_PIN_2, GPIO_PIN_SET);

    // Set PWM duty cycle (speed)
    uint16_t pwm_value = (speed * htim2.Instance->ARR) / 100;  // Scale speed to PWM value
    __HAL_TIM_SET_COMPARE(&htim2, TIM_CHANNEL_2, pwm_value);
}

// Stop Motor 1
void Motor1_Stop(void) {
    __HAL_TIM_SET_COMPARE(&htim2, TIM_CHANNEL_1, 0);
}

// Stop Motor 2
void Motor2_Stop(void) {
    __HAL_TIM_SET_COMPARE(&htim2, TIM_CHANNEL_2, 0);
}

// Turn the car left or right by driving the motors in opposite directions
void Motor_Turn(uint16_t speed, uint8_t direction) {
    if (direction == TURN_LEFT) {
        // Motor 1 forward, Motor 2 backward (turn left)
        Motor1_Forward(speed);
        Motor2_Backward(speed);
    } else if (direction == TURN_RIGHT) {
        // Motor 1 backward, Motor 2 forward (turn right)
        Motor1_Backward(speed);
        Motor2_Forward(speed);
    }
}
