package com.pensieve.service;

import com.pensieve.dto.MemoryRequest;
import com.pensieve.dto.MemoryResponse;
import com.pensieve.dto.PagedResponse;
import com.pensieve.entity.Memory;
import com.pensieve.repository.MemoryRepository;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.ArrayList;
import java.util.List;

@Service
@RequiredArgsConstructor
public class MemoryService {

    private final MemoryRepository memoryRepository;
    private final RedisService redisService;
    private final ObjectMapper objectMapper = new ObjectMapper()
            .registerModule(new JavaTimeModule());

    @Transactional
    public MemoryResponse create(MemoryRequest request) {
        Memory memory = Memory.builder()
                .title(request.getTitle())
                .content(request.getContent())
                .type(Memory.MemoryType.valueOf(
                        request.getType() != null ? request.getType().toUpperCase() : "TEXT"))
                .sourceUrl(request.getSourceUrl())
                .tags(request.getTags() != null ? request.getTags() : new ArrayList<>())
                .build();

        Memory saved = memoryRepository.save(memory);
        redisService.evictRecentMemories();
        return MemoryResponse.from(saved);
    }

    @Transactional(readOnly = true)
    public PagedResponse<MemoryResponse> getAll(int page, int size) {
        Page<Memory> memoryPage = memoryRepository
                .findAllByOrderByCreatedAtDesc(PageRequest.of(page, size));

        return PagedResponse.<MemoryResponse>builder()
                .content(memoryPage.getContent().stream()
                        .map(MemoryResponse::from).toList())
                .page(memoryPage.getNumber())
                .size(memoryPage.getSize())
                .totalElements(memoryPage.getTotalElements())
                .totalPages(memoryPage.getTotalPages())
                .last(memoryPage.isLast())
                .first(memoryPage.isFirst())
                .build();
    }

    @Transactional(readOnly = true)
    public List<MemoryResponse> getRecent(int limit) {
        String cached = redisService.getRecentMemories();
        if (cached != null) {
            try {
                return objectMapper.readValue(cached,
                        objectMapper.getTypeFactory().constructCollectionType(List.class, MemoryResponse.class));
            } catch (Exception ignored) {}
        }

        List<Memory> memories = memoryRepository.findTop10ByOrderByCreatedAtDesc();
        List<MemoryResponse> list = memories.stream()
                .limit(limit)
                .map(MemoryResponse::from)
                .toList();

        try {
            redisService.cacheRecentMemories(objectMapper.writeValueAsString(list));
        } catch (Exception ignored) {}

        return list;
    }

    @Transactional(readOnly = true)
    public MemoryResponse getById(String id) {
        Memory memory = memoryRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Memory not found: " + id));
        return MemoryResponse.from(memory);
    }

    @Transactional
    public void delete(String id) {
        memoryRepository.deleteById(id);
        redisService.evictRecentMemories();
    }
}