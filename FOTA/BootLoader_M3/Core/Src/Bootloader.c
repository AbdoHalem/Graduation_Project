/****************************** Include Section ******************************/
#include "Bootloader.h"
#include "Bootloader_Private.h"

/********************************* Variables *********************************/\


extern UART_HandleTypeDef huart1; // Handle UART

static uint32_t   Copy_u32AddrUserApp = 0x08002400 ;
static uint8_t Local_u8Counter = 0;

/********************** Private Function Implementation **********************/
/*static uint8_t BL_u8VerifyCRC(uint8_t *Copy_u8Data , uint8_t Copy_u8Length , uint32_t Copy_u8HostCRC)
{
    // Local variables
    uint32_t CRCValue = 0 ; 
    uint32_t CRC_Statues = CRC_NOT_VERIFIED;
    uint8_t CRC_TEMP ;
    
    // Calculate CRC value for the Data
    for(uint8_t i = 0 ; i < Copy_u8Length ; i++)
    {
        CRC_TEMP = Copy_u8Data[i];
        CRCValue = HAL_CRC_Accumulate(&hcrc, &CRC_TEMP , 1);
    }

    //Reset the Accumulator CRC
    __HAL_CRC_DR_RESET(&hcrc);

    // Check the CRC
    CRC_Statues = (CRCValue == Copy_u8HostCRC) ? CRC_VERIFIED : CRC_NOT_VERIFIED;

    return CRC_Statues;
}*/

static uint8_t BL_u8CalculatePage(uint32_t Copy_u32AddrPage)
{

	uint32_t Result = (Copy_u32AddrPage & 0x0000FFFF);
	Result /= PAGE_SIZE;
	return Result;
}

static uint8_t BL_u8VerifyCRC(uint8_t *Copy_u8Data , uint8_t Copy_u8Length , uint32_t Copy_u8HostCRC)
{
	uint8_t CRC_Statues = CRC_NOT_VERIFIED;
	uint8_t CRC_TEMP = 0;
	uint32_t CRC_Value = 0xFFFFFFFF;

	    for(uint32_t i = 0 ; i < Copy_u8Length ; i++)
	    {
	    	CRC_TEMP = Copy_u8Data[i];

	        CRC_Value = CRC_Value ^ CRC_TEMP;
	        for(uint32_t j = 0 ; j < 32 ; j++)
	        {
	            if(CRC_Value & 0x80000000)
	            {
	                CRC_Value = (CRC_Value << 1) ^ 0x04C11DB7;
	            }
	            else
	            {
	                CRC_Value = (CRC_Value << 1);
	            }
	        }
	    }

	    CRC_Value &= 0xFFFFFFFF;

	    CRC_Statues = (CRC_Value == Copy_u8HostCRC)? CRC_VERIFIED : CRC_NOT_VERIFIED ;

	    return CRC_Statues;
}

static MemoryValidation_Ret_t BL_MemoryVerfiy(uint32_t  Copy_pu32MemoryAdd)
{
	MemoryValidation_Ret_t  Local_RetValue = MEM_INVALID ;

	if(Copy_pu32MemoryAdd >= FLASH_BASE  && Copy_pu32MemoryAdd <= FLASH_BANK1_END)
	{
		Local_RetValue = MEM_FLASH_VALID;
	}
	else if (Copy_pu32MemoryAdd >= SRAM_BASE && Copy_pu32MemoryAdd <= (SRAM_BASE + SRAM_SIZE ))
	{
		Local_RetValue = MEM_SRAM_VALID;
	}
	else if (Copy_pu32MemoryAdd >= SYSMEM_BASE   && Copy_pu32MemoryAdd <= SYSMEM_END  )
	{
		Local_RetValue = MEM_SYS_VALID;
	}

	return Local_RetValue;
}

