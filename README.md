# OpenMv+STM32实现颜色、形状、距离、尺寸识别

## 前言

校电赛选拔突然到DDL了，结果我们超级南望山战队还一点没动，有位队友昨晚肝了个通宵，今天大家一起努力终于把基础功能做完了。

赛题主要要求就是，识别2m外的图形形状，颜色，尺寸以及与这个图形的距离，最后在stm32上用OLED显示出来。

鉴于之前循迹小车的基础，我们很快速的完成了这个任务。

大体讲一下我们的心路历程，以及克服的困难吧。

## 颜色识别

因为OpenMv配套的软件，提供的LAB颜色参数而不是RGB，并且大部分网络代码是通过参数范围进行限定RGB三种颜色的判断的。我只能说，这种方法非常的抽象，非常的不准确，受光线影响非常严重。通过LAB解算RGB又会消耗大量的算例。

非常幸运的是，网上的一张图给了我思路。

![LAB](https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQSJlAm2wGzF3uvjCu5BVGr0hga5GHv9bGdwlfoWEp0kA&s)

我们可以明显的看出，RGB三种色域分别分布在三个部分，非常的明显。

我们的解决方案是，先通过RGB计算出，纯R,纯G，纯B对应的LAB参数。我们可以将这个参数想象为三维坐标，当我们获取到LAB参数点P，通过计算P点到纯RGB点的最小值，来确定P点对应的色，是在哪个色域内。这个方法可以用帮助我们用极小的计算量来高精度，判断颜色。

## 尺寸

emm，这个是我的队友完成的，他们说是小学数学题，我没细听，这里不讲了。

## 图形识别

通过OpenMv开发工具的库函数，当然提高功能中还有一个识别数字和字母的要求。
针对这个要求，没有现成好用的库函数可以使用。我们计划了三种途径。

第一种：卷积神经网络，训练好之后放到OpenMv的python代码中，但是OpenMv本质也是stm32，所以计算性能堪忧。

第二种：蒙特卡洛模拟，但是预计对于非常相近的字母，识别效果很差，而且网上没有找到先例，可能需要大量手炉代码，有点慌。

第三种：类似手指关节识别，确定字母关节，来判断是什么字母，优先考虑。

## 距离

直接一个超声波测距传感器搞定了。easy。

## 单片机之间的通信

感觉网上很多很抽象的工程代码，很难懂，真的太难懂了，用简单的原理简单的代码实现不好么？
这里给出一个基本的模板，当然是基于一些已经有的核心库实现的。

```cpp
#include "stm32f10x.h"
#include "LED.h"
#include "Delay.h"
#include "OLED.h"
void UART_Init(void) {
    USART_InitTypeDef USART_InitStructure; 
    GPIO_InitTypeDef GPIO_InitStructure; 
    NVIC_InitTypeDef NVIC_InitStructure;

   

    RCC_APB2PeriphClockCmd(RCC_APB2Periph_USART1 | RCC_APB2Periph_GPIOA, ENABLE);



  
    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_10; // PA.10
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_IPU; 
		GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_Init(GPIOA, &GPIO_InitStructure);

    USART_InitStructure.USART_BaudRate = 115200; 
    USART_InitStructure.USART_WordLength = USART_WordLength_8b; 
    
    USART_InitStructure.USART_StopBits = USART_StopBits_1;
    USART_InitStructure.USART_Parity = USART_Parity_No; 
    USART_InitStructure.USART_HardwareFlowControl = USART_HardwareFlowControl_None; 
    USART_InitStructure.USART_Mode = USART_Mode_Rx;
    USART_Init(USART1, &USART_InitStructure); 


    NVIC_InitStructure.NVIC_IRQChannel = USART1_IRQn; 
    NVIC_InitStructure.NVIC_IRQChannelPreemptionPriority = 1; 
    NVIC_InitStructure.NVIC_IRQChannelSubPriority = 1; 
    NVIC_InitStructure.NVIC_IRQChannelCmd = ENABLE; À
    NVIC_Init(&NVIC_InitStructure); 

 
    USART_ITConfig(USART1, USART_IT_RXNE, ENABLE);

    USART_Cmd(USART1, ENABLE);
}

void UART_STOP(void){
    USART_Cmd(USART1, DISABLE);

    
    USART_ITConfig(USART1, USART_IT_RXNE, DISABLE);
    NVIC_DisableIRQ(USART1_IRQn);


    USART_DeInit(USART1);  


    
    GPIO_InitTypeDef GPIO_InitStructure;
    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_10;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_IN_FLOATING; 
    GPIO_Init(GPIOA, &GPIO_InitStructure);

    
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_USART1, DISABLE);
}
void UART_START(void){
	UART_Init();
}	

volatile int8_t rx_buffer[13]; 
volatile int rx_index = 0; 


extern uint8_t f[3][3];
extern uint8_t distance;

void ProcessData(volatile int8_t data[]) {
		//OLED_ShowString(1,1,"GET IT");
		//Delay_ms(1000);
    int8_t id = 2;
		for(int i = 0;i<=2;++i){
			for(int j = 0;j<=2;++j){
				f[i][j] = data[id++];
			}
		}
		distance = data[id++];
		OLED_NEW();
		Delay_ms(100);
}

extern int8_t data_size;
int8_t Flag = 0;

void USART1_IRQHandler(void) {
    if (USART_GetITStatus(USART1, USART_IT_RXNE) != RESET) {
        
        uint8_t data = USART_ReceiveData(USART1);
				
        if (rx_index == 0 && data == 0x43) { 
            rx_buffer[rx_index++] = data;
        } else if (rx_index == 1 && data == 0x12) { 
            rx_buffer[rx_index++] = data;
        }else if (rx_index >= 2 && rx_index <= data_size+1) {
					if(Flag)rx_buffer[rx_index++] = data;
					Flag = !Flag;
        } else if (rx_index == data_size+2 && data == 0x52) { 
            rx_buffer[rx_index] = data;
            ProcessData(rx_buffer); 
            rx_index = 0; 
        } else {
						//OLED_ShowString(2,1,"FALSE");
            rx_index = 0; 
        }
    }
}
```
