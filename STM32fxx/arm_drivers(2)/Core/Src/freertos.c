/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * File Name          : freertos.c
  * Description        : Code for freertos applications
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2025 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  *
  ******************************************************************************
  */
/* USER CODE END Header */

/* Includes ------------------------------------------------------------------*/
#include "FreeRTOS.h"
#include "task.h"
#include "main.h"
#include "cmsis_os.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
#include "tim.h"
#include "stm32f1xx_it.h"
#include "usart.h"
#include "enc28j60.h"
#include "spi.h"
#include <string.h>
/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */
extern QueueHandle_t statusQueue;
extern uint8_t mymac[];
extern uint8_t myip[];
extern uint8_t destip[];
/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */
#define TRIG_PIN_1 GPIO_PIN_0
#define TRIG_PORT_1 GPIOB
#define TRIG_PIN_2 GPIO_PIN_1
#define TRIG_PORT_2 GPIOB




uint8_t myip[] = {192, 168, 1, 10};
uint8_t destip[] = {192, 168, 1, 11};

/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/
/* USER CODE BEGIN Variables */
osThreadId task4Handle;
osThreadId task5Handle;

osThreadId task6Handle;
osThreadId task7Handle;
/* USER CODE END Variables */
osThreadId defaultTaskHandle;
osThreadId task1Handle;
osThreadId task2Handle;
osThreadId task3Handle;
osSemaphoreId ProximitySemaphoreHandle;

/* Private function prototypes -----------------------------------------------*/
/* USER CODE BEGIN FunctionPrototypes */
void UART1_Task(void const *argument);
void Motor_Task(void const *argument);
void makeSomeIpMessage(uint8_t *buffer, uint16_t service_id, uint16_t method_id,
		uint16_t client_id, uint16_t session_id, uint8_t msg_type,
		uint8_t *payload, uint16_t payload_len) ;

void EthernetTask(void const *argument);
void SomeIpTask(void const *argument);
/* USER CODE END FunctionPrototypes */

void StartDefaultTask(void const * argument);
void UltrasonicTask(void const * argument);
void ProcessDistance(void const * argument);
void ProximityAction(void const * argument);

void MX_FREERTOS_Init(void); /* (MISRA C 2004 rule 8.1) */

/* GetIdleTaskMemory prototype (linked to static allocation support) */
void vApplicationGetIdleTaskMemory( StaticTask_t **ppxIdleTaskTCBBuffer, StackType_t **ppxIdleTaskStackBuffer, uint32_t *pulIdleTaskStackSize );

/* USER CODE BEGIN GET_IDLE_TASK_MEMORY */
static StaticTask_t xIdleTaskTCBBuffer;
static StackType_t xIdleStack[configMINIMAL_STACK_SIZE];

void vApplicationGetIdleTaskMemory( StaticTask_t **ppxIdleTaskTCBBuffer, StackType_t **ppxIdleTaskStackBuffer, uint32_t *pulIdleTaskStackSize )
{
  *ppxIdleTaskTCBBuffer = &xIdleTaskTCBBuffer;
  *ppxIdleTaskStackBuffer = &xIdleStack[0];
  *pulIdleTaskStackSize = configMINIMAL_STACK_SIZE;
  /* place for user code */
}
/* USER CODE END GET_IDLE_TASK_MEMORY */

/**
  * @brief  FreeRTOS initialization
  * @param  None
  * @retval None
  */
void MX_FREERTOS_Init(void) {
  /* USER CODE BEGIN Init */

  /* USER CODE END Init */

  /* USER CODE BEGIN RTOS_MUTEX */
  /* add mutexes, ... */
  /* USER CODE END RTOS_MUTEX */

  /* Create the semaphores(s) */
  /* definition and creation of ProximitySemaphore */
  osSemaphoreDef(ProximitySemaphore);
  ProximitySemaphoreHandle = osSemaphoreCreate(osSemaphore(ProximitySemaphore), 1);

  /* USER CODE BEGIN RTOS_SEMAPHORES */
  /* add semaphores, ... */
  /* USER CODE END RTOS_SEMAPHORES */

  /* USER CODE BEGIN RTOS_TIMERS */
  /* start timers, add new ones, ... */
  /* USER CODE END RTOS_TIMERS */

  /* USER CODE BEGIN RTOS_QUEUES */
  /* add queues, ... */
  /* USER CODE END RTOS_QUEUES */

  /* Create the thread(s) */
  /* definition and creation of defaultTask */
  osThreadDef(defaultTask, StartDefaultTask, osPriorityNormal, 0, 128);
  defaultTaskHandle = osThreadCreate(osThread(defaultTask), NULL);

  /* definition and creation of task1 */
  osThreadDef(task1, UltrasonicTask, osPriorityNormal, 0, 128);
  task1Handle = osThreadCreate(osThread(task1), NULL);

  /* definition and creation of task2 */
  osThreadDef(task2, ProcessDistance, osPriorityNormal, 0, 128);
  task2Handle = osThreadCreate(osThread(task2), NULL);

  /* definition and creation of task3 */
  osThreadDef(task3, ProximityAction, osPriorityNormal, 0, 128);
  task3Handle = osThreadCreate(osThread(task3), NULL);

  /* USER CODE BEGIN RTOS_THREADS */
	osThreadDef(task4, UART1_Task, osPriorityNormal, 0, 128);
	osThreadCreate(osThread(task4), NULL);

	osThreadDef(task5, Motor_Task, osPriorityNormal, 0, 128);
	osThreadCreate(osThread(task5), NULL);

	osThreadDef(task6, EthernetTask, osPriorityNormal, 0, 128);
	osThreadCreate(osThread(task6), NULL);
	osThreadDef(task7, SomeIpTask, osPriorityNormal, 0, 128);
	osThreadCreate(osThread(task7), NULL);
  /* add threads, ... */
  /* USER CODE END RTOS_THREADS */

}

