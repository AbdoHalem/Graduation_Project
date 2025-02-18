
const uint16_t crc_polynomial = 0x8008;

uint16_t calculateCRC(const uint8_t* data, size_t length) {
    uint16_t crc = 0;

    for (size_t i = 0; i < length; ++i) {
        crc ^= (uint16_t)data[i] << 8;

        for (int j = 0; j < 8; ++j) {
            if (crc & 0x8000) {
                crc = (crc << 1) ^ crc_polynomial;
            } else {
                crc = crc << 1;
            }
        }
    }

    return crc;
}
