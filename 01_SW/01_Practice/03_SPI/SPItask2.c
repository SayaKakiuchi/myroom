// CONFIG1
#pragma config FEXTOSC = HS    // External Oscillator mode selection bits (Oscillator not enabled)
#pragma config RSTOSC = EXT1X  // Power-up default value for COSC bits (HFINTOSC (1MHz))
#pragma config CLKOUTEN = OFF   // Clock Out Enable bit (CLKOUT function is disabled; i/o or oscillator function on OSC2)
#pragma config CSWEN = ON       // Clock Switch Enable bit (Writing to NOSC and NDIV is allowed)
#pragma config FCMEN = ON       // Fail-Safe Clock Monitor Enable bit (FSCM timer enabled)

// CONFIG2
#pragma config MCLRE = ON       // Master Clear Enable bit (MCLR pin is Master Clear function)
#pragma config PWRTE = OFF      // Power-up Timer Enable bit (PWRT disabled)
#pragma config LPBOREN = OFF    // Low-Power BOR enable bit (ULPBOR disabled)
#pragma config BOREN = ON       // Brown-out reset enable bits (Brown-out Reset Enabled, SBOREN bit is ignored)
#pragma config BORV = LO        // Brown-out Reset Voltage Selection (Brown-out Reset Voltage (VBOR) set to 1.9V on LF, and 2.45V on F Devices)
#pragma config ZCD = OFF        // Zero-cross detect disable (Zero-cross detect circuit is disabled at POR.)
#pragma config PPS1WAY = ON     // Peripheral Pin Select one-way control (The PPSLOCK bit can be cleared and set only once in software)
#pragma config STVREN = ON      // Stack Overflow/Underflow Reset Enable bit (Stack Overflow or Underflow will cause a reset)

// CONFIG3
#pragma config WDTCPS = WDTCPS_31// WDT Period Select bits (Divider ratio 1:65536; software control of WDTPS)
#pragma config WDTE = OFF       // WDT operating mode (WDT Disabled, SWDTEN is ignored)
#pragma config WDTCWS = WDTCWS_7// WDT Window Select bits (window always open (100%); software control; keyed access not required)
#pragma config WDTCCS = SC      // WDT input clock selector (Software Control)

// CONFIG4
#pragma config WRT = OFF        // UserNVM self-write protection bits (Write protection off)
#pragma config SCANE = available// Scanner Enable bit (Scanner module is available for use)
#pragma config LVP = ON         // Low Voltage Programming Enable bit (Low Voltage programming enabled. MCLR/Vpp pin function is MCLR.)

// CONFIG5
#pragma config CP = OFF         // UserNVM Program memory code protection bit (Program Memory code protection disabled)
#pragma config CPD = OFF        // DataNVM code protection bit (Data EEPROM code protection disabled)

// #pragma config statements should precede project file includes.
// Use project enums instead of #define for ON and OFF.

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "spi_master.h"
#include "uart.h"
#include <xc.h>

#define CS_PIN LATBbits.LATB5  // using RB5 as Chip Select PIN
#define _XTAL_FREQ 20000000

void CLOCK_Initialize(void)
{
    // Set the CLOCK CONTROL module to the options selected in the user interface.
    // NDIV 1; NOSC EXTOSC;
    OSCCON1 = 0x70;
    //
    OSCCON2 = 0x70;
    // SOSCPWR High power; CSWHOLD may proceed;
    OSCCON3 = 0x40;
    // EXTOEN enabled; HFOEN disabled; MFOEN disabled; LFOEN disabled; SOSCEN disabled; ADOEN disabled;
    OSCEN = 0x80;
    // HFFRQ 4_MHz;
    OSCFRQ = 0x2;
    //
    OSCSTAT = 0x0;
    // TUN undefined;
    OSCTUNE = 0x0;
}

void pinInit (void)
{
     /* PORTB
     * --------------------------------------------------------------------------------
     * | XXX | XXX   |   CS    |     XXX     | SPI_MOSI | SPI_SCLK | SPI_MISO |  XXX    |
     * --------------------------------------------------------------------------------
     * | RB7  | RB6  | RB5     | RB4         | RB3      | RB2      | RB1      | RB0     |
     * --------------------------------------------------------------------------------
     * | OUT  | OUT  | OUT     | OUT         | OUT      | OUT       | IN      | OUT     |
     * -------------------------------------------------------------------------------- */

    LATB = 0x0; 
    TRISB = 0b00000010; // GPIO CONFIGURATION REG (1 = In, 0 = Out)
    ANSELB = 0x0; // ALL DIGITAL
    WPUB = 0x0; 
    ODCONB = 0x0;
    SLRCONB = 0xFF;
    INLVLB = 0xFF;
    
    CS_PIN = 1;

    // SPI  registers ----------------------------------------------------------
    SSP2DATPPS = 0x9;       //RB1->MSSP2:SDI2;
    RB3PPS = 0x17;          //RB3->MSSP2:SDO2;
    SSP2CLKPPS = 0xA;       //RB2->MSSP2:SCK2;
    RB2PPS = 0x16;          //RB2->MSSP2:SCK2;
    //--------------------------------------------------------------------------
}