/* USER CODE BEGIN Header_StartDefaultTask */
/**
  * @brief  Function implementing the defaultTask thread.
  * @param  argument: Not used
  * @retval None
  */
/* USER CODE END Header_StartDefaultTask */
void StartDefaultTask(void const * argument)
{
  /* USER CODE BEGIN StartDefaultTask */
  /* Infinite loop */
  for(;;)
  {
    osDelay(1);
  }
  /* USER CODE END StartDefaultTask */
}

/* USER CODE BEGIN Header_UltrasonicTask */
/**
* @brief Function implementing the task1 thread.
* @param argument: Not used
* @retval None
*/
/* USER CODE END Header_UltrasonicTask */
void UltrasonicTask(void const * argument)
{
  /* USER CODE BEGIN UltrasonicTask */
  /* Infinite loop */
  for(;;)
  {
	  HAL_GPIO_WritePin(TRIG_PORT_1, TRIG_PIN_1, GPIO_PIN_SET);  // pull the TRIG pin HIGH
	  HAL_Delay(1);  // wait for 10 us
	  HAL_GPIO_WritePin(TRIG_PORT_1, TRIG_PIN_1, GPIO_PIN_RESET);  // pull the TRIG pin low

	  __HAL_TIM_ENABLE_IT(&htim3, TIM_IT_CC1);
	  osDelay(50);

	  HAL_GPIO_WritePin(TRIG_PORT_2, TRIG_PIN_2, GPIO_PIN_SET);  // pull the TRIG pin HIGH
	  HAL_Delay(1);  // wait for 10 us
	  HAL_GPIO_WritePin(TRIG_PORT_2, TRIG_PIN_2, GPIO_PIN_RESET);  // pull the TRIG pin low

	  __HAL_TIM_ENABLE_IT(&htim3, TIM_IT_CC2);
	  osDelay(50);
  }
  /* USER CODE END UltrasonicTask */
}

/* USER CODE BEGIN Header_ProcessDistance */
/**
* @brief Function implementing the task2 thread.
* @param argument: Not used
* @retval None
*/
/* USER CODE END Header_ProcessDistance */
void ProcessDistance(void const * argument)
{
  /* USER CODE BEGIN ProcessDistance */
  /* Infinite loop */
  for(;;)
  {
	  /*if(Distance_1<15){
		  HAL_GPIO_WritePin(GPIOB, GPIO_PIN_10, GPIO_PIN_SET);
	  }
	  else{
		  HAL_GPIO_WritePin(GPIOB, GPIO_PIN_10, GPIO_PIN_RESET);
	  }*/

	  if(Distance_2<15){
		  HAL_GPIO_WritePin(GPIOB, GPIO_PIN_11, GPIO_PIN_SET);
	  }
	  else{
		  HAL_GPIO_WritePin(GPIOB, GPIO_PIN_11, GPIO_PIN_RESET);
	  }
	  osDelay(1);
  }
  /* USER CODE END ProcessDistance */
}

/* USER CODE BEGIN Header_ProximityAction */
/**
* @brief Function implementing the task3 thread.
* @param argument: Not used
* @retval None
*/
/* USER CODE END Header_ProximityAction */
void ProximityAction(void const * argument)
{
  /* USER CODE BEGIN ProximityAction */
  /* Infinite loop */
  for(;;)
  {
	  if (xSemaphoreTake(ProximitySemaphoreHandle, portMAX_DELAY) == pdTRUE) {
	  HAL_GPIO_TogglePin(GPIOB, GPIO_PIN_10);

	  }

  }
  /* USER CODE END ProximityAction */
}

