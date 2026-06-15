package com.pensieve.dto;

import com.pensieve.entity.Memory;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.List;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class MemoryResponse {
    private String id;
    private String title;
    private String content;
    private String type;
    private String sourceUrl;
    private String filePath;
    private String sentiment;
    private Double sentimentScore;
    private String processingStatus;
    private List<String> tags;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;

    public static MemoryResponse from(Memory m) {
        return MemoryResponse.builder()
                .id(m.getId())
                .title(m.getTitle())
                .content(m.getContent())
                .type(m.getType().name())
                .sourceUrl(m.getSourceUrl())
                .filePath(m.getFilePath())
                .sentiment(m.getSentiment() != null ? m.getSentiment().name() : null)
                .sentimentScore(m.getSentimentScore())
                .processingStatus(m.getProcessingStatus() != null ? m.getProcessingStatus().name() : null)
                .tags(m.getTags())
                .createdAt(m.getCreatedAt())
                .updatedAt(m.getUpdatedAt())
                .build();
    }
}