static HAL_StatusTypeDef BL_FLASHErase(uint8_t Copy_u8PageNum , uint8_t Copy_u8NumOfPage)
{
	uint8_t Local_u8MaxNumPages = (uint8_t)(NUM_OF_PAGES - Copy_u8PageNum) ;
	HAL_StatusTypeDef Local_FlashRet = HAL_OK;

	// Check on the Page Number and Number of Pages
	if( ((Copy_u8PageNum > NUM_OF_PAGES) || (Copy_u8NumOfPage > Local_u8MaxNumPages ) )   &&   (Copy_u8PageNum != MASS_ERASE_CMD))
	{
		Local_FlashRet = HAL_ERROR;
	}
	else
	{
		// Erase Parameters
		FLASH_EraseInitTypeDef pEraseInit ;
		uint32_t PageError;

		// Check on Mass Erase
		if(Copy_u8PageNum == MASS_ERASE_CMD)
		{
			pEraseInit.TypeErase = FLASH_TYPEERASE_MASSERASE;
			pEraseInit.Banks = FLASH_BANK_1;
			pEraseInit.PageAddress = PAGE_BASE_ADDR;
			pEraseInit.NbPages = Local_u8MaxNumPages;

		}
		else
		{
			pEraseInit.TypeErase = FLASH_TYPEERASE_PAGES;

			// Choose Number of Banks  --> This option is not support in  STM32F103C8T6 so it is considered as 1 Bank
			pEraseInit.Banks = FLASH_BANK_1;

			// Enter the Page Address
			pEraseInit.PageAddress = PAGE_BASE_ADDR + ((uint32_t)Copy_u8PageNum * PAGE_SIZE);

			// Number of Pages
			pEraseInit.NbPages = (Copy_u8NumOfPage > Local_u8MaxNumPages)? Local_u8MaxNumPages: Copy_u8NumOfPage ;
		}

			// Unlock Flash
			if(HAL_FLASH_Unlock() == HAL_OK)
			{
				// Call the Fuction
				HAL_FLASHEx_Erase(&pEraseInit, &PageError);

			}
			else
			{
				Local_FlashRet = HAL_ERROR;
			}


			// Lock Flash
			if(HAL_FLASH_Lock()== HAL_OK)
			{
				// Nothing
			}
			else
			{
				Local_FlashRet = HAL_ERROR;
			}


	}

	return Local_FlashRet;
}


static HAL_StatusTypeDef BL_FLASHWrite(uint32_t Copy_u32StatingAdd , uint32_t * Copy_u16Payload , uint8_t Copy_u8PayLoadLen)
{


	// Define the Return Variable
	HAL_StatusTypeDef Local_Ret = HAL_OK;

	// Check the flash  address
	if(Copy_u32StatingAdd >= FLASH_BASE  && Copy_u32StatingAdd <= FLASH_BANK1_END)
	{
		// Define the loop iterator
		uint8_t Local_u8Iterator ;
		uint8_t NumHalfWord = (Copy_u8PayLoadLen / 4)  ;

		// Unlock Flash
		HAL_FLASH_Unlock();

		// Write the data to flash
		for(Local_u8Iterator = 0 ; Local_u8Iterator < NumHalfWord ; Local_u8Iterator++ )
		{

			HAL_FLASH_Program(FLASH_TYPEPROGRAM_WORD , (Copy_u32StatingAdd+(Local_u8Iterator*4)) ,  Copy_u16Payload[Local_u8Iterator] );

		}

		// Lock Flash
		HAL_FLASH_Lock();
	}
	else
	{
		Local_Ret = HAL_ERROR;
	}

	return Local_Ret;
}




static void BL_VoidSendAck(uint8_t Copy_u8ReplyLength)
{
    uint8_t local_u8Buffer[2] = {BL_ACK, Copy_u8ReplyLength};

    HAL_UART_Transmit(&huart1, local_u8Buffer, 2, HAL_MAX_DELAY);
}

