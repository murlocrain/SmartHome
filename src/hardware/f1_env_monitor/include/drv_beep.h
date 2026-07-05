/*
 * 蜂鸣器驱动接口
 *
 * 支持两种工作模式：
 *   1. beep_request_play()    — 播放当前选中曲谱（非阻塞）
 *   2. beep_play_tone(f,d)   — 指定频率和时长（阻塞，调用线程等待）
 *
 * 硬件端口: EPWMDEV_PWM5_M0, PWM 占空比固定 50%
 * 频率范围: 200 Hz ~ 20000 Hz
 * 时长范围: 0 ~ 60000 ms
 *
 * 曲目管理:
 *   beep_set_song(id)  — 切换曲目（0=小蜜蜂, 1=超级玛丽, 2=哭砂）
 *   beep_get_song()    — 获取当前曲目编号
 *   beep_get_song_count() — 获取曲目总数
 */
#ifndef __DRV_BEEP_H__
#define __DRV_BEEP_H__

#include <stdint.h>

/* 曲目编号常量 */
#define BEEP_SONG_BUILTIN   0   /* 小蜜蜂（内置简谱） */
#define BEEP_SONG_GBC       1   /* 超级玛丽 */
#define BEEP_SONG_CRY       2   /* 哭砂 */
#define BEEP_SONG_COUNT     3

void beep_dev_init(void);

/* 触发播放当前选中的曲谱（非阻塞），播放完毕后 beep_task 线程会自动循环 */
void beep_request_play(void);

/*
 * 播放单音调（阻塞式）
 * freq_hz     - 频率 (Hz)，范围 200 ~ 20000，超出自动钳位
 * duration_ms - 持续时长 (ms)，范围 0 ~ 60000，超出自动钳位
 * 返回: 0=成功, -1=参数错误（freq_hz <= 0 或 duration_ms <= 0）
 *        -2=PWM 端口未初始化
 */
int beep_play_tone(int freq_hz, int duration_ms);

/* 曲目管理 */
void beep_set_song(int song_id);
int  beep_get_song(void);
int  beep_get_song_count(void);

/* 暂停/恢复正在播放的曲谱（用于被其他声音打断） */
void beep_pause_play(void);
void beep_resume_play(void);

/* 停止播放并阻止自动重播 */
void beep_stop_play(void);

#endif
