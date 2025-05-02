#ifndef BOOTLOADER_H
#define BOOTLOADER_H

/**************************** Include Section *****************************/
#include <stdint.h>
#include "main.h"

/**************************** Define Section *****************************/


#define PAYLOAD_LEN 	6u
#define PAYLOAD			7u

// Resgister Adderess
#define CHIP_ID   *(( volatile uint32_t*) 0xE0042000)
#define RDP		  *((volatile uint32_t*) 0x1FFFF800)


// Macros  for get the  Varaible Value in Flash Erase
#define PAGENUM					2u
#define NUMPAGES					3U

//___________________________ Pages Config _________________________//
#define NUM_OF_PAGES					127
#define PAGE_SIZE							0x00000400    // 1K Byte
#define PAGE _END							0x000003FF
#define PAGE_BASE_ADDR				0x08000000
#define MASS_ERASE_CMD				0xFF

//____________________________ Reply______________________________//

// Get version reply
#define BL_VERSION_LEN				 1u
#define BL_VERSION                        1


//_______________________ Acknowladge Code_________________________//

#define BL_ACK                             0xA5
#define BL_NACK                           0x7F

//_______________________ Command Code ___________________________//

#define COMMAND_BL_GET_VER                				0x51
#define COMMAND_BL_GET_HELP               			 0x52
#define COMMAND_BL_GET_CID                				 0x53
#define COMMAND_BL_GET_RDP_STATUS         		 0x54
#define COMMAND_BL_GO_TO_ADDR             			 0x55
#define COMMAND_BL_FLASH_ERASE            			 0x56
#define COMMAND_BL_MEM_WRITE             			 0x57
#define COMMAND_BL_Jump_To_User_App				 0x5D

//______________ Future Command _________________//
#define COMMAND_BL_EN_R_W_PROTECT         		 0x58
#define COMMAND_BL_MEM_READ             			     0x59
#define COMMAND_BL_READ_SECTOR_P_STATUS    0x5A
#define COMMAND_BL_OTP_READ               		     0x5B
#define COMMAND_BL_DIS_R_W_PROTECT              0x5C


/*************************** Function Declaration **************************/
void BL_VoidHandleGetVerCmd(uint8_t *Copy_u8buffer);

void BL_VoidHandleGetHelpCmd(uint8_t *Copy_u8buffer);

void BL_VoidHandleGetCIDCmd(uint8_t *Copy_u8buffer);

void BL_VoidHandleGetRDPStatusCmd(uint8_t *Copy_u8buffer);

void BL_VoidHandleGoToAddrCmd(uint8_t *Copy_u8buffer);

void BL_VoidHandleFlashEraseCmd(uint8_t *Copy_u8buffer);

void BL_VoidHandleMemWriteCmd(uint8_t *Copy_u8buffer);

void BL_VoidJumpToUserApp(uint8_t *Copy_u8buffer);

void BL_VoidHandleEnRWProtectCmd(uint8_t *Copy_u8buffer);

void BL_VoidHandleMemReadCmd(uint8_t *Copy_u8buffer);

void BL_VoidHandleReadSectorPStatusCmd(uint8_t *Copy_u8buffer);

void BL_VoidHandleOTPRreadCmd(uint8_t *Copy_u8buffer);

void BL_VoidHandleDisRWProtectCmd(uint8_t *Copy_u8buffer);


#endif

