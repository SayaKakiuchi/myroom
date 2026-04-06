#include <xc.h>
#include "spi_master.h"

#define SDCARD 1                // 0: SDCARD functions disabled; 1: SDCARD functions enabled

void spiMasterInit(unsigned char mode)
{
    if (mode == 0)
    {
        //SPI setup              //MODE 0
        SSP2STAT = 0x64;         //Data is sampled in the rising edge and shifted out on the falling edge
        SSP2CON1 = 0x0A;         //Clock polarity low
    }

    if (mode == 1)
    {
        //SPI setup              //MODE 1
        SSP2STAT = 0x24;         //Data sampled on the falling edge and shifted out in the rising edge
        SSP2CON1 = 0x0A;         //Clock polarity low
    }

    if (mode == 2)
    {
        //SPI setup              //MODE 2
        SSP2STAT = 0x64;         //Data is sampled in the rising edge and shifted out on the falling edge
        SSP2CON1 = 0x1A;         //Clock polarity high
    }

    if (mode == 3)
    {
        //SPI setup              //MODE 3
        SSP2STAT = 0x24;         //Data sampled on the falling edge and shifted out in the rising edge
        SSP2CON1 = 0x1A;         //Clock polarity high
    }

    //SSP2ADD = 0x9;               //SPI clock 500kHz 
    //SSP2ADD = 0x01;               //SPI clock 2.5MHz 
    SSP2ADD = 499;
    TRISBbits.TRISB2 = 0;
    SSP2CON1bits.SSPEN = 1;
}

/**************************************************************************************
 * spiWrite
 *
 * Writes to an 8-bit register in a slave with the SPI protocol. The pins where
 * the slave device is connected are defined in the header. Call `spiInit`
 * before using this function for the first time.
 *
 * Note
 * -----
 * In order to transmit the data to the slave, the user should bring the slave's
 * chip select to 0 before calling this function. Similarly, the CS should be
 * set high after the end of the transmission.
 *
 * Used pin definitions from the header:
 * --------------------------------------
 *  * SPI_MOSI_MASTER: master output, slave input,
 *  * SPI_MISO_MASTER: master input, slave output,
 *  * SPI_CK_MASTER: clock.
 *
 * Attributes
 * -----------
 *  * outDataPtr: pointer to the data to send.
 *
 **************************************************************************************/
unsigned char spiWrite(const unsigned char* outDataPtr)//TODO this could take data as input, pointer makes no sense because we copy the data later anyway
{
    SSP2BUF = *outDataPtr;       //Send data
    
    unsigned int timeout = 61538;                       // Setting up timeout counter of about 100ms
    while((!SSP2STATbits.BF) && (--timeout > 0));       //Wait for the data to be transmitted
    if (timeout == 0){return 0;}                        // If timeout then finish turning off TIMER1 and return 0 (error)
    return 1;                                           // Return 1 after successful transaction
}

/**************************************************************************************
 * spiRead
 *
 * Reads an 8-bit register in a slave with the SPI protocol. The pins where
 * the slave device is connected are defined in the header. Call `spiInit`
 * before using this function for the first time.
 *
 * Note
 * -----
 * In order to receive the data from the slave, the user should bring the slave's
 * chip select to 0 before calling this function. Similarly, the CS should be
 * set high after the end of the transmission.
 *
 * Used pin definitions from the header:
 * --------------------------------------
 *  * SPI_MOSI_MASTER: master output, slave input,
 *  * SPI_MISO_MASTER: master input, slave output,
 *  * SPI_CK_MASTER: clock.
 *
 * Attributes
 * -----------
 *  * inDataPtr: pointer of the byte where to store the received data.
 *
 **************************************************************************************/
unsigned char spiRead(unsigned char* inDataPtr)
{
    SSP2BUF = 0x00;             //Send dummy data for proper clock generation
    
    unsigned int timeout = 61538;                       // Setting up timeout counter of about 100ms
    while((!SSP2STATbits.BF) && (--timeout > 0));       //Wait for the data to be transmitted
    if (timeout == 0){return 0;}                        // If timeout then finish turning off TIMER1 and return 0 (error)
    
    *inDataPtr = SSP2BUF;       //Read the data
    return 1;                                           // Return 1 after successful transaction
}

/**************************************************************************************
 * spiRead
 *
 * Reads an 8-bit register in a slave with the SPI protocol. The pins where
 * the slave device is connected are defined in the header. Call `spiInit`
 * before using this function for the first time.
 *
 * Note
 * -----
 * In order to receive the data from the slave, the user should bring the slave's
 * chip select to 0 before calling this function. Similarly, the CS should be
 * set high after the end of the transmission.
 *
 * Used pin definitions from the header:
 * --------------------------------------
 *  * SPI_MOSI_MASTER: master output, slave input,
 *  * SPI_MISO_MASTER: master input, slave output,
 *  * SPI_CK_MASTER: clock.
 *
 * Attributes
 * -----------
 *  * inDataPtr: pointer of the byte where to store the received data.
 *
 **************************************************************************************/
