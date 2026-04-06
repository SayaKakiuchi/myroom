// PIC16F18877 Configuration Bit Settings

// Configuration bits: selected in the GUI

//CONFIG1
#pragma config FEXTOSC = HS     // External Oscillator mode selection bits->EC above 8MHz; PFM set to high power
#pragma config RSTOSC = EXT1X     // Power-up default value for COSC bits->EXTOSC operating per FEXTOSC bits
#pragma config CLKOUTEN = OFF     // Clock Out Enable bit->CLKOUT function is disabled; i/o or oscillator function on OSC2
#pragma config CSWEN = ON     // Clock Switch Enable bit->Writing to NOSC and NDIV is allowed
#pragma config FCMEN = ON     // Fail-Safe Clock Monitor Enable bit->FSCM timer enabled

//CONFIG2
#pragma config MCLRE = ON     // Master Clear Enable bit->MCLR pin is Master Clear function
#pragma config PWRTE = OFF     // Power-up Timer Enable bit->PWRT disabled
#pragma config LPBOREN = OFF     // Low-Power BOR enable bit->ULPBOR disabled
#pragma config BOREN = ON     // Brown-out reset enable bits->Brown-out Reset Enabled, SBOREN bit is ignored
#pragma config BORV = LO     // Brown-out Reset Voltage Selection->Brown-out Reset Voltage (VBOR) set to 1.9V on LF, and 2.45V on F Devices
#pragma config ZCD = OFF     // Zero-cross detect disable->Zero-cross detect circuit is disabled at POR.
#pragma config PPS1WAY = ON     // Peripheral Pin Select one-way control->The PPSLOCK bit can be cleared and set only once in software
#pragma config STVREN = ON     // Stack Overflow/Underflow Reset Enable bit->Stack Overflow or Underflow will cause a reset
#pragma config DEBUG = OFF     // Background Debugger->Background Debugger disabled

//CONFIG3
#pragma config WDTCPS = WDTCPS_31     // WDT Period Select bits->Divider ratio 1:65536; software control of WDTPS
#pragma config WDTE = OFF     // WDT operating mode->WDT Disabled, SWDTEN is ignored
#pragma config WDTCWS = WDTCWS_7     // WDT Window Select bits->window always open (100%); software control; keyed access not required
#pragma config WDTCCS = SC     // WDT input clock selector->Software Control

//CONFIG4
#pragma config WRT = OFF     // UserNVM self-write protection bits->Write protection off
#pragma config SCANE = available     // Scanner Enable bit->Scanner module is available for use
#pragma config LVP = ON     // Low Voltage Programming Enable bit->Low Voltage programming enabled. MCLR/Vpp pin function is MCLR.

//CONFIG5
#pragma config CP = OFF     // UserNVM Program memory code protection bit->Program Memory code protection disabled
#pragma config CPD = OFF     // DataNVM code protection bit->Data EEPROM code protection disabled


// #pragma config statements should precede project file includes.
// Use project enums instead of #define for ON and OFF.

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <xc.h>
#include "i2c_master.h"
#include "uart.h"

unsigned char address = 0x48 << 1;
unsigned char id_register = 0x0B;
unsigned char config_register = 0x03;
unsigned char msb_register =  0x00;
unsigned char lsb_register = 0x01;

unsigned char rdata[] = {0};
unsigned char rdata1[] = {0};
//unsigned char rdata2[] = {0};


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

void I2CPortsInit()     //Configure needed ports (just for testing)
{
    LATC = 0x18;
    TRISC = 0xFF;
    ANSELC = 0xE7;
    WPUC = 0x00;
    ODCONC = 0x0;
    SLRCONC = 0xFF;
    INLVLC = 0xFF;
    
    LATD = 0x6;
    TRISD = 0xFF;
    ANSELD = 0xF9;
    WPUD = 0x0;
    ODCOND = 0x0;
    SLRCOND = 0xFF;
    INLVLD = 0xFF;

    /**
    PPS registers
    */
    SSP1CLKPPS = 0x13;  //RC3->MSSP1:SCL1;
    RC3PPS = 0x14;  //RC3->MSSP1:SCL1;
    SSP1DATPPS = 0x14;  //RC4->MSSP1:SDA1;
    RC4PPS = 0x15;  //RC4->MSSP1:SDA1;
    
    SSP2CLKPPS = 0x19;  //RD1->MSSP2:SCL2;
    RD1PPS = 0x16;  //RD1->MSSP2:SCL2;
    SSP2DATPPS = 0x1A;  //RD2->MSSP2:SDA2;
    RD2PPS = 0x17;  //RD2->MSSP2:SDA2;
}

void main()
{
    CLOCK_Initialize();
    UARTPortsInit();
    I2CPortsInit();
    
    uartInit(9600);
    i2cMasterInit(1,100000);
    
    unsigned char i2cAddr = 0x48 << 1;
    unsigned char idRegAddr = 0x0B;
    unsigned char configRegAddr = 0x03;
    unsigned char rdata[]={0};
    unsigned char writeData16bit[2]={configRegAddr,0x80};
    unsigned char writeData13bit[2]={configRegAddr,0x00};
    
    for(;;){
        i2cMasterWriteRead(1,&i2cAddr, &idRegAddr,1,rdata,1);
        printf("The Value of ID reg is %#x\r\n", rdata[0]);
        __delay_ms(1000);
        
        i2cMasterWriteRead(1,&i2cAddr,&configRegAddr,1,rdata,1);
        printf("The Value of Config Reg is %#x\r\n", rdata[0]);
        __delay_ms(1000);
        
        i2cMasterWrite(1,&i2cAddr,writeData16bit,2);
        
        i2cMasterWriteRead(1,&i2cAddr,&configRegAddr,1,rdata,1);
        printf("The Value of Config Reg is %#x\r\n", rdata[0]);
        __delay_ms(1000);
        
        i2cMasterWrite(1,&i2cAddr,writeData13bit,2);
    }
}
