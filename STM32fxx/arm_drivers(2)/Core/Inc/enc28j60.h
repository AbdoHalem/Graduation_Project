/*
 * enc28j60.h
 *
 *  Created on: Feb 22, 2025
 *      Author: A
 */

#ifndef INC_ENC28J60_H_
#define INC_ENC28J60_H_


#include "stm32f1xx_hal.h"

extern SPI_HandleTypeDef hspi1;
extern GPIO_TypeDef* ENC28J60_CS_PORT;
extern uint16_t ENC28J60_CS_PIN;
extern uint8_t mymac[];

#define ENC28J60_READ_CTRL_REG       0x00
#define ENC28J60_READ_BUF_MEM        0x3A
#define ENC28J60_WRITE_CTRL_REG      0x40
#define ENC28J60_WRITE_BUF_MEM       0x7A
#define ENC28J60_BIT_FIELD_SET       0x80
#define ENC28J60_BIT_FIELD_CLR       0xA0
#define ENC28J60_SOFT_RESET          0xFF

#define ENC28J60_CONTROL_REGISTERS   0x1F
#define ENC28J60_ADDR_MASK           0x1F

#define EIE              0x1B
#define EIR              0x1C
#define ESTAT            0x1D
#define ECON2            0x1E
#define ECON1            0x1F

#define ERDPTL           0x00
#define ERDPTH           0x01
#define EWRPTL           0x02
#define EWRPTH           0x03
#define ETXSTL           0x04
#define ETXSTH           0x05
#define ETXNDL           0x06
#define ETXNDH           0x07
#define ERXSTL           0x08
#define ERXSTH           0x09
#define ERXNDL           0x0A
#define ERXNDH           0x0B
#define ERXRDPTL         0x0C
#define ERXRDPTH         0x0D

#define MACON1           0x00
#define MACON3           0x02
#define MACON4           0x03
#define MABBIPG          0x04
#define MAIPGL           0x06
#define MAIPGH           0x07
#define MIREGADR         0x14
#define MIWRL            0x16
#define MIWRH            0x17
#define MISTAT           0x0A
#define MICMD            0x12
#define MIRDL            0x18
#define MIRDH            0x19

#define MAADR5           0x00
#define MAADR4           0x01
#define MAADR3           0x02
#define MAADR2           0x03
#define MAADR1           0x04
#define MAADR0           0x05

#define PHCON1           0x00
#define PHSTAT2          0x11
#define PHCON2           0x10

#define RXSTART_INIT     0x0000
#define RXSTOP_INIT      0x0BFF
#define TXSTART_INIT     0x0C00
#define TXSTOP_INIT      0x11FF
#define ENC28J60_MAXFRAME 1500
#define ENC28J60_UDP_HEADER_LEN 42

void enc28j60Init(uint8_t* macaddr);
void enc28j60clkout(uint8_t clk);
void enc28j60SetIP(uint8_t* ipaddr);
uint8_t enc28j60linkup(void);
void enc28j60PhyWrite(uint8_t address, uint16_t data);
uint16_t enc28j60PhyRead(uint8_t address);
void enc28j60PacketSend(uint8_t* packet, uint16_t len);
void enc28j60PacketSendUDP(uint8_t* dest_ip, uint16_t dest_port, uint16_t src_port, uint8_t* data, uint16_t len);
void enc28j60MakeUDPheader(uint8_t* buffer, uint8_t* dest_ip, uint16_t dest_port, uint16_t src_port, uint16_t len);

#endif /* INC_ENC28J60_H_ */