static void BL_VoidSendNack(void)
{
    uint8_t local_u8Buffer = BL_NACK;

    HAL_UART_Transmit(&huart1, &local_u8Buffer , 1, HAL_MAX_DELAY);
}

/************************** Function Implementation **************************/
void BL_VoidHandleGetVerCmd(uint8_t *Copy_u8buffer)
{
    // Data Packet
      /********************************/
     /* Length *  Command  *  CRC    */
    /********************************/

    // Local variables
    uint8_t local_u8CmdLen = Copy_u8buffer[0]+1;
    uint32_t local_u32HostCRC = *((uint32_t *)(Copy_u8buffer + local_u8CmdLen - 4));
    uint8_t local_u8CRCStatues = BL_u8VerifyCRC(Copy_u8buffer , (local_u8CmdLen - 4) , local_u32HostCRC);

    // Check the CRC
    if(local_u8CRCStatues == CRC_VERIFIED)
    {
        // Send Ack
        BL_VoidSendAck(1);

        // Send the Bootloader Version
        uint8_t local_u8BLVersion = BL_VERSION;
        HAL_UART_Transmit(&huart1, &local_u8BLVersion, 1, HAL_MAX_DELAY);
    }
    else
    {
        // Send Nack
        BL_VoidSendNack();
    }
}

void BL_VoidHandleGetHelpCmd(uint8_t *Copy_u8buffer)
{

		uint8_t local_pu8SupportedCMD[] =
		{
				0x51,
				0x52,
				0x53,
				0x54,
				0x55,
				0x56,
				0x57,
				0x58,
				0x59,
				0x5A,
				0x5B,
				0x5C

		};

	    uint8_t local_u8CmdLen = Copy_u8buffer[0]+1;
	    uint32_t local_u32HostCRC = *((uint32_t *)(Copy_u8buffer + local_u8CmdLen - 4));
	    uint8_t local_u8CRCStatues = BL_u8VerifyCRC(Copy_u8buffer , (local_u8CmdLen - 4) , local_u32HostCRC);

	    // Check the CRC
	    if(local_u8CRCStatues == CRC_VERIFIED)
	    {
	        // Send Ack
	        BL_VoidSendAck(sizeof(local_pu8SupportedCMD));

	        // Send the Bootloader Cmd
	        HAL_UART_Transmit(&huart1, local_pu8SupportedCMD, sizeof(local_pu8SupportedCMD), HAL_MAX_DELAY);
	    }
	    else
	    {
	        // Send Nack
	        BL_VoidSendNack();
	    }

}

void BL_VoidHandleGetCIDCmd(uint8_t *Copy_u8buffer)
{
	    uint8_t local_u8CmdLen = Copy_u8buffer[0]+1;
	    uint32_t local_u32HostCRC = *((uint32_t *)(Copy_u8buffer + local_u8CmdLen - 4));
	    uint8_t local_u8CRCStatues = BL_u8VerifyCRC(Copy_u8buffer , (local_u8CmdLen - 4) , local_u32HostCRC);

	    // Check the CRC
	    if(local_u8CRCStatues == CRC_VERIFIED)
	    {

	    	uint16_t local_u16DeviceId =  (uint16_t)(CHIP_ID & 0x0FFF);
	        // Send Ack
	        BL_VoidSendAck(sizeof(local_u16DeviceId));

	        // Send the Device ID
	        HAL_UART_Transmit(&huart1, &local_u16DeviceId, sizeof(local_u16DeviceId), HAL_MAX_DELAY);
	    }
	    else
	    {
	        // Send Nack
	        BL_VoidSendNack();
	    }

}

