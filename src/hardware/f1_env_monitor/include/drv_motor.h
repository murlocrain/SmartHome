/*
 * 直流电机驱动接口
 *
 * PWM 调速范围 0-100%，0 = 停止，1-100 = 对应占空比。
 * 硬件限制：单路 PWM 输出 (EPWMDEV_PWM6_M0)，不支持正反转。
 * 正反转需要增加 H 桥或方向 GPIO 配合另一路 PWM。
 */
#ifndef __DRV_MOTOR_H__
#define __DRV_MOTOR_H__

#include <stdbool.h>

void motor_dev_init(void);

/* 开关控制（兼容旧接口），speed 保持最后一次 motor_set_speed 值 */
void motor_set_state(bool state);
int  get_motor_state(void);

/* 无级调速：percent 取值 0-100，0=停止，>0 自动启动 */
void motor_set_speed(int percent);
int  get_motor_speed(void);

#endif
