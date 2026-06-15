package com.pensieve.service;

import lombok.RequiredArgsConstructor;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;

import java.time.Duration;
import java.util.List;
import java.util.concurrent.TimeUnit;

@Service
@RequiredArgsConstructor
public class RedisService {

    private final StringRedisTemplate redis;

    // ---- 缓存热点记忆列表 ----

    private static final String KEY_MEMORIES_RECENT = "memories:recent";

    public void cacheRecentMemories(String json) {
        redis.opsForValue().set(KEY_MEMORIES_RECENT, json, Duration.ofMinutes(10));
    }

    public String getRecentMemories() {
        return redis.opsForValue().get(KEY_MEMORIES_RECENT);
    }

    public void evictRecentMemories() {
        redis.delete(KEY_MEMORIES_RECENT);
    }

    // ---- SSE 任务步骤 ----

    private static final String KEY_TASK_PREFIX = "task:";

    public void addTaskStep(String taskId, String step) {
        String key = KEY_TASK_PREFIX + taskId;
        redis.opsForList().rightPush(key, step);
        redis.expire(key, 5, TimeUnit.MINUTES);
    }

    public List<String> getTaskSteps(String taskId) {
        String key = KEY_TASK_PREFIX + taskId;
        return redis.opsForList().range(key, 0, -1);
    }

    public void clearTask(String taskId) {
        redis.delete(KEY_TASK_PREFIX + taskId);
    }

    // ---- 限流 ----

    private static final String KEY_RATE_PREFIX = "rate:ask:";
    private static final int RATE_LIMIT_MAX = 60;
    private static final int RATE_LIMIT_WINDOW = 60;

    public boolean isRateLimited(String ip) {
        String key = KEY_RATE_PREFIX + ip;
        Long count = redis.opsForValue().increment(key);
        if (count != null && count == 1) {
            redis.expire(key, RATE_LIMIT_WINDOW, TimeUnit.SECONDS);
        }
        return count != null && count > RATE_LIMIT_MAX;
    }

    public long getRateCount(String ip) {
        String count = redis.opsForValue().get(KEY_RATE_PREFIX + ip);
        return count != null ? Long.parseLong(count) : 0;
    }
}