void BL_VoidHandleGetRDPStatusCmd(uint8_t *Copy_u8buffer)
{

		    uint8_t local_u8CmdLen = Copy_u8buffer[0]+1;
		    uint32_t local_u32HostCRC = *((uint32_t *)(Copy_u8buffer + local_u8CmdLen - 4));
		    uint8_t local_u8CRCStatues = BL_u8VerifyCRC(Copy_u8buffer , (local_u8CmdLen - 4) , local_u32HostCRC);

		    // Check the CRC
		    if(local_u8CRCStatues == CRC_VERIFIED)
		    {

		    	uint8_t local_u8RDPStatus =  (uint8_t)((RDP >> 8) & 0xFF);
		        // Send Ack
		        BL_VoidSendAck(sizeof(local_u8RDPStatus));

		        // Send the Device ID
		        HAL_UART_Transmit(&huart1, &local_u8RDPStatus, sizeof(local_u8RDPStatus), HAL_MAX_DELAY);
		    }
		    else
		    {
		        // Send Nack
		        BL_VoidSendNack();
		    }


}

void BL_VoidHandleGoToAddrCmd(uint8_t *Copy_u8buffer)
{

	 	 	 	uint8_t local_u8CmdLen = Copy_u8buffer[0]+1;
	 	 	 	uint32_t local_u32HostCRC = *((uint32_t *)(Copy_u8buffer + local_u8CmdLen - 4));
			    uint8_t local_u8CRCStatues = BL_u8VerifyCRC(Copy_u8buffer , (local_u8CmdLen - 4) , local_u32HostCRC);

			    // Check the CRC
			    if(local_u8CRCStatues == CRC_VERIFIED)
			    {

			    	  uint32_t  Local_u32ADDR = *((uint32_t *)(Copy_u8buffer + 2));
			    	  MemoryValidation_Ret_t Local_MemCheck = BL_MemoryVerfiy(Local_u32ADDR) ;
			    	  // Check Memory Validation
			    	  if(Local_MemCheck == MEM_INVALID)
			    	   {
			    		       // Send Ack
			    		  	   BL_VoidSendAck(sizeof(Local_MemCheck));

			    		  	   // Send the Memory Status
			    		  	   HAL_UART_Transmit(&huart1, &Local_MemCheck, sizeof(Local_MemCheck), HAL_MAX_DELAY);
			    	   }
			    	  else
			    	  {
			    		         // Send Ack
			    		  	     BL_VoidSendAck(sizeof(Local_MemCheck));

			    		  	     // Send the Memory Status
			    		  	     HAL_UART_Transmit(&huart1, &Local_MemCheck, sizeof(Local_MemCheck), HAL_MAX_DELAY);


			    		  	     void (* Local_PTF) (void);

			    		  	     Local_u32ADDR |= 0x0001;  // To making T-Bit = 1 --> refer to bit[0];


			    		  	     Local_PTF = (void *)  Local_u32ADDR;


			    		  	     Local_PTF();

			    	  }

			    }
			    else
			    {
			        // Send Nack
			        BL_VoidSendNack();
			    }

}

void BL_VoidHandleFlashEraseCmd(uint8_t *Copy_u8buffer)
{
	            uint8_t local_u8CmdLen = Copy_u8buffer[0]+1;
			    uint32_t local_u32HostCRC = *((uint32_t *)(Copy_u8buffer + local_u8CmdLen - 4));
			    uint8_t local_u8CRCStatues = BL_u8VerifyCRC(Copy_u8buffer , (local_u8CmdLen - 4) , local_u32HostCRC);

			    // Check the CRC
			    if(local_u8CRCStatues == CRC_VERIFIED)
			    {

			    	// Variable for Return Value
			    	HAL_StatusTypeDef Local_FlashRet;



			    	// Call the Erase Function
			    	Local_FlashRet = BL_FLASHErase(Copy_u8buffer[PAGENUM], Copy_u8buffer[NUMPAGES]);



			    	// Send ACK
			    	BL_VoidSendAck(sizeof(Local_FlashRet));


			    	// Send Reply
	    		  	   HAL_UART_Transmit(&huart1, &Local_FlashRet , sizeof(Local_FlashRet), HAL_MAX_DELAY);

			    }
			    else
			    {
			        // Send Nack
			        BL_VoidSendNack();
			    }


}

