/*
 * enc28j60.c
 *
 *  Created on: Feb 22, 2025
 *      Author: A
 */


#include "enc28j60.h"
#include "stm32f1xx_hal.h"
#include <string.h>

SPI_HandleTypeDef hspi1;
GPIO_TypeDef* ENC28J60_CS_PORT = GPIOA;
uint16_t ENC28J60_CS_PIN = GPIO_PIN_4;

uint8_t mymac[] = {0x74, 0x69, 0x69, 0x2D, 0x30, 0x31}; // تعريف mymac هنا بدل main.c
static uint8_t Enc28j60Bank = 0;
static uint8_t myIP[4];

static uint8_t spiTransfer(uint8_t data) {
    uint8_t rx_data;
    HAL_SPI_TransmitReceive(&hspi1, &data, &rx_data, 1, HAL_MAX_DELAY);
    return rx_data;
}

static uint8_t enc28j60ReadOp(uint8_t op, uint8_t address) {
    HAL_GPIO_WritePin(ENC28J60_CS_PORT, ENC28J60_CS_PIN, GPIO_PIN_RESET);
    spiTransfer(op | (address & ENC28J60_ADDR_MASK));
    uint8_t data = spiTransfer(0x00);
    if (address & 0x80) {
        data = spiTransfer(0x00);
    }
    HAL_GPIO_WritePin(ENC28J60_CS_PORT, ENC28J60_CS_PIN, GPIO_PIN_SET);
    return data;
}

static void enc28j60WriteOp(uint8_t op, uint8_t address, uint8_t data) {
    HAL_GPIO_WritePin(ENC28J60_CS_PORT, ENC28J60_CS_PIN, GPIO_PIN_RESET);
    spiTransfer(op | (address & ENC28J60_ADDR_MASK));
    spiTransfer(data);
    HAL_GPIO_WritePin(ENC28J60_CS_PORT, ENC28J60_CS_PIN, GPIO_PIN_SET);
}

static void enc28j60SetBank(uint8_t address) {
    if ((address & ENC28J60_CONTROL_REGISTERS) != Enc28j60Bank) {
        Enc28j60Bank = address & ENC28J60_CONTROL_REGISTERS;
        enc28j60WriteOp(ENC28J60_BIT_FIELD_CLR, ECON1, 0x03);
        enc28j60WriteOp(ENC28J60_BIT_FIELD_SET, ECON1, Enc28j60Bank >> 5);
    }
}

static void enc28j60Write(uint8_t address, uint8_t data) {
    enc28j60SetBank(address);
    enc28j60WriteOp(ENC28J60_WRITE_CTRL_REG, address, data);
}

static uint8_t enc28j60Read(uint8_t address) {
    enc28j60SetBank(address);
    return enc28j60ReadOp(ENC28J60_READ_CTRL_REG, address);
}

void enc28j60Init(uint8_t* macaddr) {
    enc28j60WriteOp(ENC28J60_SOFT_RESET, 0, ENC28J60_SOFT_RESET);
    HAL_Delay(2);

    enc28j60Write(ERXSTL, RXSTART_INIT & 0xFF);
    enc28j60Write(ERXSTH, RXSTART_INIT >> 8);
    enc28j60Write(ERXNDL, RXSTOP_INIT & 0xFF);
    enc28j60Write(ERXNDH, RXSTOP_INIT >> 8);
    enc28j60Write(ERXRDPTL, RXSTART_INIT & 0xFF);
    enc28j60Write(ERXRDPTH, RXSTART_INIT >> 8);

    enc28j60Write(ETXSTL, TXSTART_INIT & 0xFF);
    enc28j60Write(ETXSTH, TXSTART_INIT >> 8);

    enc28j60Write(MACON1, 0x0D);
    enc28j60Write(MACON3, 0x32);
    enc28j60Write(MACON4, 0x01);
    enc28j60Write(MABBIPG, 0x15);
    enc28j60Write(MAIPGL, 0x12);
    enc28j60Write(MAIPGH, 0x0C);

    enc28j60Write(MAADR5, macaddr[0]);
    enc28j60Write(MAADR4, macaddr[1]);
    enc28j60Write(MAADR3, macaddr[2]);
    enc28j60Write(MAADR2, macaddr[3]);
    enc28j60Write(MAADR1, macaddr[4]);
    enc28j60Write(MAADR0, macaddr[5]);

    enc28j60PhyWrite(PHCON1, 0x0000);
    enc28j60Write(ECON1, 0x04);
}

