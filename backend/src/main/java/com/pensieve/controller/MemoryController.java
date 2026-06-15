package com.pensieve.controller;

import com.pensieve.dto.MemoryRequest;
import com.pensieve.dto.MemoryResponse;
import com.pensieve.dto.PagedResponse;
import com.pensieve.service.MemoryService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/memories")
@RequiredArgsConstructor
public class MemoryController {

    private final MemoryService memoryService;

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public MemoryResponse create(@Valid @RequestBody MemoryRequest request) {
        return memoryService.create(request);
    }

    @GetMapping
    public PagedResponse<MemoryResponse> getAll(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {
        return memoryService.getAll(page, size);
    }

    @GetMapping("/{id}")
    public MemoryResponse getById(@PathVariable String id) {
        return memoryService.getById(id);
    }

    @DeleteMapping("/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void delete(@PathVariable String id) {
        memoryService.delete(id);
    }
}
