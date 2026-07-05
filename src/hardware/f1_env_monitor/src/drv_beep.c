/*
 * 蜂鸣器驱动：
 *   1) beep_play_tone(freq_hz, duration_ms) — 精确频率+时长控制
 *   2) beep_request_play()                 — 播放当前选中曲谱（非阻塞）
 *   3) beep_set_song(id)                   — 切换曲目
 *
 * 硬件: EPWMDEV_PWM5_M0, 占空比固定 50%
 *
 * 曲目列表:
 *   0 = 小蜜蜂（内置简谱）
 *   1 = 超级玛丽（gbc.h，3453 事件）
 *   2 = 哭砂（cry.h，1805 事件）
 */
#include "drv_beep.h"

#include <stddef.h>
#include <stdio.h>
#include <unistd.h>

#include "iot_errno.h"
#include "iot_pwm.h"
#include "los_task.h"

/* b7_beep MIDI 曲谱头文件 */
#include "gbc.h"
#include "cry.h"

#define BEEP_PORT         EPWMDEV_PWM5_M0
#define BEEP_DUTY_PCT     50       /* 固定占空比 50% */
#define BEEP_FREQ_MIN     200      /* 最低频率 Hz */
#define BEEP_FREQ_MAX     20000    /* 最高频率 Hz */
#define BEEP_DURATION_MAX 60000    /* 最长时长 ms */

static int g_beep_inited = 0;

/* ──── 曲谱播放（兼容旧接口 + 多歌曲支持）──── */

static volatile int g_play_request = 0;
static volatile int g_current_song = 0;    /* 当前选中曲目 */
static volatile int g_play_paused = 0;     /* 播放暂停标志 */

/* ── 歌曲1: 内置小蜜蜂（旧简谱格式）── */
static const uint16_t g_tune_freqs[] = {
    0,
    4186, 4700, 5276, 5588, 6272, 7040, 7902, 3136
};

static const uint8_t g_score_notes[] = {
    1, 2, 3, 1,        1, 2, 3, 1,        3, 4, 5,  3, 4, 5,
    5, 6, 5, 4, 3, 1,  5, 6, 5, 4, 3, 1,  1, 8, 1,  1, 8, 1,
};

static const uint8_t g_score_durations[] = {
    4, 4, 4, 4,        4, 4, 4, 4,        4, 4, 8,  4, 4, 8,
    3, 1, 3, 1, 4, 4,  3, 1, 3, 1, 4, 4,  4, 4, 8,  4, 4, 8,
};

static void beep_play_melody_builtin(void)
{
    size_t count = sizeof(g_score_notes) / sizeof(g_score_notes[0]);
    for (size_t i = 0; i < count && !g_play_paused; i++) {
        uint32_t tune = g_score_notes[i];
        uint16_t freq_divisor = g_tune_freqs[tune];
        uint32_t tune_interval = g_score_durations[i] * (125 * 1000);

        IoTPwmStart(BEEP_PORT, BEEP_DUTY_PCT, freq_divisor);
        usleep(tune_interval);
        IoTPwmStop(BEEP_PORT);
        usleep(100000);
    }
}

/* ── 歌曲2/3: MIDI 转 BeepEvt 格式（gbc.h / cry.h）── */
static void beep_play_evt_song(const BeepEvt *events, uint32_t count, const char *name)
{
    printf("[beep] play %s, events=%u\n", name, (unsigned)count);
    for (uint32_t i = 0; i < count && !g_play_paused; i++) {
        const BeepEvt *e = &events[i];
        if (e->freq_hz == 0) {
            IoTPwmStop(BEEP_PORT);
        } else {
            IoTPwmStart(BEEP_PORT, e->duty, e->freq_hz);
        }
        usleep(e->dur_us);
    }
    IoTPwmStop(BEEP_PORT);
}

/* ── 曲目注册表 ── */
typedef struct {
    const char   *name;
    void        (*play_fn)(void);
} melody_entry_t;

static void _play_gbc(void)  { beep_play_evt_song(g_beep_song_gbc, g_beep_song_len_gbc, "GBC"); }
static void _play_cry(void)  { beep_play_evt_song(g_beep_song_cry, g_beep_song_len_cry, "CRY"); }