/* Private application code --------------------------------------------------*/
/* USER CODE BEGIN Application */
void UART1_Task(void const *argument) {

    while (1) {
        if (dataReady) {

            uint8_t calculated_crc = crc8(&rxBuffer[0], 1);
            if (calculated_crc == rxBuffer[1]) {
                xQueueSend(motorQueue, &rxBuffer[0], portMAX_DELAY);
            }
            dataReady = 0;
        }
        vTaskDelay(pdMS_TO_TICKS(10));
    }
}

void Motor_Task(void const *argument) {
	char received_char;
    uint16_t speed = 50;
while (1) {
	if (xQueueReceive(motorQueue, &received_char, portMAX_DELAY) == pdTRUE) {
		switch (received_char) {
		case 'f': // Forward
			Motor1_Forward(speed);
			Motor2_Forward(speed);
			break;
		case 'b': // Backward
			Motor1_Backward(speed);
			Motor2_Backward(speed);
			break;
		case 'l': // Left
			Motor_Turn(speed, TURN_LEFT);
			break;
		case 'r': // Right
			Motor_Turn(speed, TURN_RIGHT);
			break;
		default:
			Motor1_Stop();
			Motor2_Stop();
			break;
		}
	}
}
}

void makeSomeIpMessage(uint8_t *buffer, uint16_t service_id, uint16_t method_id,
		uint16_t client_id, uint16_t session_id, uint8_t msg_type,
		uint8_t *payload, uint16_t payload_len) {
	uint32_t length = 8 + payload_len; // طول الـ header (8 bytes) + الـ payload

	// SOME/IP Header
	buffer[0] = (service_id >> 8) & 0xFF;   // Service ID (High byte)
	buffer[1] = service_id & 0xFF;          // Service ID (Low byte)
	buffer[2] = (method_id >> 8) & 0xFF;    // Method ID (High byte)
	buffer[3] = method_id & 0xFF;           // Method ID (Low byte)
	buffer[4] = (length >> 24) & 0xFF;      // Length (4 bytes)
	buffer[5] = (length >> 16) & 0xFF;
	buffer[6] = (length >> 8) & 0xFF;
	buffer[7] = length & 0xFF;
	buffer[8] = (client_id >> 8) & 0xFF;    // Client ID (High byte)
	buffer[9] = client_id & 0xFF;           // Client ID (Low byte)
	buffer[10] = (session_id >> 8) & 0xFF;  // Session ID (High byte)
	buffer[11] = session_id & 0xFF;         // Session ID (Low byte)
	buffer[12] = 0x01;                      // Protocol Version
	buffer[13] = 0x01;                      // Interface Version
	buffer[14] = msg_type;                  // Message Type (0x00 = Request)
	buffer[15] = 0x00;                      // Return Code (0x00 = OK)

	// Payload
	if (payload && payload_len > 0) {
		memcpy(buffer + 16, payload, payload_len);
	}
}

// Task للتعامل مع الـ Ethernet
void EthernetTask(void const *argument) {
	enc28j60Init(mymac);
	enc28j60clkout(2);
	enc28j60PhyWrite(PHCON2, 0x200);
	enc28j60SetIP(myip);

	while (1) {
		if (enc28j60linkup()) {
			//Ethernet connected!
			xQueueSend(statusQueue, "CONNECTED", portMAX_DELAY);
		} else {
			//Ethernet disconnected!
			xQueueSend(statusQueue, "DISCONNECTED", portMAX_DELAY);
		}
		vTaskDelay(pdMS_TO_TICKS(1000)); // تحقق كل ثانية
	}
}

// Task لإرسال رسائل SOME/IP
void SomeIpTask(void const *argument) {
	char status[12];
	uint8_t payload[] = { 0xDE, 0xAD, 0xBE, 0xEF }; // Payload
	uint16_t payload_len = sizeof(payload);
	uint8_t someip_buffer[32]; // Buffer كافي للـ header (16) + payload (4)

	while (1) {
		if (xQueueReceive(statusQueue, status, portMAX_DELAY) == pdTRUE) {
			if (strcmp(status, "CONNECTED") == 0) {
				//  make SOME/IP message
				makeSomeIpMessage(someip_buffer, 0x1234,       // Service ID
						0x5678,       // Method ID
						0x0001,       // Client ID
						0x0001,       // Session ID
						0x00,         // Message Type (Request)
						payload,      // Payload
						payload_len);

				// إرسال الرسالة عبر UDP إلى الـ Raspberry Pi
				enc28j60PacketSendUDP(destip, 30490, 12345, someip_buffer,
						16 + payload_len);
				//SOME/IP message sent to Raspberry Pi!
			}
		}
		vTaskDelay(pdMS_TO_TICKS(5000));
	}
}

/* USER CODE END Application */

