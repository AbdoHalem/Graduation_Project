#ifndef _BOOTLOADER_PRIVATE_H
#define _BOOTLOADER_PRIVATE_H

/****************************** Include Section ****************************/
#include <stdint.h>

/****************************** Define Section *****************************/
#define CRC_VERIFIED     0u
#define CRC_NOT_VERIFIED 1u


#define SYSMEM_BASE  0x1FFFF000
#define SYSMEM_END   0x1FFFF7FF


#define SRAM_SIZE 	  (64*1024)


/***************************** User Define Section **************************/

typedef enum
{
	MEM_INVALID         = 0,
	MEM_FLASH_VALID = 1,
	MEM_SRAM_VALID  = 2,
	MEM_SYS_VALID     = 3

}MemoryValidation_Ret_t;

/*************************** Function Declaration *************************/
static uint8_t BL_u8VerifyCRC(uint8_t *Copy_u8Data , uint8_t Copy_u8Length , uint32_t Copy_u8HostCRC);
static void BL_VoidSendAck(uint8_t Copy_u8ReplyLength);
static void BL_VoidSendNack(void);
static HAL_StatusTypeDef BL_FLASHErase(uint8_t Copy_u8PageNum , uint8_t Copy_u8NumOfPage);
static HAL_StatusTypeDef BL_FLASHWrite(uint32_t Copy_u32StatingAdd , uint32_t * Copy_u16Payload , uint8_t Copy_u8PayLoadLen);





#endif
