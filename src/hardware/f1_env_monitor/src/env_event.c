#include "env_event.h"

#include <stdio.h>

#include "los_task.h"

#define ENV_EVENT_QUEUE_LEN  8

static unsigned int g_event_queue_id;

void env_event_init(void)
{
    unsigned int ret = LOS_QueueCreate("envEventQ", ENV_EVENT_QUEUE_LEN,
                                       &g_event_queue_id, 0,
                                       sizeof(env_event_t));
    if (ret != LOS_OK) {
        printf("[env_event] queue create failed: 0x%x\n", ret);
    }
}

void env_event_send(const env_event_t *event)
{
    if (event == NULL) {
        return;
    }
    (void)LOS_QueueWriteCopy(g_event_queue_id, event, sizeof(env_event_t),
                             LOS_WAIT_FOREVER);
}

int env_event_wait(env_event_t *event, int timeout_ms)
{
    UINT32 ticks;

    if (event == NULL) {
        return LOS_NOK;
    }
    if (timeout_ms <= 0) {
        ticks = LOS_NO_WAIT;
    } else {
        ticks = LOS_MS2Tick(timeout_ms);
    }
    return LOS_QueueReadCopy(g_event_queue_id, event, sizeof(env_event_t), ticks);
}
