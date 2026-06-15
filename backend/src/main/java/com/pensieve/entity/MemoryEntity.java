package com.pensieve.entity;

import jakarta.persistence.*;
import lombok.*;

@Entity
@Table(name = "memory_entity",
       uniqueConstraints = @UniqueConstraint(columnNames = {"memory_id", "entity_id"}))
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class MemoryEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private String id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "memory_id", nullable = false)
    private Memory memory;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "entity_id", nullable = false)
    private KnowledgeEntity entity;
}