static const melody_entry_t g_melodies[BEEP_SONG_COUNT] = {
    { "BUILTIN",  beep_play_melody_builtin },
    { "GBC",      _play_gbc },
    { "CRY",      _play_cry },
};

static void beep_play_current_melody(void)
{
    if (g_current_song < 0 || g_current_song >= BEEP_SONG_COUNT) {
        g_current_song = 0;
    }
    g_play_paused = 0;
    printf("[beep] current song: %d (%s)\n", g_current_song,
           g_melodies[g_current_song].name);
    g_melodies[g_current_song].play_fn();
}

static void beep_task(void *arg)
{
    (void)arg;

    while (1) {
        if (g_play_request) {
            g_play_request = 0;
            beep_play_current_melody();
        }
        LOS_Msleep(50);
    }
}

/* ──── 精确频率+时长控制 ──── */

int beep_play_tone(int freq_hz, int duration_ms)
{
    if (!g_beep_inited) {
        printf("[beep] error: PWM not initialized\n");
        return -2;
    }

    if (freq_hz <= 0 || duration_ms <= 0) {
        printf("[beep] error: invalid params freq=%d dur=%d\n", freq_hz, duration_ms);
        return -1;
    }

    /* 频率钳位 */
    if (freq_hz < BEEP_FREQ_MIN) {
        freq_hz = BEEP_FREQ_MIN;
    }
    if (freq_hz > BEEP_FREQ_MAX) {
        freq_hz = BEEP_FREQ_MAX;
    }

    /* 时长钳位 */
    if (duration_ms > BEEP_DURATION_MAX) {
        duration_ms = BEEP_DURATION_MAX;
    }

    printf("[beep] tone freq=%dHz duration=%dms\n", freq_hz, duration_ms);

    IoTPwmStart(BEEP_PORT, BEEP_DUTY_PCT, (unsigned int)freq_hz);
    LOS_Msleep((unsigned int)duration_ms);
    IoTPwmStop(BEEP_PORT);

    return 0;
}

/* ──── 曲目管理 ──── */

void beep_set_song(int song_id)
{
    if (song_id < 0 || song_id >= BEEP_SONG_COUNT) {
        printf("[beep] invalid song id=%d, ignored\n", song_id);
        return;
    }
    g_current_song = song_id;
    printf("[beep] switch to song: %d (%s)\n", song_id,
           g_melodies[song_id].name);
}

int beep_get_song(void)
{
    return g_current_song;
}

int beep_get_song_count(void)
{
    return BEEP_SONG_COUNT;
}

void beep_pause_play(void)
{
    g_play_paused = 1;
    IoTPwmStop(BEEP_PORT);
    printf("[beep] play paused\n");
}

void beep_resume_play(void)
{
    g_play_paused = 0;
    printf("[beep] play resumed\n");
}

void beep_stop_play(void)
{
    g_play_request = 0;         /* 阻止 beep_task 自动重播 */
    g_play_paused = 1;          /* 中断正在播放的旋律循环 */
    IoTPwmStop(BEEP_PORT);
    printf("[beep] play stopped\n");
}

/* ──── 公共接口 ──── */

void beep_request_play(void)
{
    g_play_request = 1;
}

void beep_dev_init(void)
{
    unsigned int thread_id;
    TSK_INIT_PARAM_S task = {0};
    unsigned int ret;

    ret = IoTPwmInit(BEEP_PORT);
    if (ret != IOT_SUCCESS) {
        printf("[beep] IoTPwmInit failed: %u\n", ret);
        return;
    }
    g_beep_inited = 1;
    g_current_song = BEEP_SONG_BUILTIN;

    task.pfnTaskEntry = (TSK_ENTRY_FUNC)beep_task;
    task.uwStackSize = 8192;
    task.pcName = "beep_play";
    task.usTaskPrio = 21;
    ret = LOS_TaskCreate(&thread_id, &task);
    if (ret != LOS_OK) {
        printf("[beep] task create failed: 0x%x\n", ret);
    } else {
        printf("[beep] init OK, port=EPWM5_M0, freq=%d~%dHz, songs=%d\n",
               BEEP_FREQ_MIN, BEEP_FREQ_MAX, BEEP_SONG_COUNT);
    }
}
