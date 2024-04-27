#代码思路：分别先识别圆和三角形 再识别圆和三角形的颜色模块；测量三角形采用间接法测量   黑色色块问题 三个if不等于1
#如果5次或者十次检测到同一个值就发送  因为我这边要一直发送信息给32，可以让32那边执行
#通信协议:0x5a/0x5a/   X    /     Y     / mode                            /color/distance/0xb3
#       头帧 / 头帧/色块x 默认0/色块Y 默认0/默认0，/默认0 R1G2B3/默认0 物体长度 /尾帧
#三角形和正方形由于旋转的影响可能不准

import sensor, image, time,math
import struct
from pyb import UART

uart = UART(1, 115200)
uart.init(115200, bits=8, parity=None, stop=1)  #8位数据位，无校验位，1位停止位
def signed_int_to_byte(number):
    return struct.pack(">h", number)

def sending_data(x, y, z, b, f, g, a, j, k,l):
    global uart                            #将x、y、z转换为字节数组
    x_bytes = signed_int_to_byte(x)
    y_bytes = signed_int_to_byte(y)
    z_bytes = signed_int_to_byte(z)        #组装数据包，使用转换后的字节数组
    b_bytes = signed_int_to_byte(b)
    f_bytes = signed_int_to_byte(f)
    g_bytes = signed_int_to_byte(g)        #组装数据包，使用转换后的字节数组
    a_bytes = signed_int_to_byte(a)
    j_bytes = signed_int_to_byte(j)
    k_bytes = signed_int_to_byte(k)        #组装数据包，使用转换后的字节数组
    l_bytes = signed_int_to_byte(l)
    FH = bytearray([0x43, 0x12])
    FH.extend(x_bytes)
    FH.extend(y_bytes)
    FH.extend(z_bytes)
    FH.extend(b_bytes)
    FH.extend(f_bytes)
    FH.extend(g_bytes)
    FH.extend(a_bytes)
    FH.extend(j_bytes)
    FH.extend(k_bytes)
    FH.extend(l_bytes)
    FH.extend(bytearray([0x52]))
    uart.write(FH)

sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QQVGA)    #160*120
sensor.skip_frames(time = 2000)
sensor.set_auto_gain(False)
sensor.set_auto_whitebal(False)
from machine import I2C
from vl53l1x import VL53L1X

clock = time.clock()

threshold_index = 0 # 0 for red, 1 for green, 2 for blue
thresholds = [(16, 71, 15, 102, -23, 97), # red_thresholds
              (11, 29, -33, -17, 0, 48), # green_thresholds
              (0, 42, -23, 16, -46, -5)] # blue_thresholds
def check(L,A,B):
    dis_Red = math.sqrt((L-54.29)**2+(A-80.81)**2+(B-69.89)**2)
    dis_Green = math.sqrt((L-87.82)**2+(A-(-79.29))**2+(B-80.99)**2)
    dis_Blue = math.sqrt((L-29.57)**2+(A-68.3)**2+(B-(-112.03))**2)
    if(dis_Blue<dis_Green and dis_Blue<dis_Red):
        return 3
    if(dis_Green<dis_Blue and dis_Green<dis_Red):
        return 2
    if(dis_Red<dis_Green and dis_Red<dis_Blue):
        return 1


i2c = I2C(2)
distance = VL53L1X(i2c)
K = (78/45)/274        #毫米
actual_1 = 0
actual_2 = 0
actual_3 = 0
actual_4 = 0
actual_5 = 0
actual_6 = 0
actual_7 = 0
actual_8 = 0
actual_9 = 0
def clear_():
    actual_1 = 0
    actual_2 = 0
    actual_3 = 0
    actual_4 = 0
    actual_5 = 0
    actual_6 = 0
    actual_7 = 0
    actual_8 = 0
    actual_9 = 0
while(True):
    clock.tick()
    img = sensor.snapshot().lens_corr(strength = 1.8, zoom = 1.0)
    img = sensor.snapshot().rotation_corr(z_rotation=180)
#参数初始化
    X=0     #物体中心x坐标
    Y=0     #物体中心Y坐标
    mode=0  #形状 默认0 圆1角2方3
    color=0 #颜色 默认0 R1G2B3
    #distance=0 #物体x方向距离（矩形怎么办？对角线？   像素单位   利用四个角计算


