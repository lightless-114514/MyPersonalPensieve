package com.pensieve.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class MemoryRequest {
    private String title;
    private String content;
    private String type;
    private String sourceUrl;
    private List<String> tags;
}