void UARTPortsInit(void)
{
    ANSELCbits.ANSC6 = 0;           // Digital
    TRISCbits.TRISC6 = 0;           // Output

    ANSELCbits.ANSC7 = 0;           // Digital    
    TRISCbits.TRISC7 = 1;           // Input      

    RC6PPS = 0x10;                  //RC6->EUSART:TX;
    RXPPSbits.RXPPS = 0x17;         //RC7->EUSART:RX;
    
    ANSELDbits.ANSD7 = 0;           // Digital
    TRISDbits.TRISD7 = 1;           // Input
    
    ANSELDbits.ANSD6 = 0;           // Digital
    TRISDbits.TRISD6 = 1;           // Input
}

unsigned char spiWriteReadTest(const unsigned char* outDataPtr, unsigned char* inDataPtr){
    
    unsigned char dummy;
    dummy = SSP2BUF;
    SSP2BUF = *outDataPtr;

    unsigned int timeout = 61538;
    while((!SSP2STATbits.BF) && (--timeout > 0));
    if (timeout == 0) {
        return 0;
    }

    dummy = SSP2BUF;
    SSP2BUF = 0xFF;

    timeout = 61538;
    while((!SSP2STATbits.BF) && (--timeout > 0));

    if (timeout == 0) {
        return 0;
    }
    
    *inDataPtr = SSP2BUF;
    
    return 1;
}

unsigned char spiReadTest(const unsigned char* addr, unsigned char* inDataPtr, unsigned int nBytes){

    unsigned char dummy;
    
    dummy = SSP2BUF;
    SSP2BUF = *addr;
    
    unsigned int timeout = 61538;
    while ((!SSP2STATbits.BF) && (--timeout > 0));
    if (timeout == 0) {
        return 0;
    }

    dummy = SSP2BUF;
    
    for (unsigned int i = 0; i < nBytes; i++) {

        SSP2BUF = 0xFF; //sending dummy
        
        timeout = 61538;
        while ((!SSP2STATbits.BF) && (--timeout > 0));
        if (timeout == 0) {
            return 0;
        }

        *(inDataPtr + i) = SSP2BUF;
    }
    
    return 1;
}

unsigned char spiWriteTest(const unsigned char* addr, unsigned char* data){
    
    unsigned char dummy;
    dummy = SSP2BUF;
    SSP2BUF = *addr; //sending register address
    
    unsigned int timeout = 61538;
    while((!SSP2STATbits.BF) && (--timeout > 0));
    if (timeout ==0){
        return 0;
    }
    
    dummy = SSP2BUF;
    SSP2BUF = *data;
    
    timeout = 61538;
    while((!SSP2STATbits.BF) && (--timeout > 0));
    if (timeout ==0){
        return 0;
    }
    
    dummy = SSP2BUF;
    
    return 1;
}

//void spiReadTemp(const unsigned int select){
//
//}

void main(void){
    CLOCK_Initialize();
    UARTPortsInit();
    pinInit();
    
    unsigned char mode = 3;
    
    uartInit(9600);
    spiMasterInit(mode);
    __delay_ms(100);

    unsigned char commandByteIDRead = 0b01011000;
    unsigned char rdata[1]={0};
    
    unsigned char commandByteConfigRead = 0b01001000;
    unsigned char commandByteConfigWrite = 0b00001000;
    
    unsigned char config13bit = 0b00000000;
    unsigned char config16bit = 0b10000000;
    
    for(;;){
        CS_PIN = 0;
        spiReadTest(&commandByteIDRead, rdata, 1);
        printf("Value of ID Register is %#x\r\n", rdata[0]);
        CS_PIN = 1;

        __delay_ms(1000);

        CS_PIN = 0;
        spiReadTest(&commandByteConfigRead, rdata, 1);
        printf("Value of Config Register is %#x\r\n", rdata[0]);
        CS_PIN = 1;

        __delay_ms(1000);
        
        CS_PIN = 0;
        spiWriteTest(&commandByteConfigWrite, &config16bit);
        printf("ConfigRegister is modified to 16bit setting\r\n\r\n");
        CS_PIN = 1;

        __delay_ms(1000);
        
        CS_PIN = 0;
        spiReadTest(&commandByteConfigRead, rdata, 1);
        printf("Value of Config Register is %#x\r\n", rdata[0]);
        CS_PIN = 1;
        
        __delay_ms(1000);
        
        CS_PIN = 0;
        spiWriteTest(&commandByteConfigWrite, &config13bit);
        printf("ConfigRegister is modified to 13bit setting\r\n\r\n");
        CS_PIN = 1;
        
        __delay_ms(1000);
    }

}