void enc28j60clkout(uint8_t clk) {
    enc28j60Write(ECON2, clk & 0x7);
}

void enc28j60SetIP(uint8_t* ipaddr) {
    memcpy(myIP, ipaddr, 4);
}

uint8_t enc28j60linkup(void) {
    return (enc28j60PhyRead(PHSTAT2) & 0x0400) > 0;
}

void enc28j60PhyWrite(uint8_t address, uint16_t data) {
    enc28j60Write(MIREGADR, address);
    enc28j60Write(MIWRL, data & 0xFF);
    enc28j60Write(MIWRH, data >> 8);
    while (enc28j60Read(MISTAT) & 0x01);
}

uint16_t enc28j60PhyRead(uint8_t address) {
    enc28j60Write(MIREGADR, address);
    enc28j60Write(MICMD, 0x01); // MIIRD
    while (enc28j60Read(MISTAT) & 0x01);
    enc28j60Write(MICMD, 0x00);
    return (enc28j60Read(MIRDH) << 8) | enc28j60Read(MIRDL);
}

void enc28j60PacketSend(uint8_t* packet, uint16_t len) {
    while (enc28j60ReadOp(ENC28J60_READ_CTRL_REG, ECON1) & 0x08);
    enc28j60Write(EWRPTL, TXSTART_INIT & 0xFF);
    enc28j60Write(EWRPTH, TXSTART_INIT >> 8);
    enc28j60Write(ETXNDL, (TXSTART_INIT + len) & 0xFF);
    enc28j60Write(ETXNDH, (TXSTART_INIT + len) >> 8);

    HAL_GPIO_WritePin(ENC28J60_CS_PORT, ENC28J60_CS_PIN, GPIO_PIN_RESET);
    spiTransfer(ENC28J60_WRITE_BUF_MEM);
    for (uint16_t i = 0; i < len; i++) {
        spiTransfer(packet[i]);
    }
    HAL_GPIO_WritePin(ENC28J60_CS_PORT, ENC28J60_CS_PIN, GPIO_PIN_SET);

    enc28j60WriteOp(ENC28J60_BIT_FIELD_SET, ECON1, 0x08);
}

void enc28j60MakeUDPheader(uint8_t* buffer, uint8_t* dest_ip, uint16_t dest_port, uint16_t src_port, uint16_t len) {
    uint8_t broadcast_mac[] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};
    memcpy(buffer, broadcast_mac, 6);
    memcpy(buffer + 6, mymac, 6);
    buffer[12] = 0x08; buffer[13] = 0x00;

    buffer[14] = 0x45;
    buffer[15] = 0x00;
    uint16_t total_len = len + 28;
    buffer[16] = total_len >> 8; buffer[17] = total_len & 0xFF;
    buffer[18] = 0x00; buffer[19] = 0x00;
    buffer[20] = 0x40; buffer[21] = 0x00;
    buffer[22] = 0x40;
    buffer[23] = 0x11;
    buffer[24] = 0x00; buffer[25] = 0x00;
    memcpy(buffer + 26, myIP, 4);
    memcpy(buffer + 30, dest_ip, 4);

    buffer[34] = src_port >> 8; buffer[35] = src_port & 0xFF;
    buffer[36] = dest_port >> 8; buffer[37] = dest_port & 0xFF;
    buffer[38] = (len + 8) >> 8; buffer[39] = (len + 8) & 0xFF;
    buffer[40] = 0x00; buffer[41] = 0x00;
}

void enc28j60PacketSendUDP(uint8_t* dest_ip, uint16_t dest_port, uint16_t src_port, uint8_t* data, uint16_t len) {
    uint8_t buffer[700];
    enc28j60MakeUDPheader(buffer, dest_ip, dest_port, src_port, len);
    memcpy(buffer + ENC28J60_UDP_HEADER_LEN, data, len);
    enc28j60PacketSend(buffer, len + ENC28J60_UDP_HEADER_LEN);
}