unsigned char spiWriteRead(const unsigned char* outDataPtr, unsigned char* inDataPtr)
{
    SSP2BUF = *outDataPtr;             //Send dummy data for proper clock generation
    
    unsigned int timeout = 61538;                       // Setting up timeout counter of about 100ms
    while((!SSP2STATbits.BF) && (--timeout > 0));       // Wait for the data to be transmitted
    if (timeout == 0){return 0;}                        // If timeout then finish turning off TIMER1 and return 0 (error)
    
    *inDataPtr = SSP2BUF;       //Read the data
    return 1;                                           // Return 1 after successful transaction
}

/**************************************************************************************
 * spiMasterWriteBytes
 *
 * Write a number of bytes to the slave using the SPI protocol (by calling
 * `spiWrite`). The pins where the slave device is connected are defined in the
 * header. Call `spiInit` before using this function for the first time.
 *
 * Note
 * -----
 * In order to send the data to the slave, the user should bring the slave's
 * chip select to 0 before calling this function. Similarly, the CS should be
 * set high after the end of the transmission.
 *
 * Used pin definitions from the header:
 * --------------------------------------
 *  * SPI_MOSI_MASTER: master output, slave input,
 *  * SPI_MISO_MASTER: master input, slave output,
 *  * SPI_CK_MASTER: clock.
 *
 * Attributes
 * -----------
 *  * outDataPtr: array of bytes that will be sent (pointer to the first element),
 *  * nBytes: no. bytes that will be sent, starting at the first element of
 *    `outDataPtr`, inclusive.
 *
 **************************************************************************************/
void spiWriteBytes(const unsigned char* outDataPtr, unsigned char nBytes)
{
    // Simply send all the desired bytes.
    for (unsigned char i = 0; i < nBytes; i++)
    {
        spiWrite(outDataPtr + i); // One byte at a time.
    }
}

/**************************************************************************************
 * spiMasterReadBytes
 *
 * Read a number of bytes from the slave using the SPI protocol (by calling
 * `spiRead`). The pins where the slave device is connected are defined in the
 * header. Call `spiInit` before using this function for the first time.
 *
 * Note
 * -----
 * In order to receive the data from the slave, the user should bring the slave's
 * chip select to 0 before calling this function. Similarly, the CS should be
 * set high after the end of the transmission.
 *
 * Used pin definitions from the header:
 * --------------------------------------
 *  * SPI_MOSI_MASTER: master output, slave input,
 *  * SPI_MISO_MASTER: master input, slave output,
 *  * SPI_CK_MASTER: clock.
 *
 * Attributes
 * -----------
 *  * inDataPtr: array of bytes where the received data will be written, starting
 *    at index 0 (pointer to the first element),
 *  * nBytes: no. bytes that will be read.
 *
 **************************************************************************************/
void spiReadBytes(const unsigned char* inDataPtr, unsigned char nBytes)
{
    for (unsigned char i = 0; i < nBytes; i++)
    {
        spiRead(inDataPtr + i); // One byte at a time.
    }
}

// SD CARD SPI management related functions ------------------------------------------------------------------------------
#if SDCARD == 1
/**************************************************************************************
 * xchg_spi
 *
 * Single byte SPI transaction for SD CARD library
 *
 *
 * Attributes
 * -----------
 *  * dat: Byte to be sent
 *
 **************************************************************************************/
BYTE xchg_spi (BYTE dat)
{
	SSP2BUF = dat;			/* Initiate an SPI transaction */
    
    unsigned int timeout = 61538;                       // Setting up timeout counter of about 100ms
	while ((!SSP2IF) && (--timeout > 0));               // Wait for end of the SPI transaction
    if (timeout == 0){return 0;}                        // If timeout then finish turning off TIMER1 and return 0 (error)
    
    SSP2IF = 0;
	return (BYTE)SSP2BUF;	/* Get received byte */
}


/**************************************************************************************
 * xmit_spi_multi
 *
 * Multi-byte SPI transaction (transmit) for SD CARD library
 *
 * Attributes
 * -----------
 *  * buff: Buffer with the data to be send
 *  * cnt: Number of bytes to be send
 **************************************************************************************/