#检测圆
    for c in img.find_circles(threshold =5000, x_margin = 10, y_margin = 10, r_margin = 10,
            r_min = 2, r_max = 100, r_step = 2):
        area = (c.x()-c.r(), c.y()-c.r(), 2*c.r(), 2*c.r())#area为识别到的圆的区域，即圆的外接矩形框
        statistics = img.get_statistics(roi=area)#像素颜色统计  这里为什么不直接用○的ROI？
        #print(statistics)

        #(0,100,0,120,0,120)是红色的阈值，所以当区域内的众数（也就是最多的颜色），范围在这个阈值内，就说明是红色的圆。
        #l_mode()，a_mode()，b_mode()是L通道，A通道，B通道的众数。
        if check(statistics.l_mode(),statistics.a_mode(),statistics.b_mode())==1:# red:# red
            img.draw_circle(c.x(), c.y(), c.r(), color = (255, 0, 0))#识别到的红色圆形用红色的圆框出来
            X=c.x()
            Y=c.y()
            mode=1
            color=1
            #distance= 2*c.r()
            actual_1 = (K * (2*c.r()))*distance.read()
            print("实际直径: {}".format(actual_1))
            print("红色圆形")
        if check(statistics.l_mode(),statistics.a_mode(),statistics.b_mode())==2:# red:#green
            img.draw_circle(c.x(), c.y(), c.r(), color = (0, 255, 0))#识别到的绿色圆形用绿色的圆框出来
            X=c.x()
            Y=c.y()
            mode=1
            color=2
            #distance= 2*c.r()
            actual_2 = (K * (2*c.r()))*distance.read()
            print("实际直径: {}".format(actual_2))
            print("绿色圆形")
        if check(statistics.l_mode(),statistics.a_mode(),statistics.b_mode())==3:# red:#blue
            img.draw_circle(c.x(), c.y(), c.r(), color = (0, 0, 255))#识别到的蓝色圆形用蓝色的圆框出来
            X=c.x()
            Y=c.y()
            mode=1
            color=3
            #distance= 2*c.r()
            actual_3 = (K * (2*c.r()))*distance.read
            print("实际直径: {}".format(actual_3))
            print("蓝色圆形")

#检测矩形   问题：现在会出现颜色标记出错的问题
    for d in img.find_rects(threshold = 20000):
        area=(d[0],d[1],d[2],d[3])   #(x, y, w, h)
        statistics = img.get_statistics(roi=area)#像素颜色统计
        #print(statistics1)
        x=0
        x=d[2]/d[3]
        print(x)
        q=[0,0]
        Q=0
        for p in d.corners():Q=((p[0]-q[0])**2+(p[1]-q[1])**2)**0.5
        if check(statistics.l_mode(),statistics.a_mode(),statistics.b_mode())==1:# red
            img.draw_rectangle(d.rect(), color = (255, 0, 0))
            X=int(d[0]+d[2]/2)
            Y=int(d[1]+d[3]/2)
            mode=3
            color=1
            #distance=int(Q)
            actual_4 = (K * d[2])*distance.read()
            print("实际边长: {}".format(actual_4))
            print("红色正方形")

        if check(statistics.l_mode(),statistics.a_mode(),statistics.b_mode())==2:# red
            img.draw_rectangle(d.rect(), color = (0, 255, 0))
            X=int(d[0]+d[2]/2)
            Y=int(d[1]+d[3]/2)
            mode=3
            color=2
            actual_5 = (K * d[2])*distance.read()
            print("实际边长: {}".format(actual_5))
            print("绿色正方形")
        if check(statistics.l_mode(),statistics.a_mode(),statistics.b_mode())==3:# red
            img.draw_rectangle(d.rect(), color = (0,0 , 255))
            X=int(d[0]+d[2]/2)
            Y=int(d[1]+d[3]/2)
            mode=3
            color=3
            actual_6 = (K * d[2])*distance.read()
            print("实际边长: {}".format(actual_6))
            print("蓝色正方形")
        print(distance)

#检测三角形    色块查找绿色有影响   黑色产生
    for blob in img.find_blobs(thresholds,pixels_threshold=200,roi = (20,20,100,80),area_threshold=50):
        if blob.density()>0.40 and blob.density()<0.55 :
           statistics = img.get_statistics(roi=blob.rect())#像素颜色统计
           color = img.get_statistics(roi=blob.rect())
           if check(statistics.l_mode(),statistics.a_mode(),statistics.b_mode())==1:
              img.draw_cross(blob.cx(), blob.cy(), color = (255, 0, 0))
              actual_7 = (K * blob.w())*distance.read()
              print("实际边长: {}".format(actual_7))
              print("红色三角形")
           if check(statistics.l_mode(),statistics.a_mode(),statistics.b_mode())==2:
              img.draw_cross(blob.cx(), blob.cy(), color = (0, 255, 0))
              actual_8 = (K * blob.w())*distance.read()
              print("实际边长: {}".format(actual_8))
              print("绿色三角形")
           if check(statistics.l_mode(),statistics.a_mode(),statistics.b_mode())==3:
              img.draw_cross(blob.cx(), blob.cy(), color = (0, 0, 255))
              actual_9 = (K * blob.w())*distance.read()
              print("实际边长: {}".format(actual_9))
              print("蓝色三角形")
    print("range: mm ", distance.read())
    time.sleep_ms(50)


         #data = bytearray([0xb3,0xb3,1,1,1,1,1,1,1,1,1,1,100,0x5b])
    #sending_data(1,1,1,1,1,1,1,1,1,100)
    sending_data(int(actual_1),int(actual_2),int(actual_3),int(actual_4),int(actual_5),int(actual_6),int(actual_7),int(actual_8),int(actual_9),int(distance.read()))
    print("yi fa song")

    clear_()

   # print("FPS %f" % clock.fps())
