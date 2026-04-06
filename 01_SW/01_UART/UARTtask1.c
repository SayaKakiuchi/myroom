// PIC16F18877 Configuration Bit Settings

// 'C' source line config statements

// CONFIG1
#pragma config FEXTOSC = HS        // External Oscillator mode selection bits (Oscillator not enabled)
#pragma config RSTOSC = EXT1X     // HFINTOSC = 32MHz
#pragma config CLKOUTEN = OFF       // Clock Out Enable bit (CLKOUT function is disabled; i/o or oscillator function on OSC2)
#pragma config CSWEN = ON           // Clock Switch Enable bit (Writing to NOSC and NDIV is allowed)
#pragma config FCMEN = ON           // Fail-Safe Clock Monitor Enable bit (FSCM timer enabled)

// CONFIG2
#pragma config MCLRE = ON           // Master Clear Enable bit (MCLR pin is Master Clear function)
#pragma config PWRTE = OFF          // Power-up Timer Enable bit (PWRT disabled)
#pragma config LPBOREN = OFF        // Low-Power BOR enable bit (ULPBOR disabled)
#pragma config BOREN = ON           // Brown-out reset enable bits (Brown-out Reset Enabled, SBOREN bit is ignored)
#pragma config BORV = LO            // Brown-out Reset Voltage Selection (Brown-out Reset Voltage (VBOR) set to 1.9V on LF, and 2.45V on F Devices)
#pragma config ZCD = OFF            // Zero-cross detect disable (Zero-cross detect circuit is disabled at POR.)
#pragma config PPS1WAY = ON         // Peripheral Pin Select one-way control (The PPSLOCK bit can be cleared and set only once in software)
#pragma config STVREN = ON          // Stack Overflow/Underflow Reset Enable bit (Stack Overflow or Underflow will cause a reset)

// CONFIG3
#pragma config WDTCPS = WDTCPS_31   // WDT Period Select bits (Divider ratio 1:65536; software control of WDTPS)
#pragma config WDTE = OFF           // WDT operating mode (WDT Disabled, SWDTEN is ignored)
#pragma config WDTCWS = WDTCWS_7    // WDT Window Select bits (window always open (100%); software control; keyed access not required)
#pragma config WDTCCS = SC          // WDT input clock selector (Software Control)

// CONFIG4
#pragma config WRT = OFF            // UserNVM self-write protection bits (Write protection off)
#pragma config SCANE = available    // Scanner Enable bit (Scanner module is available for use)
#pragma config LVP = ON             // Low Voltage Programming Enable bit (Low Voltage programming enabled. MCLR/Vpp pin function is MCLR.)

// CONFIG5
#pragma config CP = OFF             // UserNVM Program memory code protection bit (Program Memory code protection disabled)
#pragma config CPD = OFF            // DataNVM code protection bit (Data EEPROM code protection disabled)

// #pragma config statements should precede project file includes.
// Use project enums instead of #define for ON and OFF.

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <xc.h>
#include "uart.h"

unsigned char CR = 0x0D;    // Carriage Return Value
unsigned char rx_buffer;

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

void PORT_init(void)
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

void uartReadBytes_test(char *buffer)
{
    char rxbuffer[50]={0};
    unsigned long timeout = 806452;
    
//    while((!PIR3bits.RCIF)&&(--timeout>0));
    while(!PIR3bits.RCIF);
    
    if(timeout==0)
    {
        printf("ERROR - Communication Timeout\r\n");
        return;
    }
    
//    uartRead(buffer, 48);
    uartRead(buffer, 1);
    uartWrite(buffer, 48);
//    memset(buffer, 0, sizeof(buffer));
}

void print_menu()
{
    printf("\r\n");
    printf("Press 1 for print Okuyama-sensei's Message\r\n");
    printf("Press 2 for print Michiko-san's Message\r\n");
    printf("Press 3 for print Shun-san's Message\r\n");
    printf("\r\n");
    return;
}

void main(void)
{
    CLOCK_Initialize();
    PORT_init();
    uartInit(9600);
    
    unsigned char int_message[]={"UART PRACTICE PROGRAM\r\n"};
    unsigned char message1[]={"Press[1]!\r\n"};
    unsigned char message2[]={"Press[2]!\r\n"};
    unsigned char message3[]={"Press[3]!\r\n"};
    unsigned char last_message[]={"Press x for showing menu.\r\n\r\n"};
    
    printf("%s", int_message);
    print_menu();
    
    char rxbuffer[50]={0};
    for(;;){
//        uartWrite(message, sizeof(message));
//        __delay_ms(1000);
        
        uartReadBytes_test(rxbuffer);
        printf("RX: %d (%c)\r\n", rxbuffer[0], rxbuffer[0]);
        if(rxbuffer[0] == '1'){
            printf("Message >> %s", message1);
        }
        else if(rxbuffer[0] == '2'){
            printf("Message >> %s", message2);
        }
        else if(rxbuffer[0] == '3'){
            printf("Message >> %s", message3);
        }
        else if(rxbuffer[0] == 'x'){
            print_menu();
        }
        else
        {
            printf("Undefined Strings.\r\n");
        }
        
        printf("%s", last_message);

    }
}