void BL_VoidHandleMemWriteCmd(uint8_t *Copy_u8buffer)
{

					uint8_t local_u8CmdLen = Copy_u8buffer[0]+1;
				    uint32_t local_u32HostCRC = *((uint32_t *)(Copy_u8buffer + local_u8CmdLen - 4));
				    uint8_t local_u8CRCStatues = BL_u8VerifyCRC(Copy_u8buffer , (local_u8CmdLen - 4) , local_u32HostCRC);

				    // Check the CRC
				    if(local_u8CRCStatues == CRC_VERIFIED)
				    {

				    	uint32_t  Local_u32ADDR = *((uint32_t *)(Copy_u8buffer + 2));
				    	MemoryValidation_Ret_t Local_MemCheck = BL_MemoryVerfiy(Local_u32ADDR);

						if(Local_MemCheck ==  MEM_INVALID)
						{
							// Send ACK
							BL_VoidSendAck(sizeof(Local_MemCheck));

							// Send Satuts
							HAL_UART_Transmit(&huart1, &Local_MemCheck, sizeof(Local_MemCheck), HAL_MAX_DELAY);
						}
						else
						{

							// Variable for Return Value
							HAL_StatusTypeDef Local_FlashRet;


							if(Local_u8Counter == 0)
							{
									Copy_u32AddrUserApp = *((uint32_t *)(Copy_u8buffer + 2));
									uint8_t Local_u8PageNum = BL_u8CalculatePage(Local_u32ADDR);
									BL_FLASHErase(Local_u8PageNum, (127-Local_u8PageNum));

									Local_u8Counter = 1;
							}



							// Send ACK
							BL_VoidSendAck(sizeof(Local_FlashRet));


							// Call the Erase Function
							Local_FlashRet = BL_FLASHWrite(Local_u32ADDR , (uint16_t *)&Copy_u8buffer[PAYLOAD] , Copy_u8buffer[PAYLOAD_LEN]);


							// Send Reply
					     	HAL_UART_Transmit(&huart1, &Local_FlashRet , sizeof(Local_FlashRet), HAL_MAX_DELAY);

						}



				    }
				    else
				    {
				        // Send Nack
				        BL_VoidSendNack();
				    }


}




void BL_VoidHandleEnRWProtectCmd(uint8_t *Copy_u8buffer)
{

}

void BL_VoidHandleMemReadCmd(uint8_t *Copy_u8buffer)
{

}

void BL_VoidHandleReadSectorPStatusCmd(uint8_t *Copy_u8buffer)
{

}

void BL_VoidHandleOTPRreadCmd(uint8_t *Copy_u8buffer)
{

}

void BL_VoidHandleDisRWProtectCmd(uint8_t *Copy_u8buffer)
{

}

void BL_VoidJumpToUserApp(uint8_t *Copy_u8buffer)
{

	            // Send Ack
	            BL_VoidSendAck(1);

	            // Send the Bootloader Version
	            uint8_t local_u8BLVersion = BL_VERSION;
	            HAL_UART_Transmit(&huart1, &local_u8BLVersion, 1, HAL_MAX_DELAY);


	            Local_u8Counter = 0;

	        	// Pointer to Reset Handler
	        	void (*Local_pResetHandler) (void);

	        	uint32_t ResetHandlerAddress;

	        	// Configure Msp of User App
	        	uint32_t Local_u32MspValue = *((volatile  uint32_t * ) Copy_u32AddrUserApp);

	        	// Write the user MSP value int MSP register
	        	__asm volatile ("MSR MSP , %0" : :"r"(Local_u32MspValue ));

	        	// Get the Reset Handler Address
	        	ResetHandlerAddress = *((volatile  uint32_t * ) (Copy_u32AddrUserApp+4));

	        	Local_pResetHandler = (void *) ResetHandlerAddress;

	        	// Jump to User App reset Handler
	        	Local_pResetHandler();
}

