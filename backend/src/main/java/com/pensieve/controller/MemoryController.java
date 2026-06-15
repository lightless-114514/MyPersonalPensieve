package com.pensieve.controller;

import com.pensieve.dto.MemoryRequest;
import com.pensieve.dto.MemoryResponse;
import com.pensieve.dto.PagedResponse;
import com.pensieve.service.MemoryService;
import com.pensieve.service.RedisService;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/memories")
@RequiredArgsConstructor
public class MemoryController {

    private final MemoryService memoryService;
    private final RedisService redisService;

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public MemoryResponse create(@Valid @RequestBody MemoryRequest request,
                                  HttpServletRequest httpRequest) {
        checkRateLimit(httpRequest);
        return memoryService.create(request);
    }

    @GetMapping
    public PagedResponse<MemoryResponse> getAll(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size,
            HttpServletRequest httpRequest) {
        checkRateLimit(httpRequest);
        return memoryService.getAll(page, size);
    }

    @GetMapping("/recent")
    public List<MemoryResponse> getRecent(
            @RequestParam(defaultValue = "10") int limit,
            HttpServletRequest httpRequest) {
        checkRateLimit(httpRequest);
        return memoryService.getRecent(limit);
    }

    @GetMapping("/{id}")
    public MemoryResponse getById(@PathVariable String id,
                                   HttpServletRequest httpRequest) {
        checkRateLimit(httpRequest);
        return memoryService.getById(id);
    }

    @DeleteMapping("/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void delete(@PathVariable String id,
                        HttpServletRequest httpRequest) {
        checkRateLimit(httpRequest);
        memoryService.delete(id);
    }

    private void checkRateLimit(HttpServletRequest request) {
        String ip = request.getRemoteAddr();
        if (redisService.isRateLimited(ip)) {
            throw new RuntimeException("请求过于频繁，请稍后再试");
        }
    }
}