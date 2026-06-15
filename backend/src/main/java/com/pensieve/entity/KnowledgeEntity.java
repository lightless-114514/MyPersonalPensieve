package com.pensieve.entity;

import jakarta.persistence.*;
import lombok.*;
import java.util.HashSet;
import java.util.Set;

@jakarta.persistence.Entity
@Table(name = "entities")
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class KnowledgeEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private String id;

    @Column(nullable = false, length = 200)
    private String name;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 15)
    private EntityType type;

    @OneToMany(mappedBy = "entity", cascade = CascadeType.ALL, orphanRemoval = true)
    @Builder.Default
    private Set<MemoryEntity> memoryEntities = new HashSet<>();

    public enum EntityType {
        PERSON, PLACE, ORG, EVENT, TOPIC, TECHNOLOGY, OTHER
    }
}