BYTE xmit_spi_multi (const BYTE* buff, UINT cnt)
{
	do 
    {
		SSP2BUF = *buff++;	/* Initiate an SPI transaction */
        
		unsigned int timeout = 61538;                       // Setting up timeout counter of about 100ms
        while ((!SSP2IF) && (--timeout > 0));               // Wait for end of the SPI transaction
        if (timeout == 0){return 0;}                        // If timeout then finish turning off TIMER1 and return 0 (error)
        
        SSP2IF = 0;
		SSP2BUF;			/* Discard received byte */
        
//		SSP2BUF = *buff++;
//        
//		unsigned int timeout = 61538;                       // Setting up timeout counter of about 100ms
//        while ((!SSP2IF) && (--timeout > 0));               // Wait for end of the SPI transaction
//        if (timeout == 0){return 0;}                        // If timeout then finish turning off TIMER1 and return 0 (error)
//        
//        SSP2IF = 0;
//		SSP2BUF;
	} 
    while (cnt -= 2);
    return 1;                                               // Return 1 after successful transaction
}

/**************************************************************************************
 * rcvr_spi_multi
 *
 * Multi-byte SPI transaction (receive) for SD CARD library
 *
 * Attributes
 * -----------
 *  *buff: Pointer to the buffer with the data to be send
 *  cnt: Number of bytes to be send
 **************************************************************************************/
BYTE rcvr_spi_multi (BYTE* buff, UINT cnt)
{
	do 
    {
		SSP2BUF = 0xFF;		/* Initiate an SPI transaction */
        
		unsigned int timeout = 61538;                       // Setting up timeout counter of about 100ms
        while ((!SSP2IF) && (--timeout > 0));               // Wait for end of the SPI transaction
        if (timeout == 0){return 0;}                        // If timeout then finish turning off TIMER1 and return 0 (error)
                
        SSP2IF = 0;
		*buff++ = SSP2BUF;	/* Get received byte */
//		SSP2BUF = 0xFF;
//                
//		unsigned int timeout = 61538;                       // Setting up timeout counter of about 100ms
//        while ((!SSP2IF) && (--timeout > 0));               // Wait for end of the SPI transaction
//        if (timeout == 0){return 0;}                        // If timeout then finish turning off TIMER1 and return 0 (error)
//        
//        SSP2IF = 0;
//		*buff++ = SSP2BUF;
	}
    while (cnt -= 2);
    return 1;                                               // Return 1 after successful transaction
}
#endif
// -----------------------------------------------------------------------------------------------------------------------


/*------Functions for communicating PIC to PIC via SPI (Deprecated for Ten-Koh-2)------
//-------------------------------------------------------------------------------------
 * spiMasterWriteBytesPIC
 *
 * Send the 1st array's element as the size of the array to be sent and then send
 * the array using the SPI protocol. Use only to receive data using the function
 * spiWriteBytesPIC.
 *
 * Attributes
 * -----------
 *  * outDataPtr: array of bytes that will be sent (pointer to the first element),
 *  * nBytes: no. bytes that will be sent, starting at the first element of
 *    `outDataPtr`, inclusive.
 *
 **************************************************************************************
void spiMasterWriteBytesPIC(unsigned char* const outDataPtr, unsigned char nBytes)
{
    // Decrease array elements counter till find a 0xFF (end of valid data)
    while (!((*(outDataPtr + (nBytes - 1)) == 0x00)&&(*(outDataPtr + (nBytes - 2)) == 0xFF)))
    {
        nBytes--;
    }

    nBytes = (unsigned char)(nBytes - 2);       // Number of valid array elements

    spiMasterWrite(&nBytes);                    // Sending nBytes as 1st byte
    spiMasterWriteBytes(outDataPtr, nBytes);    // Sending valid array elements
}

//-------------------------------------------------------------------------------------
 * spiMasterReadBytesPIC
 *
 * Receive the 1st array's element as the size of the received string and then receive
 * that exact number of elements using the SPI protocol. Should be used to receive
 * data sent by the function uartWriteBytesPIC.
 *
 * Attributes
 * -----------
 *  * inDataPtr: array of bytes that will be received (pointer to the first element
 * which is the size of the array).
 *
 **************************************************************************************-/
void spiMasterReadBytesPIC(unsigned char* const inDataPtr)
{
    unsigned char nBytes;       // Store number of bytes to receive
    spiMasterRead(inDataPtr);   // Receiving 1st byte (number of bytes to receive)
    if (*inDataPtr == 0xFF){return;}    // If nBytes received is wrong because a slave failure then return
    nBytes = *inDataPtr;        // Store number of bytes to receive
    spiMasterReadBytes((inDataPtr + 1), nBytes);        // Receiving nBytes
}
***************************************************************************************/
